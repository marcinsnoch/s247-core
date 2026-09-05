import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.database import models  # noqa: F401
from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.modules.users.models import User, UserRole
from app.modules.workspaces.models import Workspace

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        ws = Workspace(code="WS0001", name="Test Workspace", is_active=True)
        session.add(ws)
        await session.flush()

        user = User(
            email="test@s247.local",
            hashed_password=hash_password("testpass123"),
            full_name="Jan Tester",
            role=UserRole.ADMIN,
            is_active=True,
            workspace_id=ws.id
        )
        session.add(user)
        await session.commit()

        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
