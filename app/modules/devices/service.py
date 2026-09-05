from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.devices.models import Device
from app.modules.devices.repository import DeviceRepository
from app.modules.devices.schemas import DeviceCreate, DeviceUpdate
from app.shared.exceptions import ConflictException, NotFoundException


class DeviceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DeviceRepository(db)

    async def get_by_id(self, device_id: int) -> Device:
        device = await self.repo.get_by_id(device_id)
        if not device:
            raise NotFoundException("Device not found")
        return device

    async def list(self, workspace_id: int | None = None, skip: int = 0, limit: int = 100) -> Sequence[Device]:
        return await self.repo.list(workspace_id=workspace_id, skip=skip, limit=limit)

    async def create(self, data: DeviceCreate) -> Device:
        existing = await self.repo.get_by_code(data.code)
        if existing:
            raise ConflictException(f"Device with code {data.code} already exists")

        device = Device(
            code=data.code.strip(),
            name=data.name,
            model=data.model,
            status=data.status,
            workspace_id=data.workspace_id
        )
        created = await self.repo.create(device)
        await self.db.commit()
        return created

    async def update(self, device_id: int, data: DeviceUpdate) -> Device:
        device = await self.get_by_id(device_id)
        if data.name is not None:
            device.name = data.name
        if data.model is not None:
            device.model = data.model
        if data.status is not None:
            device.status = data.status
        if data.workspace_id is not None:
            device.workspace_id = data.workspace_id
        await self.db.commit()
        await self.db.refresh(device)
        return device
