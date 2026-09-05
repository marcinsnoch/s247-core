from typing import TYPE_CHECKING
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models import User
    from app.modules.devices.models import Device
    from app.modules.tickets.models import Ticket


class Workspace(Base, TimestampMixin):
    """Workspace / tenant entity, matching RabbitMQ vhosts (e.g. WS0001)."""
    __tablename__ = "workspaces"

    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="workspace", cascade="all, delete-orphan")
    devices: Mapped[list["Device"]] = relationship("Device", back_populates="workspace", cascade="all, delete-orphan")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="workspace", cascade="all, delete-orphan")
