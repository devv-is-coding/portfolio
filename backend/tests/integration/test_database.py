"""The session settings every connection gets (CONNECT_ARGS)."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import IDLE_CONNECTION_TIMEOUT_SECONDS, POOL_RECYCLE_SECONDS

pytestmark = pytest.mark.anyio


async def test_connections_run_in_utc(db_session: AsyncSession) -> None:
    zone = await db_session.scalar(text("SELECT @@session.time_zone"))

    assert zone == "+00:00"


async def test_unused_connections_are_closed_by_mariadb(db_session: AsyncSession) -> None:
    # Otherwise the pool keeps them open forever and a serverless database never sleeps.
    timeout = await db_session.scalar(text("SELECT @@session.wait_timeout"))

    assert timeout == IDLE_CONNECTION_TIMEOUT_SECONDS


def test_the_pool_replaces_connections_before_mariadb_closes_them() -> None:
    assert 0 < POOL_RECYCLE_SECONDS < IDLE_CONNECTION_TIMEOUT_SECONDS
