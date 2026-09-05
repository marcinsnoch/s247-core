from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import PasswordChangeRequest, UserUpdate
from app.shared.exceptions import BaseAppException, NotFoundException


class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_profile(self, user_id: int) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User profile not found")
        return user

    async def update_profile(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get_profile(user_id)
        if data.full_name is not None:
            user.full_name = data.full_name
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user_id: int, data: PasswordChangeRequest) -> None:
        user = await self.get_profile(user_id)
        if not verify_password(data.current_password, user.hashed_password):
            raise BaseAppException(
                status_code=400,
                message="Current password is incorrect",
                error_code="INVALID_PASSWORD",
                field="current_password"
            )

        user.hashed_password = hash_password(data.new_password)
        await self.db.commit()
