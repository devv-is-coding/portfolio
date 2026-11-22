from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

# MariaDB closes a connection that has been unused this long. The pool would otherwise
# keep its connections open forever, and a free serverless database (Layerbase) only
# sleeps once no connection is open: kept awake around the clock, it gets paused.
IDLE_CONNECTION_TIMEOUT_SECONDS = 300
# Reopen a pooled connection before MariaDB can have closed it, so no request ever
# gets a dead one.
POOL_RECYCLE_SECONDS = IDLE_CONNECTION_TIMEOUT_SECONDS - 60

# Every session runs in UTC, so CURRENT_TIMESTAMP defaults and NOW() are UTC
# whatever the server's time zone is. Python code compares with naive UTC.
CONNECT_ARGS = {
    "init_command": f"SET time_zone = '+00:00', wait_timeout = {IDLE_CONNECTION_TIMEOUT_SECONDS}"
}

# Creating the engine doesn't connect; the first query does.
_settings = get_settings()
engine = create_async_engine(
    _settings.database_url,
    pool_size=_settings.db_pool_size,
    max_overflow=_settings.db_max_overflow,
    pool_pre_ping=True,  # drop dead connections (e.g. after MariaDB restarts)
    pool_recycle=POOL_RECYCLE_SECONDS,
    connect_args=CONNECT_ARGS,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """One session per request; closed automatically afterwards."""
    async with SessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def ping(session: AsyncSession) -> None:
    """Run `SELECT 1`. Raises SQLAlchemyError when MariaDB can't be reached."""
    await session.execute(text("SELECT 1"))
