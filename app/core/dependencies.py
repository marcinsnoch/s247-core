from collections.abc import Callable
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Permission, get_role_permissions, has_all_permissions
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


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Dependency factory enforcing that the authenticated user possesses one of the required roles."""
    expected_roles = set(roles)

    async def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in expected_roles:
            role_names = ", ".join(r.value for r in expected_roles)
            current_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
            raise ForbiddenException(
                f"Operation forbidden. Required role: one of [{role_names}]. Current role: {current_role}"
            )
        return current_user

    return _role_checker


def require_permissions(*permissions: Permission | str) -> Callable[[User], User]:
    """Dependency factory enforcing that the authenticated user possesses all specified permissions."""
    expected_perms = [
        p if isinstance(p, Permission) else Permission(str(p))
        for p in permissions
    ]

    async def _permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_all_permissions(current_user.role, expected_perms):
            user_perms = get_role_permissions(current_user.role)
            missing = [p.value for p in expected_perms if p not in user_perms]
            missing_str = ", ".join(missing)
            raise ForbiddenException(
                f"Access forbidden. Missing required permission(s): [{missing_str}]"
            )
        return current_user

    return _permission_checker


# Backward-compatible convenience dependencies
require_admin = require_roles(UserRole.ADMIN)
require_staff = require_roles(UserRole.ADMIN, UserRole.TECHNICIAN)
