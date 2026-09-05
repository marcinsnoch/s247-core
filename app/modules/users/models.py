import enum
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.workspaces.models import Workspace
    from app.modules.tickets.models import Ticket


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TECHNICIAN = "technician"
    CLIENT = "client"


class User(Base, TimestampMixin):
    """User account model for s247 platform."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]),
        default=UserRole.CLIENT,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    workspace_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    workspace: Mapped["Workspace | None"] = relationship("Workspace", back_populates="users")

    created_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", foreign_keys="Ticket.creator_id", back_populates="creator"
    )
    assigned_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", foreign_keys="Ticket.assigned_id", back_populates="assigned_to"
    )
