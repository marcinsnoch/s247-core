from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.workspaces.models import Workspace
    from app.modules.tickets.models import Ticket


class Device(Base, TimestampMixin):
    """Machine / device registered for telemetry and technical servicing."""
    __tablename__ = "devices"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="active", nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workspace_id: Mapped[int] = mapped_column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="devices")

    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="device")
