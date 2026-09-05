from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DeviceBase(BaseModel):
    code: str
    name: str
    model: str | None = None
    status: str = "active"
    workspace_id: int


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: str | None = None
    model: str | None = None
    status: str | None = None
    workspace_id: int | None = None


class DeviceResponse(DeviceBase):
    id: int
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
