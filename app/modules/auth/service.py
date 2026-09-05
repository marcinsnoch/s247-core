import logging
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
    verify_password_reset_token,
)
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemas import RegisterRequest, TokenResponse
from app.modules.users.models import User, UserRole
from app.modules.users.repository import UserRepository
from app.modules.workspaces.models import Workspace
from app.shared.exceptions import ConflictException, ForbiddenException, NotFoundException, UnauthorizedException

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def authenticate(self, identifier: str, password: str) -> User:
        """Authenticate user by email/username and password."""
        user = await self.user_repo.get_by_email(identifier.lower().strip())
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")
        if not user.is_active:
            raise ForbiddenException("User account is disabled")
        return user

    def _build_access_token_claims(self, user: User) -> dict:
        return {
            "sub": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "workspace_id": user.workspace_id,
        }

    async def issue_token_pair(self, user: User) -> TokenResponse:
        """Issue access token and refresh token, persisting refresh token for rotation."""
        claims = self._build_access_token_claims(user)
        access_token = create_access_token(claims)

        raw_refresh, token_hash, expires_at = generate_refresh_token()
        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False,
        )
        self.db.add(refresh_record)
        await self.db.commit()

        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=raw_refresh,
            scope=f"role:{role_str}",
        )

    async def refresh_tokens(self, raw_refresh_token: str) -> TokenResponse:
        """Refresh token rotation (RTR): Validate token, revoke it, and issue a fresh pair."""
        token_hash = hash_token(raw_refresh_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.execute(stmt)
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise UnauthorizedException("Invalid refresh token")

        now = datetime.now(timezone.utc)
        record_expires = token_record.expires_at
        if record_expires.tzinfo is None:
            record_expires = record_expires.replace(tzinfo=timezone.utc)

        if record_expires < now:
            raise UnauthorizedException("Refresh token has expired")

        if token_record.revoked:
            # Token reuse detected! Invalidate all tokens for this user for security
            stmt_revoke_all = (
                update(RefreshToken)
                .where(RefreshToken.user_id == token_record.user_id)
                .values(revoked=True)
            )
            await self.db.execute(stmt_revoke_all)
            await self.db.commit()
            raise UnauthorizedException("Refresh token has been revoked or already used")

        # Invalidate the current refresh token (RTR)
        token_record.revoked = True

        # Retrieve user
        user = await self.user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            await self.db.commit()
            raise UnauthorizedException("User account is inactive or not found")

        # Issue replacement refresh token
        new_raw_refresh, new_token_hash, new_expires_at = generate_refresh_token()
        new_record = RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            revoked=False,
        )
        self.db.add(new_record)
        await self.db.commit()

        claims = self._build_access_token_claims(user)
        access_token = create_access_token(claims)
        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)

        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=new_raw_refresh,
            scope=f"role:{role_str}",
        )

    async def revoke_token(self, raw_refresh_token: str | None) -> None:
        """Revoke a refresh token (logout)."""
        if not raw_refresh_token:
            return
        token_hash = hash_token(raw_refresh_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if record:
            record.revoked = True
            await self.db.commit()

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user account."""
        normalized_email = data.email.lower().strip()
        existing = await self.user_repo.get_by_email(normalized_email)
        if existing:
            raise ConflictException(f"User with email {normalized_email} already exists")

        workspace_id = data.workspace_id
        if not workspace_id:
            # Associate with default WS0001 or first workspace if available
            ws_res = await self.db.execute(select(Workspace).order_by(Workspace.id.asc()).limit(1))
            first_ws = ws_res.scalar_one_or_none()
            if first_ws:
                workspace_id = first_ws.id

        new_user = User(
            email=normalized_email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name.strip(),
            role=UserRole.CLIENT,
            is_active=True,
            workspace_id=workspace_id,
        )
        created = await self.user_repo.create(new_user)
        await self.db.commit()
        return created

    async def request_password_reset(self, email: str) -> str:
        """Generate a single-use password reset token for user."""
        normalized_email = email.lower().strip()
        user = await self.user_repo.get_by_email(normalized_email)
        if not user or not user.is_active:
            raise NotFoundException("User with this email not found")

        reset_token = create_password_reset_token(user.id, user.email)
        logger.info("Password reset requested for user %s. Token generated.", user.email)
        return reset_token

    async def reset_password(self, token: str, new_password: str) -> None:
        """Validate reset token, update password and revoke all active refresh tokens."""
        payload = verify_password_reset_token(token)
        if not payload:
            raise UnauthorizedException("Invalid or expired password reset token")

        try:
            user_id = int(payload["sub"])
        except (ValueError, TypeError):
            raise UnauthorizedException("Malformed reset token")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        user.hashed_password = hash_password(new_password)

        # Invalidate all existing refresh tokens for security
        stmt_revoke_all = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id)
            .values(revoked=True)
        )
        await self.db.execute(stmt_revoke_all)
        await self.db.commit()
        logger.info("Password successfully reset for user %s.", user.email)
