import logging
from collections.abc import AsyncIterator
from typing import Any

import pytest
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
    assert response.json() == {
        "error": {"code": "service_unavailable", "message": "Database unavailable", "details": None}
    }


def test_passing_health_checks_stay_out_of_the_info_log(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="app.access")

    client.get("/health")

    assert [r for r in caplog.records if r.name == "app.access"] == []


def test_failing_health_checks_are_logged(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="app.access")
    app.dependency_overrides.pop(check_database)
    app.dependency_overrides[get_session] = _unreachable_session

    client.get("/health")

    [access] = [r for r in caplog.records if r.name == "app.access"]
    assert access.levelno == logging.INFO
    assert access.getMessage().startswith("GET /health 503 ")
