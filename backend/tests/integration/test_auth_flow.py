from datetime import timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_refresh_token, utc_now
from app.models import RefreshToken, User
from app.services.auth import UserExistsError, UserNotFoundError, create_admin
from tests.integration.factories import ADMIN_EMAIL, ADMIN_PASSWORD

pytestmark = pytest.mark.anyio


async def _login(
    api: AsyncClient, email: str = ADMIN_EMAIL, password: str = ADMIN_PASSWORD
) -> dict[str, Any]:
    response = await api.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


async def _live_tokens(db_session: AsyncSession, user: User) -> int:
    count = await db_session.scalar(
        select(func.count())
        .select_from(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
    )
    return count or 0


async def test_login_returns_tokens_and_me_returns_the_admin(
    api: AsyncClient, admin: User, db_session: AsyncSession
) -> None:
    tokens = await _login(api, email="ADMIN@example.com")  # emails match case-insensitively

    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] == get_settings().access_token_expire_minutes * 60
    me = await api.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == ADMIN_EMAIL
    assert me.json()["last_login_at"] is not None
    stored = await db_session.scalar(select(RefreshToken).where(RefreshToken.user_id == admin.id))
    assert stored is not None
    assert stored.token_hash == hash_refresh_token(tokens["refresh_token"])  # never plain


@pytest.mark.parametrize(
    ("email", "password"), [(ADMIN_EMAIL, "wrong password"), ("nobody@example.com", ADMIN_PASSWORD)]
)
async def test_login_failures_look_the_same(
    api: AsyncClient, admin: User, email: str, password: str
) -> None:
    response = await api.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "unauthorized", "message": "Incorrect email or password", "details": None}
    }


async def test_inactive_admin_cannot_log_in_or_use_tokens(
    api: AsyncClient, admin: User, db_session: AsyncSession
) -> None:
    tokens = await _login(api)
    admin.is_active = False
    await db_session.commit()

    login = await api.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    me = await api.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    refresh = await api.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert (login.status_code, me.status_code, refresh.status_code) == (401, 401, 401)


async def test_refresh_rotates_the_token(
    api: AsyncClient, admin: User, db_session: AsyncSession
) -> None:
    first = await _login(api)

    response = await api.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})

    assert response.status_code == 200
    second = response.json()
    assert second["refresh_token"] != first["refresh_token"]
    old = await db_session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(first["refresh_token"])
        )
    )
    assert old is not None
    assert old.revoked_at is not None
    assert old.replaced_by_id is not None
    me = await api.get("/auth/me", headers={"Authorization": f"Bearer {second['access_token']}"})
    assert me.status_code == 200


async def test_reusing_a_rotated_refresh_token_revokes_every_session(
    api: AsyncClient, admin: User, db_session: AsyncSession
) -> None:
    other_device = await _login(api)
    stolen = await _login(api)
    rotated = await api.post("/auth/refresh", json={"refresh_token": stolen["refresh_token"]})
    assert rotated.status_code == 200

    reuse = await api.post("/auth/refresh", json={"refresh_token": stolen["refresh_token"]})

    assert reuse.status_code == 401
    assert await _live_tokens(db_session, admin) == 0
    for token in (rotated.json()["refresh_token"], other_device["refresh_token"]):
        response = await api.post("/auth/refresh", json={"refresh_token": token})
        assert response.status_code == 401


async def test_expired_or_unknown_refresh_token_is_rejected(
    api: AsyncClient, admin: User, db_session: AsyncSession
) -> None:
    tokens = await _login(api)
    await db_session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == admin.id)
        .values(expires_at=utc_now() - timedelta(seconds=1))
    )
    await db_session.commit()

    expired = await api.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    unknown = await api.post("/auth/refresh", json={"refresh_token": "made-up-token"})

    assert expired.status_code == 401
    assert unknown.status_code == 401
    assert unknown.json() == {
        "error": {"code": "unauthorized", "message": "Invalid refresh token", "details": None}
    }


async def test_logout_revokes_the_refresh_token(
    api: AsyncClient, admin: User, db_session: AsyncSession
) -> None:
    tokens = await _login(api)

    first = await api.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    again = await api.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    refresh = await api.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert (first.status_code, again.status_code) == (204, 204)
    assert refresh.status_code == 401
    assert await _live_tokens(db_session, admin) == 0


async def test_too_many_failed_logins_are_rate_limited(api: AsyncClient, admin: User) -> None:
    wrong = {"email": ADMIN_EMAIL, "password": "wrong password"}
    for _ in range(get_settings().login_max_attempts):
        assert (await api.post("/auth/login", json=wrong)).status_code == 401

    blocked = await api.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})

    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


async def test_create_admin_refuses_duplicates_and_resets_passwords(
    api: AsyncClient, admin: User, db_session: AsyncSession
) -> None:
    tokens = await _login(api)

    with pytest.raises(UserExistsError):
        await create_admin(db_session, " Admin@Example.com ", "another password!")
    with pytest.raises(UserNotFoundError):
        await create_admin(db_session, "nobody@example.com", "x" * 12, reset_password=True)
    await create_admin(db_session, ADMIN_EMAIL, "a brand new password", reset_password=True)

    assert admin.email == ADMIN_EMAIL
    old_password = await api.post(
        "/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert old_password.status_code == 401
    assert (await _login(api, password="a brand new password"))["access_token"]
    old_session = await api.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert old_session.status_code == 401
