from collections.abc import AsyncIterator
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.database import get_session
from app.main import app
from app.routers.health import check_database


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


class _UnreachableSession:
    async def execute(self, *_args: Any, **_kwargs: Any) -> None:
        raise OperationalError("SELECT 1", {}, Exception("Can't connect to MariaDB"))


async def _unreachable_session() -> AsyncIterator[_UnreachableSession]:
    yield _UnreachableSession()


def test_health_returns_503_when_database_is_unreachable(client: TestClient) -> None:
    # Use the real database check, but with a session whose queries fail.
    app.dependency_overrides.pop(check_database)
    app.dependency_overrides[get_session] = _unreachable_session

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
