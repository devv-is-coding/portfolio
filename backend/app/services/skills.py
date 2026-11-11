"""Skills shown on the portfolio, with optional icons from the media library."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationFailedError
from app.core.pagination import Page, PageParams, Sort
from app.core.slugs import slugify
from app.models import Skill
from app.models.enums import MediaKind
from app.repositories.skills import SkillRepository
from app.schemas.errors import ErrorDetail
from app.schemas.skill import SLUG_MAX_LENGTH, SkillCreate, SkillRead, SkillUpdate
from app.services import audit
from app.services.audit import AuditContext
from app.services.media import require_media, to_public

ENTITY_TYPE = "skill"


class SkillNotFoundError(NotFoundError):
    default_message = "Skill not found"


def to_read(skill: Skill, url_endpoint: str | None) -> SkillRead:
    return SkillRead(
        id=skill.id,
        name=skill.name,
        slug=skill.slug,
        category=skill.category,
        icon_media_id=skill.icon_media_id,
        icon=to_public(skill.icon, url_endpoint),
        display_order=skill.display_order,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
    )


async def list_skills(
    session: AsyncSession,
    url_endpoint: str | None,
    *,
    category: str | None,
    q: str | None,
    sort: Sort,
    page: PageParams,
) -> Page[SkillRead]:
    items, total = await SkillRepository(session).search(
        category=category, q=q, sort=sort, page=page
    )
    return Page.create([to_read(skill, url_endpoint) for skill in items], total, page)


async def _load(session: AsyncSession, skill_id: int) -> Skill:
    skill = await SkillRepository(session).get_with_icon(skill_id)
    if skill is None:
        raise SkillNotFoundError
    return skill


async def get_skill(session: AsyncSession, url_endpoint: str | None, skill_id: int) -> SkillRead:
    return to_read(await _load(session, skill_id), url_endpoint)


def _slug_from_name(name: str) -> str:
    slug = slugify(name, SLUG_MAX_LENGTH)
    if not slug:
        raise ValidationFailedError(
            details=[
                ErrorDetail(
                    field="body.slug",
                    message="Can't make a slug from this name; send one explicitly",
                    type="invalid_slug",
                )
            ]
        )
    return slug


async def create_skill(
    session: AsyncSession, url_endpoint: str | None, context: AuditContext, body: SkillCreate
) -> SkillRead:
    """Duplicate names or slugs fail on the unique indexes and come back as 409."""
    if body.icon_media_id is not None:
        await require_media(session, body.icon_media_id, MediaKind.IMAGE, "icon_media_id")
    repo = SkillRepository(session)
    skill = Skill(**body.model_dump(exclude={"slug"}), slug=body.slug or _slug_from_name(body.name))
    repo.add(skill)
    await repo.flush()
    audit.record(
        session,
        context,
        "skill.create",
        entity_type=ENTITY_TYPE,
        entity_id=skill.id,
        details={"name": skill.name, "slug": skill.slug},
    )
    await session.commit()
    return to_read(await _load(session, skill.id), url_endpoint)


async def update_skill(
    session: AsyncSession,
    url_endpoint: str | None,
    context: AuditContext,
    skill_id: int,
    body: SkillUpdate,
) -> SkillRead:
    values = body.model_dump(exclude_unset=True)
    if values.get("icon_media_id") is not None:
        await require_media(session, values["icon_media_id"], MediaKind.IMAGE, "icon_media_id")
    skill = await _load(session, skill_id)
    diff = audit.apply_changes(skill, values)
    if diff:
        audit.record(
            session,
            context,
            "skill.update",
            entity_type=ENTITY_TYPE,
            entity_id=skill.id,
            details=diff,
        )
        await session.commit()
        skill = await _load(session, skill_id)
    return to_read(skill, url_endpoint)


async def delete_skill(session: AsyncSession, context: AuditContext, skill_id: int) -> None:
    """Also removes the skill from every project (project_skills cascade)."""
    repo = SkillRepository(session)
    skill = await _load(session, skill_id)
    details = {"name": skill.name, "slug": skill.slug}
    await repo.delete(skill)
    audit.record(
        session,
        context,
        "skill.delete",
        entity_type=ENTITY_TYPE,
        entity_id=skill_id,
        details=details,
    )
    await session.commit()
