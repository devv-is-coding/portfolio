from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

# Every session runs in UTC, so CURRENT_TIMESTAMP defaults and NOW() are UTC
# whatever the server's time zone is. Python code compares with naive UTC.
CONNECT_ARGS = {"init_command": "SET time_zone = '+00:00'"}

# Creating the engine doesn't connect; the first query does.
engine = create_async_engine(
    get_settings().database_url,
    pool_pre_ping=True,  # drop dead connections (e.g. after MariaDB restarts)
    pool_recycle=3600,  # stay below MariaDB's wait_timeout
    connect_args=CONNECT_ARGS,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """One session per request; closed automatically afterwards."""
    async with SessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
