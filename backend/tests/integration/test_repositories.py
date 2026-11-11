from datetime import timedelta

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utc_now
from app.models import Project, RefreshToken, User
from app.models.enums import PublicationStatus
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.users import UserRepository

pytestmark = pytest.mark.anyio


async def _user(session: AsyncSession, email: str) -> User:
    users = UserRepository(session)
    user = User(email=email, password_hash="hash")
    users.add(user)
    await users.flush()
    return user


async def _token(session: AsyncSession, user: User, token_hash: str) -> RefreshToken:
    tokens = RefreshTokenRepository(session)
    token = RefreshToken(
        user_id=user.id, token_hash=token_hash, expires_at=utc_now() + timedelta(days=1)
    )
    tokens.add(token)
    await tokens.flush()
    return token


async def test_get_by_email_ignores_case_and_returns_none_when_unknown(
    db_session: AsyncSession,
) -> None:
    user = await _user(db_session, "admin@example.com")
    users = UserRepository(db_session)

    assert await users.get_by_email("ADMIN@Example.com") is user
    assert await users.get_by_email("nobody@example.com") is None
    assert await users.get(user.id) is user


async def test_get_by_hash_for_update_finds_only_that_token(db_session: AsyncSession) -> None:
    user = await _user(db_session, "admin@example.com")
    token = await _token(db_session, user, "a" * 64)
    tokens = RefreshTokenRepository(db_session)

    assert await tokens.get_by_hash_for_update("a" * 64) is token
    assert await tokens.get_by_hash_for_update("b" * 64) is None


async def test_revoke_all_for_user_touches_only_that_users_live_tokens(
    db_session: AsyncSession,
) -> None:
    admin = await _user(db_session, "admin@example.com")
    other = await _user(db_session, "other@example.com")
    live = await _token(db_session, admin, "a" * 64)
    already_revoked = await _token(db_session, admin, "b" * 64)
    earlier = utc_now().replace(microsecond=0) - timedelta(days=1)
    already_revoked.revoked_at = earlier
    others = await _token(db_session, other, "c" * 64)
    await db_session.flush()

    now = utc_now().replace(microsecond=0)
    await RefreshTokenRepository(db_session).revoke_all_for_user(admin.id, now)
    for token in (live, already_revoked, others):
        await db_session.refresh(token)

    assert live.revoked_at == now
    assert already_revoked.revoked_at == earlier
    assert others.revoked_at is None


async def test_delete_removes_the_row(db_session: AsyncSession) -> None:
    user = await _user(db_session, "admin@example.com")
    users = UserRepository(db_session)

    await users.delete(user)
    await users.flush()

    assert await users.get_by_email("admin@example.com") is None


async def test_statuses_are_stored_as_codes_and_read_back_as_values(
    db_session: AsyncSession,
) -> None:
    project = Project(title="A", slug="a", status=PublicationStatus.ARCHIVED)
    db_session.add(project)
    await db_session.flush()

    raw = await db_session.scalar(
        text("SELECT status FROM projects WHERE id = :id"), {"id": project.id}
    )
    found = await db_session.scalar(
        select(Project)
        .where(Project.status == "archived")
        .execution_options(populate_existing=True)
    )

    assert raw == 2
    assert found is not None
    assert found.status is PublicationStatus.ARCHIVED
