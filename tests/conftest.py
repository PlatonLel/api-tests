from collections.abc import AsyncGenerator
import os
from pathlib import Path
import sys

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASS", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("SECRET", "test-secret")

from src.auth.manager import current_optional_user, current_user
from src.auth.models import User
from src.database import Base, get_db
from src.links.models import Link
from src.main import app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def db_session(tmp_path) -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=False,
    ) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def owner_user() -> User:
    return User(id=1, email="owner@example.com", hashed_password="hash")


@pytest.fixture
def other_user() -> User:
    return User(id=2, email="other@example.com", hashed_password="hash")


@pytest.fixture
def mock_optional_owner(owner_user: User):
    async def override_current_optional_user() -> User:
        return owner_user

    app.dependency_overrides[current_optional_user] = override_current_optional_user
    yield owner_user
    app.dependency_overrides.pop(current_optional_user, None)


@pytest.fixture
def mock_required_owner(owner_user: User):
    async def override_current_user() -> User:
        return owner_user

    app.dependency_overrides[current_user] = override_current_user
    yield owner_user
    app.dependency_overrides.pop(current_user, None)


@pytest.fixture
def mock_required_other(other_user: User):
    async def override_current_user() -> User:
        return other_user

    app.dependency_overrides[current_user] = override_current_user
    yield other_user
    app.dependency_overrides.pop(current_user, None)
