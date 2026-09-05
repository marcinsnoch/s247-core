from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.tickets.models import Ticket


class TicketRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id_with_relations(self, id_: int) -> Ticket | None:
        stmt = select(Ticket).where(Ticket.id == id_).options(
            selectinload(Ticket.creator),
            selectinload(Ticket.assigned_to)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_number(self, ticket_number: str) -> Ticket | None:
        stmt = select(Ticket).where(Ticket.ticket_number == ticket_number).options(
            selectinload(Ticket.creator),
            selectinload(Ticket.assigned_to)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        workspace_id: int | None = None,
        creator_id: int | None = None,
        assigned_id: int | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> Sequence[Ticket]:
        stmt = select(Ticket).options(
            selectinload(Ticket.creator),
            selectinload(Ticket.assigned_to)
        ).order_by(Ticket.created_at.desc())

        if workspace_id is not None:
            stmt = stmt.where(Ticket.workspace_id == workspace_id)
        if creator_id is not None:
            stmt = stmt.where(Ticket.creator_id == creator_id)
        if assigned_id is not None:
            stmt = stmt.where(Ticket.assigned_id == assigned_id)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, ticket: Ticket) -> Ticket:
        self.db.add(ticket)
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket
