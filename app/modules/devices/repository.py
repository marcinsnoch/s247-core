from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.devices.models import Device


class DeviceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, device_id: int) -> Device | None:
        return await self.db.get(Device, device_id)

    async def get_by_code(self, code: str) -> Device | None:
        stmt = select(Device).where(Device.code == code.strip())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, workspace_id: int | None = None, skip: int = 0, limit: int = 100) -> Sequence[Device]:
        stmt = select(Device)
        if workspace_id is not None:
            stmt = stmt.where(Device.workspace_id == workspace_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create(self, device: Device) -> Device:
        self.db.add(device)
        await self.db.flush()
        await self.db.refresh(device)
        return device
