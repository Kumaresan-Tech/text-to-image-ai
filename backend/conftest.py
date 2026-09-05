import os
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_db
from app.models.base import Base
from app.services.auth_service import create_access_token, hash_password


# ── Test Database ─────────────────────────────────
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/text2img_test",
)


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False, pool_size=10, pool_pre_ping=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture
async def client(engine) -> AsyncGenerator[AsyncClient, None]:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        session = session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Test User ─────────────────────────────────────
@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    from app.models import User

    user = User(
        id=str(uuid.uuid4()),
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        name="Test User",
        hashed_password=hash_password("TestPass123!"),
        credits=100,
        plan="FREE",
        role="user",
        is_active=True,
        is_banned=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession):
    from app.models import User

    admin = User(
        id=str(uuid.uuid4()),
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        name="Test Admin",
        hashed_password=hash_password("AdminPass123!"),
        credits=999,
        plan="PRO",
        role="admin",
        is_active=True,
        is_banned=False,
    )
    db_session.add(admin)
    await db_session.commit()
    return admin


@pytest.fixture
def user_token(test_user) -> str:
    return create_access_token(str(test_user.id))


@pytest.fixture
def admin_token(test_admin) -> str:
    return create_access_token(str(test_admin.id))


@pytest.fixture
def auth_headers(user_token) -> dict:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


# ── Mock External Services ────────────────────────
@pytest.fixture(autouse=True)
def mock_storage():
    with patch("app.services.storage_service.StorageService") as mock:
        storage = AsyncMock()
        storage.upload_file.return_value = "https://storage.example.com/test.png"
        storage.get_public_url.return_value = "https://storage.example.com/test.png"
        mock.return_value = storage
        yield storage


@pytest.fixture
def mock_ai_provider():
    mock = AsyncMock()
    mock.generate.return_value = MagicMock(
        images=[MagicMock(url="https://example.com/image.png")],
        seed=42,
    )
    return mock


@pytest.fixture
def mock_llm_client():
    mock = AsyncMock()
    mock.enhance.return_value = "enhanced prompt with more detail"
    mock.optimize.return_value = "optimized prompt for better results"
    mock.generate_negative.return_value = "blurry, low quality, watermark"
    mock.suggest.return_value = ["a futuristic city", "a mountain landscape"]
    mock.safety_check.return_value = (True, [])
    return mock
