from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.modules.profile.service import ProfileService
from app.modules.users.models import User
from app.modules.users.schemas import PasswordChangeRequest, UserResponse, UserUpdate

router = APIRouter(prefix="/me", tags=["User Profile"])


@router.get("", response_model=UserResponse, summary="Get current user profile")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Retrieve profile details of the authenticated user."""
    return current_user


@router.patch("", response_model=UserResponse, summary="Update current user profile")
async def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Selectively update current user profile fields."""
    return await ProfileService(db).update_profile(current_user.id, data)


@router.post("/change-password", status_code=204, summary="Change current password")
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user password verifying previous password."""
    await ProfileService(db).change_password(current_user.id, data)
