"""ETags, 304s and Cache-Control (app/core/http_cache.py), and gzip on the real app."""

import pytest
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.testclient import TestClient

from app.core.errors import NotFoundError, register_exception_handlers
from app.core.http_cache import HttpCacheMiddleware, etag_for

BIG = "x" * 5000


def _client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    state = {"text": "first"}

    @app.get("/items")
    async def items() -> dict[str, str]:
        return state

    @app.post("/items")
    async def change(text: str) -> dict[str, str]:
        state["text"] = text
        return state

    @app.get("/big")
    async def big() -> dict[str, str]:
        return {"text": BIG}

    @app.get("/missing")
    async def missing() -> None:
        raise NotFoundError

    @app.get("/admin/items")
    async def admin_items() -> dict[str, str]:
        return state

    @app.post("/auth/login")
    async def login() -> dict[str, str]:
        return {"access_token": "secret"}

    app.add_middleware(HttpCacheMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)
    return TestClient(app)


def test_public_reads_get_a_weak_etag_and_must_revalidate() -> None:
    response = _client().get("/items")

    assert response.headers["ETag"] == etag_for(response.content)
    assert response.headers["ETag"].startswith('W/"')
    assert response.headers["Cache-Control"] == "public, no-cache"


def test_an_unchanged_response_is_a_304_without_a_body() -> None:
    client = _client()
    etag = client.get("/items").headers["ETag"]

    revalidated = client.get("/items", headers={"If-None-Match": etag})
    strong_form = client.get("/items", headers={"If-None-Match": etag.removeprefix("W/")})
    one_of_many = client.get("/items", headers={"If-None-Match": f'"other", {etag}'})

    for response in (revalidated, strong_form, one_of_many):
        assert (response.status_code, response.content) == (304, b"")
        assert response.headers["ETag"] == etag
        assert "content-length" not in response.headers or response.headers["content-length"] == "0"


def test_changed_content_gets_a_new_etag_and_the_full_body() -> None:
    client = _client()
    old_etag = client.get("/items").headers["ETag"]
    client.post("/items", params={"text": "second"})

    response = client.get("/items", headers={"If-None-Match": old_etag})

    assert (response.status_code, response.json()) == (200, {"text": "second"})
    assert response.headers["ETag"] != old_etag


@pytest.mark.parametrize(
    ("method", "path"),
    [("GET", "/admin/items"), ("POST", "/auth/login")],
)
def test_admin_and_auth_responses_are_never_stored(method: str, path: str) -> None:
    response = _client().request(method, path)

    assert response.headers["Cache-Control"] == "no-store"
    assert "ETag" not in response.headers


def test_errors_get_no_etag() -> None:
    response = _client().get("/missing")

    assert response.status_code == 404
    assert "ETag" not in response.headers


def test_large_bodies_are_gzipped_and_still_revalidate() -> None:
    client = _client()

    small = client.get("/items")
    big = client.get("/big")
    revalidated = client.get("/big", headers={"If-None-Match": big.headers["ETag"]})

    assert "content-encoding" not in small.headers
    assert big.headers["content-encoding"] == "gzip"
    assert big.json() == {"text": BIG}
    assert revalidated.status_code == 304
