"""Every public read uses a fixed number of SQL queries, however many rows it returns.

A relation loaded per row (N+1) shows up here as a count that grows with the data.
The budgets are the current counts: lower them when a query goes away, never raise
one without a reason.
"""

from collections.abc import Awaitable, Callable
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.imagekit import get_media_url_endpoint
from app.core.security import utc_now
from app.main import app
from app.models import (
    BlogCategory,
    BlogPost,
    BlogTag,
    Certification,
    Education,
    Experience,
    Media,
    Profile,
    Project,
    ProjectImage,
    SiteSetting,
    Skill,
    SocialLink,
)
from app.models.enums import PublicationStatus

pytestmark = pytest.mark.anyio

type Builder = Callable[[AsyncSession, range], Awaitable[None]]


def _media(name: str) -> Media:
    return Media(
        file_id=f"budget-{name}",
        file_path=f"/budget/{name}.webp",
        mime_type="image/webp",
        size_bytes=1,
        width=1,
        height=1,
    )


async def _projects(session: AsyncSession, numbers: range) -> None:
    skills = [Skill(name=f"Budget {n}", slug=f"budget-skill-{n}") for n in numbers]
    for n in numbers:
        project = Project(
            title=f"Budget {n}",
            slug=f"budget-{n}",
            thumbnail=_media(f"thumb-{n}"),
            status=PublicationStatus.PUBLISHED,
            published_at=utc_now(),
        )
        project.images = [ProjectImage(media=_media(f"shot-{n}-{i}")) for i in range(3)]
        project.skills = skills
        session.add(project)
    await session.flush()


async def _posts(session: AsyncSession, numbers: range) -> None:
    for n in numbers:
        session.add(
            BlogPost(
                title=f"Budget {n}",
                slug=f"budget-{n}",
                content="# Text",
                cover=_media(f"cover-{n}"),
                category=BlogCategory(name=f"Budget {n}", slug=f"budget-category-{n}"),
                tags=[
                    BlogTag(name=f"Budget {n}-{i}", slug=f"budget-tag-{n}-{i}") for i in range(2)
                ],
                status=PublicationStatus.PUBLISHED,
                published_at=utc_now(),
            )
        )
    await session.flush()


async def _skills(session: AsyncSession, numbers: range) -> None:
    session.add_all(
        Skill(name=f"Budget {n}", slug=f"budget-{n}", icon=_media(f"icon-{n}")) for n in numbers
    )
    await session.flush()


async def _experiences(session: AsyncSession, numbers: range) -> None:
    session.add_all(
        Experience(company=f"Budget {n}", position="Dev", start_date=date(2020, 1, 1))
        for n in numbers
    )
    await session.flush()


async def _education(session: AsyncSession, numbers: range) -> None:
    session.add_all(Education(institution=f"Budget {n}") for n in numbers)
    await session.flush()


async def _certifications(session: AsyncSession, numbers: range) -> None:
    session.add_all(
        Certification(name=f"Budget {n}", issuing_organization="Budget") for n in numbers
    )
    await session.flush()


async def _categories(session: AsyncSession, numbers: range) -> None:
    session.add_all(BlogCategory(name=f"Budget {n}", slug=f"budget-{n}") for n in numbers)
    await session.flush()


async def _tags(session: AsyncSession, numbers: range) -> None:
    session.add_all(BlogTag(name=f"Budget {n}", slug=f"budget-{n}") for n in numbers)
    await session.flush()


async def _settings(session: AsyncSession, numbers: range) -> None:
    session.add_all(SiteSetting(setting_key=f"site.budget_{n}", setting_value=n) for n in numbers)
    await session.flush()


async def _profile(session: AsyncSession, numbers: range) -> None:
    profile = await session.get(Profile, 1)
    if profile is None:
        profile = Profile(
            id=1, full_name="Budget", avatar=_media("avatar"), resume=_media("resume")
        )
        session.add(profile)
    session.add_all(
        SocialLink(profile=profile, platform=f"site-{n}", url=f"https://example.com/{n}")
        for n in numbers
    )
    await session.flush()


@pytest.mark.parametrize(
    ("path", "build", "budget"),
    [
        ("/projects", _projects, 2),
        ("/projects/budget-0", _projects, 3),
        ("/blog/posts", _posts, 2),
        ("/blog/posts/budget-0", _posts, 2),
        ("/skills", _skills, 1),
        ("/experiences", _experiences, 1),
        ("/education", _education, 1),
        ("/certifications", _certifications, 1),
        ("/blog/categories", _categories, 1),
        ("/blog/tags", _tags, 1),
        ("/settings", _settings, 1),
        ("/profile", _profile, 2),
    ],
)
async def test_public_reads_use_a_fixed_number_of_queries(
    api: AsyncClient,
    db_session: AsyncSession,
    sql_statements: list[str],
    path: str,
    build: Builder,
    budget: int,
) -> None:
    app.dependency_overrides[get_media_url_endpoint] = lambda: "https://ik.imagekit.io/test"

    await build(db_session, range(2))
    sql_statements.clear()
    few = await api.get(path)
    with_few = len(sql_statements)

    await build(db_session, range(2, 12))
    sql_statements.clear()
    many = await api.get(path)
    with_many = len(sql_statements)

    assert (few.status_code, many.status_code) == (200, 200)
    assert (with_few, with_many) == (budget, budget), sql_statements
