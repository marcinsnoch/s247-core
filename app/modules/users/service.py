from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserUpdate
from app.shared.exceptions import ConflictException, NotFoundException


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    async def get_by_id(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self.repo.get_by_email(email)

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        return await self.repo.list(skip=skip, limit=limit)

    async def create(self, data: UserCreate) -> User:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise ConflictException(f"User with email {data.email} already exists")

        new_user = User(
            email=data.email.lower().strip(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            is_active=data.is_active,
            workspace_id=data.workspace_id
        )
        created = await self.repo.create(new_user)
        await self.db.commit()
        return created

    async def update(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get_by_id(user_id)

        if data.full_name is not None:
            user.full_name = data.full_name
        if data.role is not None:
            user.role = data.role
        if data.is_active is not None:
            user.is_active = data.is_active
        if data.workspace_id is not None:
            user.workspace_id = data.workspace_id
        if data.password:
            user.hashed_password = hash_password(data.password)

        await self.db.commit()
        await self.db.refresh(user)
        return user
