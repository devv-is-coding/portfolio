"""Security headers and the request body limit (app/core/http_security.py)."""

import json
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import register_exception_handlers
from app.core.http_cache import HttpCacheMiddleware
from app.core.http_security import (
    BodySizeLimitMiddleware,
    FrontendOnlyMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.logging import RequestContextMiddleware
from app.main import app as real_app

LIMIT = 100


class _Body(BaseModel):
    text: str


def _client(*, hsts: bool = False) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/echo")
    async def echo(body: _Body) -> _Body:
        return body

    @app.get("/framed")
    async def framed() -> dict[str, str]:
        return {}

    app.add_middleware(BodySizeLimitMiddleware, max_bytes=LIMIT)
    app.add_middleware(SecurityHeadersMiddleware, hsts=hsts)
    return TestClient(app)


def _chunks(size: int) -> Iterator[bytes]:
    """A JSON body sent without Content-Length (chunked), in 10-byte pieces."""
    body = b'{"text": "' + b"x" * (size - 12) + b'"}'
    for start in range(0, len(body), 10):
        yield body[start : start + 10]


def test_every_response_gets_the_security_headers() -> None:
    response = _client().get("/missing")

    assert response.status_code == 404
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "Strict-Transport-Security" not in response.headers


def test_hsts_only_when_enabled() -> None:
    response = _client(hsts=True).get("/framed")

    assert response.headers["Strict-Transport-Security"] == "max-age=31536000"


def test_bodies_within_the_limit_pass() -> None:
    response = _client().post("/echo", json={"text": "x" * 50})

    assert (response.status_code, response.json()) == (200, {"text": "x" * 50})


def test_a_declared_body_over_the_limit_is_413_before_the_app_runs() -> None:
    response = _client().post("/echo", json={"text": "x" * LIMIT})

    assert response.status_code == 413
    assert response.json() == {
        "error": {
            "code": "payload_too_large",
            "message": "Request body too large",
            "details": None,
        }
    }
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_a_chunked_body_over_the_limit_is_413() -> None:
    client = _client()

    small = client.post("/echo", content=_chunks(60), headers={"Content-Type": "application/json"})
    large = client.post(
        "/echo", content=_chunks(LIMIT + 50), headers={"Content-Type": "application/json"}
    )

    assert small.status_code == 200
    assert large.status_code == 413
    assert large.json()["error"]["code"] == "payload_too_large"


def test_the_middleware_order() -> None:
    classes: list[object] = [middleware.cls for middleware in real_app.user_middleware]

    # Outermost first: headers on everything (a refused request too), the frontend gate
    # before any other work, gzip on every body, the cache and the limit inside CORS (a
    # 304 or 413 still has the CORS headers).
    assert classes == [
        RequestContextMiddleware,
        SecurityHeadersMiddleware,
        FrontendOnlyMiddleware,
        GZipMiddleware,
        CORSMiddleware,
        HttpCacheMiddleware,
        BodySizeLimitMiddleware,
    ]


FRONTEND_KEY = "a-frontend-api-key-of-at-least-32-characters"


def _gated_client(key: str | None) -> TestClient:
    app = FastAPI()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/projects")
    async def projects() -> dict[str, str]:
        return {"items": "listed"}

    app.add_middleware(FrontendOnlyMiddleware, key=key)
    app.add_middleware(SecurityHeadersMiddleware, hsts=False)
    return TestClient(app)


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-Frontend-Key": "wrong"},
        {"X-Frontend-Key": FRONTEND_KEY[:-1]},
        {"X-Frontend-Key": ""},
    ],
)
def test_the_gate_refuses_requests_without_the_frontend_key(headers: dict[str, str]) -> None:
    response = _gated_client(FRONTEND_KEY).get("/projects", headers=headers)

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "This API only answers the site's own server",
            "details": None,
        }
    }
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_the_gate_lets_the_frontend_through() -> None:
    response = _gated_client(FRONTEND_KEY).get(
        "/projects", headers={"X-Frontend-Key": FRONTEND_KEY}
    )

    assert (response.status_code, response.json()) == (200, {"items": "listed"})


def test_health_stays_open_for_health_checks() -> None:
    response = _gated_client(FRONTEND_KEY).get("/health")

    assert (response.status_code, response.json()) == (200, {"status": "ok"})


def test_without_a_key_the_gate_is_off() -> None:
    response = _gated_client(None).get("/projects")

    assert response.status_code == 200


def test_the_development_app_has_the_gate_off_and_the_docs_on() -> None:
    client = TestClient(real_app)

    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


# Imports the real app with production settings in a fresh interpreter: the app reads its
# settings once, at import, so this process's development app can't be switched over.
PRODUCTION_PROBE = """
import json, sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
key = {"X-Frontend-Key": sys.argv[1]}
print(json.dumps({
    "projects_without_key": client.get("/projects").status_code,
    "docs_without_key": client.get("/docs").status_code,
    "docs": client.get("/docs", headers=key).status_code,
    "redoc": client.get("/redoc", headers=key).status_code,
    "openapi": client.get("/openapi.json", headers=key).status_code,
    "unknown_with_key": client.get("/missing", headers=key).status_code,
}))
"""


def test_the_production_app_answers_only_the_frontend_and_hides_the_docs() -> None:
    env = os.environ | {
        "ENVIRONMENT": "production",
        "JWT_SECRET_KEY": "a-production-secret-key-of-at-least-32-chars",
        "FRONTEND_API_KEY": FRONTEND_KEY,
        "CORS_ORIGINS": "[]",
        "IMAGEKIT_PUBLIC_KEY": "public_test",
        "IMAGEKIT_PRIVATE_KEY": "private_test",
        "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/portfolio",
        "SENTRY_DSN": "",
    }
    result = subprocess.run(
        [sys.executable, "-c", PRODUCTION_PROBE, FRONTEND_KEY],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )

    assert json.loads(result.stdout.strip().splitlines()[-1]) == {
        "projects_without_key": 403,
        "docs_without_key": 403,
        "docs": 404,
        "redoc": 404,
        "openapi": 404,
        "unknown_with_key": 404,
    }
