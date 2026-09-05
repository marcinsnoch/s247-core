from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database.session import get_db
from app.modules.users.models import User, UserRole
from app.shared.exceptions import ForbiddenException, UnauthorizedException

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate current authenticated user from Bearer JWT token."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Missing or invalid Authorization header")

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise UnauthorizedException("Invalid or expired token")

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise UnauthorizedException("Invalid user subject identifier in token")

    stmt = select(User).where(User.id == user_id, User.is_active == True)  # noqa: E712
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User does not exist or account is inactive")

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require administrator privileges."""
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException("Administrator privileges required")
    return current_user


async def require_staff(current_user: User = Depends(get_current_user)) -> User:
    """Require staff privileges (technician or admin)."""
    if current_user.role not in (UserRole.ADMIN, UserRole.TECHNICIAN):
        raise ForbiddenException("Staff privileges (technician or administrator) required")
    return current_user
