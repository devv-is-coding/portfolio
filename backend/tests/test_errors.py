"""Every kind of error comes back in the shared shape, without leaking internals."""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from app.core.errors import (
    ConflictError,
    NotFoundError,
    RateLimitedError,
    UnauthorizedError,
    register_exception_handlers,
)
from app.main import app as real_app


class _Body(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=12)


def _integrity_error(mariadb_code: int, message: str) -> IntegrityError:
    return IntegrityError("INSERT INTO skills ...", {}, Exception(mariadb_code, message))


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/not-found")
    async def not_found() -> None:
        raise NotFoundError("Project not found")

    @app.get("/conflict")
    async def conflict() -> None:
        raise ConflictError

    @app.get("/unauthorized")
    async def unauthorized() -> None:
        raise UnauthorizedError

    @app.get("/rate-limited")
    async def rate_limited() -> None:
        raise RateLimitedError(retry_after=30)

    @app.get("/duplicate")
    async def duplicate() -> None:
        raise _integrity_error(1062, "Duplicate entry 'python' for key 'uq_skills_slug'")

    @app.get("/foreign-key")
    async def foreign_key() -> None:
        raise _integrity_error(1452, "Cannot add or update a child row: fk_projects_media")

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("secret internal detail")

    @app.post("/validate")
    async def validate(body: _Body) -> None:
        return None

    return app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(_build_app(), raise_server_exceptions=False) as test_client:
        yield test_client


def _error(code: str, message: str) -> dict[str, object]:
    return {"error": {"code": code, "message": message, "details": None}}


@pytest.mark.parametrize(
    ("path", "status", "code", "message"),
    [
        ("/not-found", 404, "not_found", "Project not found"),
        ("/conflict", 409, "conflict", "The request conflicts with existing data"),
        ("/unauthorized", 401, "unauthorized", "Not authenticated"),
        ("/rate-limited", 429, "rate_limited", "Too many requests, try again later"),
        ("/duplicate", 409, "conflict", "A record with these values already exists"),
        ("/foreign-key", 409, "conflict", "The request conflicts with existing data"),
        ("/crash", 500, "internal_error", "Internal server error"),
        ("/no-such-route", 404, "not_found", "Not Found"),
    ],
)
def test_errors_use_the_shared_shape(
    client: TestClient, path: str, status: int, code: str, message: str
) -> None:
    response = client.get(path)

    assert response.status_code == status
    assert response.json() == _error(code, message)


def test_headers_are_kept(client: TestClient) -> None:
    assert client.get("/unauthorized").headers["www-authenticate"] == "Bearer"
    assert client.get("/rate-limited").headers["retry-after"] == "30"


def test_internals_never_leak(client: TestClient) -> None:
    for path in ("/crash", "/duplicate", "/foreign-key"):
        body = client.get(path).text
        for leak in (
            "secret internal detail",
            "INSERT",
            "uq_skills_slug",
            "fk_projects",
            "Traceback",
        ):
            assert leak not in body


def test_duplicate_values_never_reach_the_log(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level("INFO", logger="app.core.errors"):
        client.get("/duplicate")
        client.get("/foreign-key")

    assert "python" not in caplog.text  # the duplicate value
    assert "Duplicate value on GET /duplicate" in caplog.text
    assert "fk_projects_media" in caplog.text  # constraint names stay, for debugging


def test_wrong_method_is_405(client: TestClient) -> None:
    response = client.delete("/not-found")

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_validation_errors_list_each_field_without_echoing_input(client: TestClient) -> None:
    response = client.post("/validate", json={"email": "a", "password": "secret-pw"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["message"] == "Invalid request"
    assert [(d["field"], d["type"]) for d in error["details"]] == [
        ("body.email", "string_too_short"),
        ("body.password", "string_too_short"),
    ]
    assert "secret-pw" not in response.text


def test_openapi_documents_only_the_shared_error_shape() -> None:
    schema = real_app.openapi()

    assert "HTTPValidationError" not in schema["components"]["schemas"]
    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            for status, response in operation["responses"].items():
                if status.startswith(("4", "5")):
                    ref = response["content"]["application/json"]["schema"]["$ref"]
                    assert ref.endswith("/ErrorResponse"), (method, path, status)
