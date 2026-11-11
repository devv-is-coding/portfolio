import json
import logging
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import register_exception_handlers
from app.core.logging import (
    REQUEST_ID_HEADER,
    JsonFormatter,
    RequestContextMiddleware,
    configure_logging,
    request_id_var,
)
from tests.fakes import IsolatedSettings, field


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.add_middleware(RequestContextMiddleware)

    @app.get("/ok")
    async def ok() -> dict[str, str | None]:
        logging.getLogger("app.test").info("inside the request")
        return {"request_id": request_id_var.get()}

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("secret internal detail")

    return app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(_build_app()) as test_client:
        yield test_client


def test_generates_a_request_id_and_returns_it(client: TestClient) -> None:
    response = client.get("/ok")

    request_id = response.headers[REQUEST_ID_HEADER]
    assert len(request_id) == 32
    assert response.json() == {"request_id": request_id}


def test_keeps_a_valid_incoming_request_id(client: TestClient) -> None:
    response = client.get("/ok", headers={REQUEST_ID_HEADER: "abc-123.DEF_4"})

    assert response.headers[REQUEST_ID_HEADER] == "abc-123.DEF_4"


@pytest.mark.parametrize("incoming", ["has space", "x" * 65, "new\nline", "<script>"])
def test_replaces_an_invalid_incoming_request_id(client: TestClient, incoming: str) -> None:
    response = client.get("/ok", headers={REQUEST_ID_HEADER: incoming})

    assert response.headers[REQUEST_ID_HEADER] != incoming
    assert len(response.headers[REQUEST_ID_HEADER]) == 32


def test_every_log_line_of_a_request_has_its_request_id(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)

    request_id = client.get("/ok").headers[REQUEST_ID_HEADER]

    inside = next(r for r in caplog.records if r.getMessage() == "inside the request")
    access = next(r for r in caplog.records if r.name == "app.access")
    assert field(inside, "request_id") == request_id
    assert field(access, "request_id") == request_id
    assert access.getMessage().startswith("GET /ok 200 ")
    assert (
        field(access, "method"),
        field(access, "path"),
        field(access, "status"),
        field(access, "user_id"),
    ) == ("GET", "/ok", 200, None)


def test_access_log_has_no_query_string(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)

    client.get("/ok", params={"token": "secret-value"})

    app_lines = [r.getMessage() for r in caplog.records if r.name.startswith("app.")]
    assert app_lines
    assert not any("secret-value" in line for line in app_lines)


def test_unexpected_error_is_logged_with_request_id_and_answered_with_500(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    response = client.get("/crash")

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Internal server error", "details": None}
    }
    request_id = response.headers[REQUEST_ID_HEADER]
    logged = next(r for r in caplog.records if r.levelno == logging.ERROR)
    assert field(logged, "request_id") == request_id
    assert logged.exc_info is not None
    access = next(r for r in caplog.records if r.name == "app.access")
    assert field(access, "status") == 500
    assert "secret internal detail" not in response.text


def test_json_formatter_writes_one_object_with_the_fields() -> None:
    record = logging.LogRecord("app.access", logging.INFO, __file__, 1, "GET /x 200", (), None)
    record.request_id = "abc"
    record.status = 200

    entry = json.loads(JsonFormatter().format(record))

    assert entry["message"] == "GET /x 200"
    assert entry["request_id"] == "abc"
    assert entry["status"] == 200
    assert entry["level"] == "INFO"


def test_configure_logging_is_idempotent_and_applies_the_level() -> None:
    root = logging.getLogger()
    before_level, before_handlers = root.level, root.handlers[:]
    try:
        settings = IsolatedSettings(log_level="WARNING", log_format="json")
        configure_logging(settings)
        configure_logging(settings)

        assert root.level == logging.WARNING
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, JsonFormatter)
    finally:
        root.setLevel(before_level)
        root.handlers = before_handlers
