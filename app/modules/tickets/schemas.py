from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.modules.tickets.models import TicketPriority, TicketStatus
from app.modules.users.schemas import UserResponse


class TicketBase(BaseModel):
    title: str
    description: str
    priority: TicketPriority = TicketPriority.NORMAL
    device_id: int | None = None


class TicketCreate(TicketBase):
    workspace_id: int | None = None


class TicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_id: int | None = None
    device_id: int | None = None


class TicketResponse(TicketBase):
    id: int
    ticket_number: str
    status: TicketStatus
    workspace_id: int
    creator_id: int | None
    assigned_id: int | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None

    creator: UserResponse | None = None
    assigned_to: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)
