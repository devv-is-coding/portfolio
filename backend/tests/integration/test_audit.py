from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import register_exception_handlers
from app.dependencies import AuditContextDep
from app.models import AuditLog, User
from app.services import audit
from app.services.audit import REDACTED, AuditContext
from app.services.auth import create_admin
from tests.integration.factories import ADMIN_EMAIL, ADMIN_PASSWORD

pytestmark = pytest.mark.anyio


async def _entries(session: AsyncSession, action: str) -> list[AuditLog]:
    rows = await session.scalars(select(AuditLog).where(AuditLog.action == action))
    return list(rows.all())


async def test_record_writes_the_entry_with_secrets_redacted(db_session: AsyncSession) -> None:
    audit.record(
        db_session,
        AuditContext(user_id=None, ip_address="203.0.113.7"),
        "project.update",
        entity_type="project",
        entity_id=42,
        details={"title": {"old": "A", "new": "B"}, "password": "hunter2"},
    )
    await db_session.commit()

    [entry] = await _entries(db_session, "project.update")
    assert (entry.entity_type, entry.entity_id, entry.ip_address) == ("project", 42, "203.0.113.7")
    assert entry.details == {"title": {"old": "A", "new": "B"}, "password": REDACTED}
    assert entry.created_at is not None


async def test_entry_is_rolled_back_with_the_change_it_describes(
    db_session: AsyncSession, admin: User
) -> None:

    audit.record(db_session, AuditContext(None, None), "user.create")
    db_session.add(User(email=ADMIN_EMAIL, password_hash="duplicate"))
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    assert await _entries(db_session, "user.create") == []


async def test_auth_events_are_audited_without_secrets(
    api: AsyncClient, db_session: AsyncSession, admin: User
) -> None:

    await api.post("/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong password"})
    await api.post("/auth/login", json={"email": "nobody@example.com", "password": ADMIN_PASSWORD})
    tokens = (
        await api.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    ).json()
    rotated = await api.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    await api.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})  # reuse
    await api.post("/auth/logout", json={"refresh_token": rotated.json()["refresh_token"]})

    [created] = await _entries(db_session, "auth.admin_created")
    assert (created.user_id, created.entity_type, created.entity_id) == (None, "user", admin.id)
    failures = await _entries(db_session, "auth.login_failed")
    assert [(f.user_id, f.details) for f in failures] == [
        (admin.id, {"email": ADMIN_EMAIL, "reason": "wrong_password"}),
        (None, {"email": "nobody@example.com", "reason": "unknown_email"}),
    ]
    [login] = await _entries(db_session, "auth.login")
    assert (login.user_id, login.ip_address) == (admin.id, "127.0.0.1")
    [reuse] = await _entries(db_session, "auth.refresh_reuse_detected")
    assert (reuse.user_id, reuse.entity_type) == (admin.id, "refresh_token")
    # The reuse revoked every session, so this logout had nothing live to revoke.
    assert await _entries(db_session, "auth.logout") == []
    every_entry = await db_session.scalars(select(AuditLog))
    for entry in every_entry:
        assert ADMIN_PASSWORD not in str(entry.details)
        assert tokens["refresh_token"] not in str(entry.details)


async def test_logout_of_a_live_session_is_audited(
    api: AsyncClient, db_session: AsyncSession, admin: User
) -> None:
    tokens = (
        await api.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    ).json()

    await api.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})

    [logout] = await _entries(db_session, "auth.logout")
    assert logout.user_id == admin.id


async def test_password_reset_is_audited(db_session: AsyncSession, admin: User) -> None:

    await create_admin(db_session, ADMIN_EMAIL, "a brand new password", reset_password=True)

    [reset] = await _entries(db_session, "auth.password_reset")
    assert reset.entity_id == admin.id


async def test_audit_context_dependency_gives_the_admin_and_ip(
    db_session: AsyncSession, admin: User, admin_headers: dict[str, str]
) -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/whoami")
    async def whoami(context: AuditContextDep) -> dict[str, object]:
        return {"user_id": context.user_id, "ip_address": context.ip_address}

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        anonymous = await client.get("/whoami")
        response = await client.get("/whoami", headers=admin_headers)

    assert anonymous.status_code == 401
    assert response.json() == {"user_id": admin.id, "ip_address": "127.0.0.1"}
