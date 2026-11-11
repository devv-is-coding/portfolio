"""The repository pagination helpers against MariaDB, using the users table."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PageParams, parse_sort
from app.models import User
from app.repositories.base import apply_sort, search_filter
from app.repositories.users import UserRepository

pytestmark = pytest.mark.anyio

DOMAIN = "@pagination.test"
SORTABLE = {"email": User.email, "created_at": User.created_at}


async def _users(session: AsyncSession, *local_parts: str) -> None:
    users = UserRepository(session)
    for local_part in local_parts:
        users.add(User(email=f"{local_part}{DOMAIN}", password_hash="hash"))
    await users.flush()


async def test_paginate_returns_the_page_and_the_total(db_session: AsyncSession) -> None:
    await _users(db_session, *(f"user{i:02d}" for i in range(25)))
    statement = apply_sort(
        select(User).where(User.email.endswith(DOMAIN)),
        parse_sort("email", SORTABLE),
        SORTABLE,
        User.id,
    )

    items, total = await UserRepository(db_session).paginate(statement, PageParams(page=3, size=10))

    assert total == 25
    assert [user.email for user in items] == [f"user{i:02d}{DOMAIN}" for i in range(20, 25)]


async def test_page_past_the_end_is_empty_with_the_total(db_session: AsyncSession) -> None:
    await _users(db_session, "only")

    items, total = await UserRepository(db_session).paginate(
        select(User).where(User.email.endswith(DOMAIN)), PageParams(page=5, size=10)
    )

    assert (items, total) == ([], 1)


async def test_descending_sort_with_id_tiebreaker(db_session: AsyncSession) -> None:
    await _users(db_session, "b", "a", "c")
    statement = apply_sort(
        select(User).where(User.email.endswith(DOMAIN)),
        parse_sort("-created_at", SORTABLE),  # all equal: the id decides, newest first
        SORTABLE,
        User.id,
    )

    items, _ = await UserRepository(db_session).paginate(statement, PageParams())

    assert [user.email.split("@")[0] for user in items] == ["c", "a", "b"]


async def test_ascending_sort_breaks_ties_oldest_first(db_session: AsyncSession) -> None:
    await _users(db_session, "b", "a", "c")
    statement = apply_sort(
        select(User).where(User.email.endswith(DOMAIN)),
        parse_sort("created_at", SORTABLE),
        SORTABLE,
        User.id,
    )

    items, _ = await UserRepository(db_session).paginate(statement, PageParams())

    assert [user.email.split("@")[0] for user in items] == ["b", "a", "c"]


async def test_search_is_case_insensitive_and_escapes_wildcards(db_session: AsyncSession) -> None:
    await _users(db_session, "100%off", "100aoff", "under_score", "underXscore", "Admin")

    async def emails(term: str) -> list[str]:
        statement = select(User).where(
            User.email.endswith(DOMAIN), search_filter([User.email], term)
        )
        items, _ = await UserRepository(db_session).paginate(statement, PageParams())
        return sorted(user.email.split("@")[0] for user in items)

    assert await emails("100%") == ["100%off"]
    assert await emails("under_") == ["under_score"]
    assert await emails("admin") == ["Admin"]
