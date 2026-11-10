"""Tests against the real MariaDB (the configured DB_* database, migrated to head).

Every test runs inside one transaction that is rolled back afterwards, so nothing is
ever written: the app's own commits become savepoints (join_transaction_mode).

Locally these tests are skipped when MariaDB isn't reachable (start it with
`docker compose up --watch`). CI sets TESTS_REQUIRE_DATABASE=1, so there an
unreachable database fails the run instead of skipping it.
"""

import os
from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import pool
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.core.database import CONNECT_ARGS, get_session
from app.core.redis import get_redis
from app.main import app
from app.models import User
from app.routers.health import check_database
from tests.fakes import FakeRedis, as_redis
from tests.integration.factories import bearer_headers, create_admin_user

pytestmark = pytest.mark.anyio


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    # NullPool: each test gets a fresh connection on its own event loop.
    engine = create_async_engine(
        get_settings().database_url, poolclass=pool.NullPool, connect_args=CONNECT_ARGS
    )
    try:
        connection = await engine.connect()
    except (OSError, OperationalError) as exc:
        await engine.dispose()
        if os.environ.get("TESTS_REQUIRE_DATABASE") == "1":
            raise
        pytest.skip(f"MariaDB not reachable: {exc}")
    transaction = await connection.begin()
    session = AsyncSession(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
async def api(db_session: AsyncSession, fake_redis: FakeRedis) -> AsyncIterator[AsyncClient]:
    """HTTP client for the app, using the test transaction and an in-memory Redis."""

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def _redis() -> object:
        return as_redis(fake_redis)

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_redis] = _redis
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _no_leftover_overrides() -> Iterator[None]:
    # The real database check is used here; make sure no unit-test override leaks in.
    app.dependency_overrides.pop(check_database, None)
    yield


@pytest.fixture
async def admin(db_session: AsyncSession) -> User:
    """The admin account (ADMIN_EMAIL / ADMIN_PASSWORD from factories.py)."""
    return await create_admin_user(db_session)


@pytest.fixture
def admin_headers(admin: User) -> dict[str, str]:
    """Headers authenticating as `admin`."""
    return bearer_headers(admin)
