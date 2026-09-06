from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_permissions
from app.core.rbac import Permission
from app.database.session import get_db
from app.modules.devices.schemas import DeviceCreate, DeviceResponse, DeviceUpdate
from app.modules.devices.service import DeviceService
from app.modules.users.models import User, UserRole

router = APIRouter(prefix="/devices", tags=["Devices & Telemetry"])


@router.get("/", response_model=list[DeviceResponse], summary="List devices")
async def list_devices(
    workspace_id: int | None = Query(None, description="Filter by workspace ID"),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_permissions(Permission.DEVICES_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve registered devices (requires devices:read permission)."""
    target_ws = current_user.workspace_id if current_user.role == UserRole.CLIENT else workspace_id
    return await DeviceService(db).list(workspace_id=target_ws, skip=skip, limit=limit)


@router.post("/", response_model=DeviceResponse, status_code=201, summary="Register device")
async def create_device(
    data: DeviceCreate,
    _staff: User = Depends(require_permissions(Permission.DEVICES_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    """Register a new device for diagnostics (requires devices:create permission)."""
    return await DeviceService(db).create(data)


@router.get("/{device_id}", response_model=DeviceResponse, summary="Get device details")
async def get_device(
    device_id: int,
    _current_user: User = Depends(require_permissions(Permission.DEVICES_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve device details by ID (requires devices:read permission)."""
    return await DeviceService(db).get_by_id(device_id)


@router.patch("/{device_id}", response_model=DeviceResponse, summary="Update device")
async def update_device(
    device_id: int,
    data: DeviceUpdate,
    _staff: User = Depends(require_permissions(Permission.DEVICES_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    """Update device metadata or operating status (requires devices:update permission)."""
    return await DeviceService(db).update(device_id, data)
