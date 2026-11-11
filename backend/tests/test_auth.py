"""Auth endpoint behaviour that needs no database (full flows: tests/integration)."""

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.security import create_access_token
from tests.fakes import IsolatedSettings


def test_me_without_token_is_401_with_bearer_challenge(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {
        "error": {"code": "unauthorized", "message": "Not authenticated", "details": None}
    }


@pytest.mark.parametrize(
    "authorization",
    ["Bearer not-a-jwt", "Basic dXNlcjpwYXNz", "Bearer "],
)
def test_me_with_invalid_token_is_401(client: TestClient, authorization: str) -> None:
    response = client.get("/auth/me", headers={"Authorization": authorization})

    assert response.status_code == 401


def test_me_with_token_from_another_key_is_401(client: TestClient) -> None:
    other = IsolatedSettings(jwt_secret_key=SecretStr("another-secret-key-that-is-long-enough!"))
    token = create_access_token(1, other)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


@pytest.mark.parametrize(
    "body",
    [
        {"email": "not-an-email", "password": "x"},
        {"email": "admin@example.com", "password": ""},
        {"email": "admin@example.com", "password": "x" * 257},
        {"email": "admin@example.com"},
    ],
)
def test_login_rejects_invalid_bodies(client: TestClient, body: dict[str, str]) -> None:
    assert client.post("/auth/login", json=body).status_code == 422


def test_refresh_and_logout_require_a_token(client: TestClient) -> None:
    assert client.post("/auth/refresh", json={}).status_code == 422
    assert client.post("/auth/logout", json={"refresh_token": ""}).status_code == 422
