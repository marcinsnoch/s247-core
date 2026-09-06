import enum
from typing import Sequence

from app.modules.users.models import UserRole


class Permission(str, enum.Enum):
    """Fine-grained atomic system permissions."""

    # Users management
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"

    # Workspaces (tenants)
    WORKSPACES_READ = "workspaces:read"
    WORKSPACES_CREATE = "workspaces:create"
    WORKSPACES_UPDATE = "workspaces:update"
    WORKSPACES_DELETE = "workspaces:delete"

    # Service tickets
    TICKETS_READ = "tickets:read"
    TICKETS_CREATE = "tickets:create"
    TICKETS_UPDATE = "tickets:update"
    TICKETS_ASSIGN = "tickets:assign"
    TICKETS_STATUS = "tickets:status"
    TICKETS_DELETE = "tickets:delete"

    # Devices & telemetry
    DEVICES_READ = "devices:read"
    DEVICES_CREATE = "devices:create"
    DEVICES_UPDATE = "devices:update"
    DEVICES_DELETE = "devices:delete"

    # Self profile
    PROFILE_READ = "profile:read"
    PROFILE_UPDATE = "profile:update"


# Role-to-Permissions RBAC matrix
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.ADMIN: set(Permission),  # Admins possess all permissions
    UserRole.TECHNICIAN: {
        # Users & Workspaces (read-only for operational context)
        Permission.USERS_READ,
        Permission.WORKSPACES_READ,
        # Tickets full servicing
        Permission.TICKETS_READ,
        Permission.TICKETS_CREATE,
        Permission.TICKETS_UPDATE,
        Permission.TICKETS_ASSIGN,
        Permission.TICKETS_STATUS,
        # Devices registration & maintenance
        Permission.DEVICES_READ,
        Permission.DEVICES_CREATE,
        Permission.DEVICES_UPDATE,
        # Profile
        Permission.PROFILE_READ,
        Permission.PROFILE_UPDATE,
    },
    UserRole.CLIENT: {
        # Tickets access for their own workspace
        Permission.TICKETS_READ,
        Permission.TICKETS_CREATE,
        Permission.TICKETS_UPDATE,
        # Read-only access to devices in their workspace
        Permission.DEVICES_READ,
        # Profile
        Permission.PROFILE_READ,
        Permission.PROFILE_UPDATE,
    },
}


def _normalize_role(role: UserRole | str) -> UserRole:
    if isinstance(role, UserRole):
        return role
    try:
        return UserRole(str(role).lower())
    except ValueError:
        return UserRole.CLIENT


def get_role_permissions(role: UserRole | str) -> set[Permission]:
    """Retrieve all effective permissions for a given user role."""
    normalized = _normalize_role(role)
    return ROLE_PERMISSIONS.get(normalized, set())


def has_permission(role: UserRole | str, permission: Permission | str) -> bool:
    """Check if a given role grants a specific permission."""
    perms = get_role_permissions(role)
    perm_val = permission.value if isinstance(permission, Permission) else str(permission)
    return any(p.value == perm_val for p in perms)


def has_all_permissions(role: UserRole | str, permissions: Sequence[Permission | str]) -> bool:
    """Check if a given role grants all specified permissions."""
    return all(has_permission(role, p) for p in permissions)
