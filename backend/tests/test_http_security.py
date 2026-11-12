"""Security headers and the request body limit (app/core/http_security.py)."""

from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import register_exception_handlers
from app.core.http_cache import HttpCacheMiddleware
from app.core.http_security import BodySizeLimitMiddleware, SecurityHeadersMiddleware
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

    # Outermost first: headers on everything, gzip on every body, the cache and the
    # limit inside CORS (a 304 or 413 still has the CORS headers).
    assert classes == [
        RequestContextMiddleware,
        SecurityHeadersMiddleware,
        GZipMiddleware,
        CORSMiddleware,
        HttpCacheMiddleware,
        BodySizeLimitMiddleware,
    ]
