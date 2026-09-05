import re
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

from app.modules.users.models import UserRole


class UserBase(BaseModel):
    email: str
    full_name: str
    role: UserRole = UserRole.CLIENT
    is_active: bool = True
    workspace_id: int | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned):
            raise ValueError("Invalid email format")
        return cleaned


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    workspace_id: int | None = None
    password: str | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
