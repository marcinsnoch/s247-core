from typing import Sequence
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_permissions
from app.core.rbac import Permission
from app.database.session import get_db
from app.modules.workspaces.schemas import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.modules.workspaces.service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces (Tenants)"])


@router.get("/", response_model=list[WorkspaceResponse], summary="List workspaces")
async def list_workspaces(
    skip: int = 0,
    limit: int = 100,
    _auth=Depends(require_permissions(Permission.WORKSPACES_READ)),
    db: AsyncSession = Depends(get_db),
):
    """List registered workspaces (requires workspaces:read permission)."""
    return await WorkspaceService(db).list_all(skip=skip, limit=limit)


@router.post("/", response_model=WorkspaceResponse, status_code=201, summary="Create workspace")
async def create_workspace(
    data: WorkspaceCreate,
    _auth=Depends(require_permissions(Permission.WORKSPACES_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    """Register a new workspace / tenant (requires workspaces:create permission)."""
    return await WorkspaceService(db).create(data)


@router.get("/{workspace_id}", response_model=WorkspaceResponse, summary="Get workspace details")
async def get_workspace(
    workspace_id: int,
    _auth=Depends(require_permissions(Permission.WORKSPACES_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve workspace details by ID (requires workspaces:read permission)."""
    return await WorkspaceService(db).get_by_id(workspace_id)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse, summary="Update workspace")
async def update_workspace(
    workspace_id: int,
    data: WorkspaceUpdate,
    _auth=Depends(require_permissions(Permission.WORKSPACES_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    """Update workspace attributes (requires workspaces:update permission)."""
    return await WorkspaceService(db).update(workspace_id, data)
