from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.modules.tickets.schemas import TicketCreate, TicketResponse, TicketUpdate
from app.modules.tickets.service import TicketService
from app.modules.users.models import User

router = APIRouter(prefix="/tickets", tags=["Service Tickets"])


@router.get("/", response_model=list[TicketResponse], summary="List service tickets")
async def list_tickets(
    workspace_id: int | None = Query(None, description="Filter by workspace ID"),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve service tickets filtered by user permissions and workspace."""
    return await TicketService(db).list_tickets(
        current_user=current_user,
        workspace_id=workspace_id,
        skip=skip,
        limit=limit
    )


@router.post("/", response_model=TicketResponse, status_code=201, summary="Create service ticket")
async def create_ticket(
    data: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new service ticket."""
    return await TicketService(db).create_ticket(data, current_user)


@router.get("/{ticket_id}", response_model=TicketResponse, summary="Get ticket details")
async def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve single ticket details by ID."""
    return await TicketService(db).get_ticket(ticket_id, current_user)


@router.patch("/{ticket_id}", response_model=TicketResponse, summary="Update service ticket")
async def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update service ticket status, description, or technician assignment."""
    return await TicketService(db).update_ticket(ticket_id, data, current_user)
