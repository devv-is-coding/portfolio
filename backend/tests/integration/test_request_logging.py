import logging

import pytest
from httpx import AsyncClient

from app.core.logging import REQUEST_ID_HEADER
from app.models import User
from tests.fakes import field
from tests.integration.factories import ADMIN_EMAIL, ADMIN_PASSWORD

pytestmark = pytest.mark.anyio


async def test_access_log_records_the_authenticated_user(
    api: AsyncClient, admin: User, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    login = await api.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    token = login.json()["access_token"]

    me = await api.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    access = [
        r for r in caplog.records if r.name == "app.access" and field(r, "path") == "/auth/me"
    ]
    assert [field(r, "user_id") for r in access] == [admin.id]
    assert field(access[0], "request_id") == me.headers[REQUEST_ID_HEADER]


async def test_passwords_and_tokens_never_reach_the_logs(
    api: AsyncClient, admin: User, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)

    await api.post("/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong password"})
    tokens = (
        await api.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    ).json()
    await api.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    await api.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    await api.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})

    for secret in (
        ADMIN_PASSWORD,
        "wrong password",
        tokens["access_token"],
        tokens["refresh_token"],
    ):
        assert secret not in caplog.text
