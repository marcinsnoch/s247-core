from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin, require_staff
from app.database.session import get_db
from app.modules.users.schemas import UserCreate, UserResponse, UserUpdate
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users Management"])


@router.get("/", response_model=list[UserResponse], summary="List users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    _staff=Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve users list (requires staff privileges)."""
    return await UserService(db).list(skip=skip, limit=limit)


@router.post("/", response_model=UserResponse, status_code=201, summary="Create user")
async def create_user(
    data: UserCreate,
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user account (requires admin privileges)."""
    return await UserService(db).create(data)


@router.get("/{user_id}", response_model=UserResponse, summary="Get user details")
async def get_user(
    user_id: int,
    _staff=Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve single user details by ID."""
    return await UserService(db).get_by_id(user_id)


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user")
async def update_user(
    user_id: int,
    data: UserUpdate,
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user account attributes (requires admin privileges)."""
    return await UserService(db).update(user_id, data)
