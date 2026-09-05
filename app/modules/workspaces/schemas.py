from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WorkspaceBase(BaseModel):
    code: str
    name: str
    is_active: bool = True


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class WorkspaceResponse(WorkspaceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
