from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.health import check_database


async def _database_ok() -> None:
    """Unit tests don't need MariaDB: treat the database as reachable."""


@pytest.fixture
def anyio_backend() -> str:
    """Async tests (`pytest.mark.anyio`) run on asyncio, like the app."""
    return "asyncio"


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[check_database] = _database_ok
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
