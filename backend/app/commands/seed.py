"""Fill the database with realistic test data, for load tests and `EXPLAIN` checks.

    uv run python -m app.commands.seed           # add the seed data
    uv run python -m app.commands.seed --clear   # remove it again

Every seeded row is marked (slugs and file ids start with `seed-`, emails end with
`@seed.example.com`, audit actions are `seed.event`, ...), so `--clear` removes exactly
what was added and never touches real content. Refuses to run with
ENVIRONMENT=production, and refuses to seed twice.

The integration tests use the same database and expect it without seed data: run
`--clear` before `pytest`.
"""

import argparse
import asyncio
import random
from datetime import timedelta

from sqlalchemy import delete, func, insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.security import utc_now
from app.models import (
    AuditLog,
    BlogCategory,
    BlogPost,
    BlogTag,
    Certification,
    ContactMessage,
    Education,
    Experience,
    Media,
    Project,
    ProjectImage,
    SiteSetting,
    Skill,
)
from app.models.enums import ContactMessageStatus, PublicationStatus

PROJECTS = 100
IMAGES_PER_PROJECT = 3
SKILLS = 30
SKILLS_PER_PROJECT = 4
POSTS = 100
CATEGORIES = 8
TAGS = 20
TAGS_PER_POST = 3
EXPERIENCES = 15
EDUCATION = 5
CERTIFICATIONS = 20
CONTACT_MESSAGES = 1_000
AUDIT_ROWS = 10_000

SEED_EMAIL_DOMAIN = "@seed.example.com"
SEED_COMPANY = "Seed Company"
SEED_INSTITUTION = "Seed University"
SEED_ORGANIZATION = "Seed Organization"
SEED_ACTION = "seed.event"
SEED_SETTING_KEYS = ("site.seed_title", "seo.seed_description")

# About 3,000 characters of Markdown, like a real post.
POST_CONTENT = "\n\n".join(
    f"## Section {n}\n\nLorem ipsum dolor sit amet, consectetur adipiscing elit. " * 3
    for n in range(1, 9)
)


def _publication(index: int) -> PublicationStatus:
    """Mostly published (80%), some drafts and archived, as on a real site."""
    if index % 5:
        return PublicationStatus.PUBLISHED
    return PublicationStatus.DRAFT if index % 2 else PublicationStatus.ARCHIVED


def _media(name: str, mime_type: str = "image/webp") -> Media:
    return Media(
        file_id=f"seed-{name}",
        file_path=f"/seed/{name}.webp",
        mime_type=mime_type,
        size_bytes=150_000,
        width=1600,
        height=900,
        alt_text=f"Seed image {name}",
    )


async def _already_seeded(session: AsyncSession) -> bool:
    count = await session.scalar(
        select(func.count()).select_from(Media).where(Media.file_id.startswith("seed-"))
    )
    return bool(count)


