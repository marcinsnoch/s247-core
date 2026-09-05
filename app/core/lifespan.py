from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from sqlalchemy import select

from app.core.security import hash_password
from app.database import models  # noqa: F401
from app.database.base import Base
from app.database.session import AsyncSessionLocal, engine
from app.modules.users.models import User, UserRole
from app.modules.workspaces.models import Workspace

logger = logging.getLogger(__name__)


async def seed_initial_data() -> None:
    """Seed initial workspace and administrator account if the database is empty."""
    async with AsyncSessionLocal() as session:
        # 1. Default Workspace WS0001
        res_ws = await session.execute(select(Workspace).where(Workspace.code == "WS0001"))
        default_ws = res_ws.scalar_one_or_none()
        if not default_ws:
            default_ws = Workspace(
                code="WS0001",
                name="Main Workshop s247",
                is_active=True
            )
            session.add(default_ws)
            await session.flush()
            logger.info("Seeded default workspace: WS0001.")

        # 2. Default Administrator
        res_user = await session.execute(select(User).where(User.email == "admin@s247.local"))
        admin_user = res_user.scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                email="admin@s247.local",
                hashed_password=hash_password("admin123"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
                workspace_id=default_ws.id
            )
            session.add(admin_user)
            logger.info("Seeded default administrator account: admin@s247.local (password: admin123).")

        await session.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager handling startup and shutdown events."""
    logger.info("Starting s247 Core API... Initializing database schema.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        await seed_initial_data()
    except Exception as e:
        logger.warning("Error during initial data seeding (tables may already exist): %s", e)

    yield

    logger.info("Shutting down s247 Core API... Disposing database connections.")
    await engine.dispose()
