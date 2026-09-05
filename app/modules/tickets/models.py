from datetime import datetime
import enum
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.workspaces.models import Workspace
    from app.modules.users.models import User
    from app.modules.devices.models import Device


class TicketStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_PARTS = "waiting_for_parts"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class Ticket(Base, TimestampMixin):
    """Service request / ticket entity in s247 platform."""
    __tablename__ = "tickets"

    ticket_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status", values_callable=lambda x: [e.value for e in x]),
        default=TicketStatus.NEW,
        nullable=False
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority", values_callable=lambda x: [e.value for e in x]),
        default=TicketPriority.NORMAL,
        nullable=False
    )

    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="tickets")

    device_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    device: Mapped["Device | None"] = relationship("Device", back_populates="tickets")

    creator_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[creator_id], back_populates="created_tickets")

    assigned_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_to: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_id], back_populates="assigned_tickets")

    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
