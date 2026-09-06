from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_permissions
from app.core.rbac import Permission
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
    current_user: User = Depends(require_permissions(Permission.TICKETS_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve service tickets filtered by user permissions and workspace (requires tickets:read)."""
    return await TicketService(db).list_tickets(
        current_user=current_user,
        workspace_id=workspace_id,
        skip=skip,
        limit=limit
    )


@router.post("/", response_model=TicketResponse, status_code=201, summary="Create service ticket")
async def create_ticket(
    data: TicketCreate,
    current_user: User = Depends(require_permissions(Permission.TICKETS_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new service ticket (requires tickets:create)."""
    return await TicketService(db).create_ticket(data, current_user)


@router.get("/{ticket_id}", response_model=TicketResponse, summary="Get ticket details")
async def get_ticket(
    ticket_id: int,
    current_user: User = Depends(require_permissions(Permission.TICKETS_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve single ticket details by ID (requires tickets:read)."""
    return await TicketService(db).get_ticket(ticket_id, current_user)


@router.patch("/{ticket_id}", response_model=TicketResponse, summary="Update service ticket")
async def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    current_user: User = Depends(require_permissions(Permission.TICKETS_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    """Update service ticket status, description, or technician assignment (requires tickets:update)."""
    return await TicketService(db).update_ticket(ticket_id, data, current_user)
