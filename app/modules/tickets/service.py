from datetime import datetime, timezone
import random
import string
from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tickets.models import Ticket, TicketStatus
from app.modules.tickets.repository import TicketRepository
from app.modules.tickets.schemas import TicketCreate, TicketUpdate
from app.modules.users.models import User, UserRole
from app.shared.exceptions import BaseAppException, ForbiddenException, NotFoundException


class TicketService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TicketRepository(db)

    def _generate_ticket_number(self) -> str:
        year = datetime.now(timezone.utc).year
        random_suffix = "".join(random.choices(string.digits, k=5))
        return f"TICK-{year}-{random_suffix}"

    async def create_ticket(self, data: TicketCreate, current_user: User) -> Ticket:
        workspace_id = data.workspace_id or current_user.workspace_id
        if not workspace_id:
            raise BaseAppException(
                status_code=400,
                message="workspace_id is required or user must be assigned to a workspace",
                error_code="WORKSPACE_REQUIRED"
            )

        ticket = Ticket(
            ticket_number=self._generate_ticket_number(),
            title=data.title,
            description=data.description,
            priority=data.priority,
            status=TicketStatus.NEW,
            workspace_id=workspace_id,
            device_id=data.device_id,
            creator_id=current_user.id
        )
        created = await self.repo.create(ticket)
        await self.db.commit()
        return await self.repo.get_by_id_with_relations(created.id) or created

    async def get_ticket(self, ticket_id: int, current_user: User) -> Ticket:
        ticket = await self.repo.get_by_id_with_relations(ticket_id)
        if not ticket:
            raise NotFoundException("Service ticket not found")

        if current_user.role == UserRole.CLIENT:
            if ticket.creator_id != current_user.id and ticket.workspace_id != current_user.workspace_id:
                raise ForbiddenException("Access to this ticket is forbidden")

        return ticket

    async def list_tickets(
        self,
        current_user: User,
        workspace_id: int | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Ticket]:
        if current_user.role == UserRole.CLIENT:
            return await self.repo.list_filtered(
                workspace_id=current_user.workspace_id,
                creator_id=current_user.id,
                skip=skip,
                limit=limit
            )
        return await self.repo.list_filtered(
            workspace_id=workspace_id,
            skip=skip,
            limit=limit
        )

    async def update_ticket(self, ticket_id: int, data: TicketUpdate, current_user: User) -> Ticket:
        ticket = await self.get_ticket(ticket_id, current_user)

        if data.title is not None:
            ticket.title = data.title
        if data.description is not None:
            ticket.description = data.description
        if data.priority is not None:
            ticket.priority = data.priority
        if data.device_id is not None:
            ticket.device_id = data.device_id

        if data.status is not None:
            ticket.status = data.status
            if data.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED) and not ticket.closed_at:
                ticket.closed_at = datetime.now(timezone.utc)
            elif data.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
                ticket.closed_at = None

        if data.assigned_id is not None and current_user.role in (UserRole.ADMIN, UserRole.TECHNICIAN):
            ticket.assigned_id = data.assigned_id

        await self.db.commit()
        await self.db.refresh(ticket)
        return await self.repo.get_by_id_with_relations(ticket.id) or ticket
