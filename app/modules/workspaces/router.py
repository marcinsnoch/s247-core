from typing import Sequence
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.database.session import get_db
from app.modules.workspaces.schemas import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate
from app.modules.workspaces.service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces (Tenants)"])


@router.get("/", response_model=list[WorkspaceResponse], summary="List workspaces")
async def list_workspaces(
    skip: int = 0,
    limit: int = 100,
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all registered workspaces (admin only)."""
    return await WorkspaceService(db).list_all(skip=skip, limit=limit)


@router.post("/", response_model=WorkspaceResponse, status_code=201, summary="Create workspace")
async def create_workspace(
    data: WorkspaceCreate,
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Register a new workspace / tenant (admin only)."""
    return await WorkspaceService(db).create(data)


@router.get("/{workspace_id}", response_model=WorkspaceResponse, summary="Get workspace details")
async def get_workspace(
    workspace_id: int,
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve workspace details by ID."""
    return await WorkspaceService(db).get_by_id(workspace_id)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse, summary="Update workspace")
async def update_workspace(
    workspace_id: int,
    data: WorkspaceUpdate,
    _admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update workspace attributes."""
    return await WorkspaceService(db).update(workspace_id, data)