async def seed(session: AsyncSession, rng: random.Random) -> None:
    now = utc_now()

    skills = [
        Skill(
            name=f"Seed skill {n}",
            slug=f"seed-skill-{n}",
            category=("backend", "frontend", "devops")[n % 3],
            icon=_media(f"icon-{n}", "image/svg+xml"),
            display_order=n,
        )
        for n in range(SKILLS)
    ]
    session.add_all(skills)

    for n in range(PROJECTS):
        status = _publication(n)
        project = Project(
            title=f"Seed project {n}",
            slug=f"seed-project-{n}",
            short_description=f"A seeded project about topic {n % 17}.",
            description=POST_CONTENT,
            thumbnail=_media(f"thumb-{n}"),
            live_url=f"https://example.com/seed/{n}",
            status=status,
            is_featured=n % 10 == 0,
            display_order=n,
            published_at=now - timedelta(days=n) if status is PublicationStatus.PUBLISHED else None,
        )
        project.images = [
            ProjectImage(media=_media(f"shot-{n}-{i}"), display_order=i)
            for i in range(IMAGES_PER_PROJECT)
        ]
        project.skills = rng.sample(skills, SKILLS_PER_PROJECT)
        session.add(project)

    categories = [
        BlogCategory(name=f"Seed category {n}", slug=f"seed-category-{n}")
        for n in range(CATEGORIES)
    ]
    tags = [BlogTag(name=f"Seed tag {n}", slug=f"seed-tag-{n}") for n in range(TAGS)]
    session.add_all([*categories, *tags])
    for n in range(POSTS):
        status = _publication(n)
        session.add(
            BlogPost(
                title=f"Seed post {n}",
                slug=f"seed-post-{n}",
                excerpt=f"What seeded post {n} is about.",
                content=POST_CONTENT,
                category=categories[n % CATEGORIES],
                cover=_media(f"cover-{n}"),
                tags=rng.sample(tags, TAGS_PER_POST),
                status=status,
                published_at=now - timedelta(days=n)
                if status is PublicationStatus.PUBLISHED
                else None,
            )
        )

    today = now.date()
    session.add_all(
        Experience(
            company=f"{SEED_COMPANY} {n}",
            position="Software engineer",
            description=POST_CONTENT[:800],
            start_date=today - timedelta(days=365 * (n + 1)),
            end_date=None if n == 0 else today - timedelta(days=365 * n),
            display_order=n,
        )
        for n in range(EXPERIENCES)
    )
    session.add_all(
        Education(
            institution=f"{SEED_INSTITUTION} {n}",
            degree="BSc",
            field_of_study="Computer science",
            start_date=today - timedelta(days=365 * (4 + n * 4)),
            end_date=today - timedelta(days=365 * n * 4),
        )
        for n in range(EDUCATION)
    )
    session.add_all(
        Certification(
            name=f"Seed certification {n}",
            issuing_organization=SEED_ORGANIZATION,
            credential_url=f"https://example.com/credential/{n}",
            issued_at=today - timedelta(days=90 * n),
            expires_at=today + timedelta(days=365 - 90 * n),
        )
        for n in range(CERTIFICATIONS)
    )
    session.add_all(
        SiteSetting(setting_key=key, setting_value=f"Seed value for {key}")
        for key in SEED_SETTING_KEYS
    )
    await session.flush()

    statuses = list(ContactMessageStatus)
    await session.execute(
        insert(ContactMessage),
        [
            {
                "name": f"Visitor {n}",
                "email": f"visitor{n}{SEED_EMAIL_DOMAIN}",
                "subject": f"Hello number {n}",
                "message": "I'd like to talk about a project. " * 10,
                "status": statuses[n % len(statuses)],
                "ip_address": f"203.0.113.{n % 250}",
                "created_at": now - timedelta(minutes=17 * n),
            }
            for n in range(CONTACT_MESSAGES)
        ],
    )
    await session.execute(
        insert(AuditLog),
        [
            {
                "action": SEED_ACTION,
                "entity_type": ("project", "blog_post", "skill", "media")[n % 4],
                "entity_id": n % 500,
                "details": {"title": {"old": f"Old {n}", "new": f"New {n}"}},
                "ip_address": "203.0.113.1",
                "created_at": now - timedelta(minutes=3 * n),
            }
            for n in range(AUDIT_ROWS)
        ],
    )
    await session.commit()


async def clear(session: AsyncSession) -> None:
    """Delete every seeded row. Links (gallery, skills, tags) go by the database's
    cascade rules; media last, once nothing references it."""
    await session.execute(delete(Project).where(Project.slug.startswith("seed-")))
    await session.execute(delete(BlogPost).where(BlogPost.slug.startswith("seed-")))
    await session.execute(delete(BlogCategory).where(BlogCategory.slug.startswith("seed-")))
    await session.execute(delete(BlogTag).where(BlogTag.slug.startswith("seed-")))
    await session.execute(delete(Skill).where(Skill.slug.startswith("seed-")))
    await session.execute(delete(Experience).where(Experience.company.startswith(SEED_COMPANY)))
    await session.execute(
        delete(Education).where(Education.institution.startswith(SEED_INSTITUTION))
    )
    await session.execute(
        delete(Certification).where(Certification.issuing_organization == SEED_ORGANIZATION)
    )
    await session.execute(
        delete(ContactMessage).where(ContactMessage.email.endswith(SEED_EMAIL_DOMAIN))
    )
    await session.execute(delete(AuditLog).where(AuditLog.action == SEED_ACTION))
    await session.execute(
        delete(SiteSetting).where(
            or_(*(SiteSetting.setting_key == key for key in SEED_SETTING_KEYS))
        )
    )
    await session.execute(delete(Media).where(Media.file_id.startswith("seed-")))
    await session.commit()


async def _run(*, clear_only: bool) -> str:
    try:
        async with SessionLocal() as session:
            if clear_only:
                await clear(session)
                return "Seed data removed."
            if await _already_seeded(session):
                raise SystemExit("Already seeded. Run with --clear first.")
            await seed(session, random.Random(42))
            return "Seed data added."
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Add or remove realistic test data.")
    parser.add_argument("--clear", action="store_true", help="remove the seed data")
    args = parser.parse_args(argv)
    if get_settings().environment == "production":
        raise SystemExit("Refusing to seed a production database.")
    print(asyncio.run(_run(clear_only=args.clear)))


if __name__ == "__main__":
    main()
