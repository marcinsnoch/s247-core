from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_permissions
from app.core.rbac import Permission
from app.database.session import get_db
from app.modules.users.schemas import UserCreate, UserResponse, UserUpdate
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users Management"])


@router.get("/", response_model=list[UserResponse], summary="List users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    _auth=Depends(require_permissions(Permission.USERS_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve users list (requires users:read permission)."""
    return await UserService(db).list(skip=skip, limit=limit)


@router.post("/", response_model=UserResponse, status_code=201, summary="Create user")
async def create_user(
    data: UserCreate,
    _auth=Depends(require_permissions(Permission.USERS_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user account (requires users:create permission)."""
    return await UserService(db).create(data)


@router.get("/{user_id}", response_model=UserResponse, summary="Get user details")
async def get_user(
    user_id: int,
    _auth=Depends(require_permissions(Permission.USERS_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve single user details by ID (requires users:read permission)."""
    return await UserService(db).get_by_id(user_id)


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user")
async def update_user(
    user_id: int,
    data: UserUpdate,
    _auth=Depends(require_permissions(Permission.USERS_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    """Update user account attributes (requires users:update permission)."""
    return await UserService(db).update(user_id, data)
