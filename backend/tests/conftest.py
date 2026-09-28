"""
Shared pytest fixtures.

SAFETY: these fixtures create and DROP all tables. They therefore hard-set
the database URL to a dedicated *_test database and refuse to run against
anything else, so a test run can never wipe the development data.
"""

import os

os.environ["TRIAGE_PROVIDER"] = "simulated"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://civicpulse:localdevpassword@localhost:5432/civicpulse_test",
)
os.environ["REDIS_URL"] = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/1")

assert os.environ["DATABASE_URL"].endswith("_test"), (
    "Refusing to run tests: DATABASE_URL must point at a database whose name ends in '_test'"
)

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from redis.asyncio import Redis  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def db_engine():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncSession:
    session_factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def redis_client():
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


@pytest_asyncio.fixture
async def client(db_engine, db_session, redis_client):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # The lifespan block does not run under ASGITransport, so set app state by hand.
    app.state.redis = redis_client
    app.state.db_engine = db_engine

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()