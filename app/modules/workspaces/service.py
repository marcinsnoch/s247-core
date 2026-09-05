from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workspaces.models import Workspace
from app.modules.workspaces.repository import WorkspaceRepository
from app.modules.workspaces.schemas import WorkspaceCreate, WorkspaceUpdate
from app.shared.exceptions import ConflictException, NotFoundException


class WorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = WorkspaceRepository(db)

    async def get_by_id(self, workspace_id: int) -> Workspace:
        ws = await self.repo.get_by_id(workspace_id)
        if not ws:
            raise NotFoundException("Workspace not found")
        return ws

    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[Workspace]:
        return await self.repo.list(skip=skip, limit=limit)

    async def create(self, data: WorkspaceCreate) -> Workspace:
        existing = await self.repo.get_by_code(data.code)
        if existing:
            raise ConflictException(f"Workspace with code {data.code} already exists")

        ws = Workspace(
            code=data.code.strip().upper(),
            name=data.name,
            is_active=data.is_active
        )
        created = await self.repo.create(ws)
        await self.db.commit()
        return created

    async def update(self, workspace_id: int, data: WorkspaceUpdate) -> Workspace:
        ws = await self.get_by_id(workspace_id)
        if data.name is not None:
            ws.name = data.name
        if data.is_active is not None:
            ws.is_active = data.is_active
        await self.db.commit()
        await self.db.refresh(ws)
        return ws
