"""Portfolio projects: public reads (published only), admin CRUD, gallery and skills."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import Page, PageParams, Sort
from app.core.slugs import slug_or_explicit
from app.models import Project, ProjectImage
from app.models.enums import MediaKind, PublicationStatus
from app.repositories.project_images import ProjectImageRepository
from app.repositories.projects import ProjectRepository
from app.repositories.skills import SkillRepository
from app.schemas.project import (
    SLUG_MAX_LENGTH,
    ProjectAdminRead,
    ProjectCreate,
    ProjectDetail,
    ProjectImageCreate,
    ProjectImageRead,
    ProjectImageUpdate,
    ProjectSkillsUpdate,
    ProjectSummary,
    ProjectUpdate,
    SkillSummary,
)
from app.services import crud
from app.services.audit import AuditContext
from app.services.media import require_media, to_public
from app.services.publishing import publication_values, resolve_published_at

ENTITY_TYPE = "project"
IMAGE_ENTITY_TYPE = "project_image"


class ProjectNotFoundError(NotFoundError):
    default_message = "Project not found"


class ProjectImageNotFoundError(NotFoundError):
    default_message = "Project image not found"


# --- reads -----------------------------------------------------------------------------


def _summary_fields(project: Project, url_endpoint: str | None) -> dict[str, object]:
    return {
        "id": project.id,
        "title": project.title,
        "slug": project.slug,
        "short_description": project.short_description,
        "thumbnail": to_public(project.thumbnail, url_endpoint),
        "live_url": project.live_url,
        "repository_url": project.repository_url,
        "is_featured": project.is_featured,
        "display_order": project.display_order,
        "published_at": project.published_at,
        "skills": [SkillSummary.model_validate(skill) for skill in project.skills],
    }


def _image_read(image: ProjectImage, url_endpoint: str | None) -> ProjectImageRead:
    media = to_public(image.media, url_endpoint)
    if media is None:  # can't happen: project_images.media_id is NOT NULL
        raise ValueError(f"project image {image.id} has no media")
    return ProjectImageRead(
        id=image.id,
        media_id=image.media_id,
        image=media.model_copy(update={"alt_text": image.alt_text or media.alt_text}),
        display_order=image.display_order,
    )


def _detail_fields(project: Project, url_endpoint: str | None) -> dict[str, object]:
    return _summary_fields(project, url_endpoint) | {
        "description": project.description,
        "images": [_image_read(image, url_endpoint) for image in project.images],
        "updated_at": project.updated_at,
    }


def to_admin_read(project: Project, url_endpoint: str | None) -> ProjectAdminRead:
    return ProjectAdminRead.model_validate(
        _detail_fields(project, url_endpoint)
        | {
            "status": project.status,
            "thumbnail_media_id": project.thumbnail_media_id,
            "created_at": project.created_at,
        }
    )


async def list_published(
    session: AsyncSession,
    url_endpoint: str | None,
    *,
    featured: bool | None,
    skill_slug: str | None,
    q: str | None,
    sort: Sort,
    page: PageParams,
) -> Page[ProjectSummary]:
    items, total = await ProjectRepository(session).search(
        published_only=True, featured=featured, skill_slug=skill_slug, q=q, sort=sort, page=page
    )
    summaries = [ProjectSummary.model_validate(_summary_fields(p, url_endpoint)) for p in items]
    return Page.create(summaries, total, page)


async def get_published(
    session: AsyncSession, url_endpoint: str | None, slug: str
) -> ProjectDetail:
    """Drafts and archived projects are a 404, exactly like missing ones."""
    project = await ProjectRepository(session).get_published_by_slug(slug)
    if project is None:
        raise ProjectNotFoundError
    return ProjectDetail.model_validate(_detail_fields(project, url_endpoint))


async def list_all(
    session: AsyncSession,
    url_endpoint: str | None,
    *,
    status: PublicationStatus | None,
    q: str | None,
    sort: Sort,
    page: PageParams,
) -> Page[ProjectAdminRead]:
    items, total = await ProjectRepository(session).search(
        published_only=False, status=status, q=q, sort=sort, page=page
    )
    return Page.create([to_admin_read(p, url_endpoint) for p in items], total, page)


async def _load(session: AsyncSession, project_id: int) -> Project:
    project = await ProjectRepository(session).get_with_details(project_id)
    if project is None:
        raise ProjectNotFoundError
    return project


async def get(session: AsyncSession, url_endpoint: str | None, project_id: int) -> ProjectAdminRead:
    return to_admin_read(await _load(session, project_id), url_endpoint)


# --- writes ----------------------------------------------------------------------------


async def create(
    session: AsyncSession, url_endpoint: str | None, context: AuditContext, body: ProjectCreate
) -> ProjectAdminRead:
    if body.thumbnail_media_id is not None:
        await require_media(session, body.thumbnail_media_id, MediaKind.IMAGE, "thumbnail_media_id")
    values = body.model_dump(mode="json", exclude={"slug", "status", "published_at"})
    project = Project(
        **values,
        slug=slug_or_explicit(body.slug, body.title, SLUG_MAX_LENGTH),
        status=body.status,
        published_at=resolve_published_at(
            body.status, body.published_at, sent="published_at" in body.model_fields_set
        ),
    )
    await crud.create(
        session,
        context,
        project,
        entity_type=ENTITY_TYPE,
        details={"title": project.title, "slug": project.slug, "status": project.status.value},
    )
    return to_admin_read(await _load(session, project.id), url_endpoint)


async def update(
    session: AsyncSession,
    url_endpoint: str | None,
    context: AuditContext,
    project_id: int,
    body: ProjectUpdate,
) -> ProjectAdminRead:
    if body.thumbnail_media_id is not None:
        await require_media(session, body.thumbnail_media_id, MediaKind.IMAGE, "thumbnail_media_id")
    project = await _load(session, project_id)
    # URLs as strings (JSON mode); status and published_at keep their types.
    values = body.model_dump(mode="json", exclude_unset=True, exclude={"status", "published_at"})
    values |= publication_values(project, body.status, body.published_at, body.model_fields_set)
    if await crud.update(session, context, project, values, entity_type=ENTITY_TYPE):
        project = await _load(session, project_id)
    return to_admin_read(project, url_endpoint)


async def delete(session: AsyncSession, context: AuditContext, project_id: int) -> None:
    """Gallery images and skill links go with it (database cascade)."""
    project = await _load(session, project_id)
    await crud.delete(
        session,
        context,
        project,
        entity_type=ENTITY_TYPE,
        details={"title": project.title, "slug": project.slug},
    )


async def replace_skills(
    session: AsyncSession,
    url_endpoint: str | None,
    context: AuditContext,
    project_id: int,
    body: ProjectSkillsUpdate,
) -> ProjectAdminRead:
    """Set the project's skills to exactly these ids (duplicates ignored)."""
    requested = list(dict.fromkeys(body.skill_ids))
    skills = await SkillRepository(session).get_many(requested)
    crud.require_all_found(requested, skills, field="skill_ids")
    project = await _load(session, project_id)
    changed = await crud.replace_links(
        session,
        context,
        project,
        project.skills,
        skills,
        action=f"{ENTITY_TYPE}.skills_update",
        entity_type=ENTITY_TYPE,
        field="skill_ids",
    )
    if changed:
        project = await _load(session, project_id)
    return to_admin_read(project, url_endpoint)


# --- gallery ---------------------------------------------------------------------------


async def add_image(
    session: AsyncSession,
    url_endpoint: str | None,
    context: AuditContext,
    project_id: int,
    body: ProjectImageCreate,
) -> ProjectImageRead:
    await _load(session, project_id)
    await require_media(session, body.media_id, MediaKind.IMAGE, "media_id")
    image = ProjectImage(project_id=project_id, **body.model_dump())
    await crud.create(
        session,
        context,
        image,
        entity_type=IMAGE_ENTITY_TYPE,
        details={"project_id": project_id, "media_id": body.media_id},
    )
    return await _image(session, url_endpoint, project_id, image.id)


async def _get_image(session: AsyncSession, project_id: int, image_id: int) -> ProjectImage:
    image = await ProjectImageRepository(session).get_for_project(project_id, image_id)
    if image is None:
        raise ProjectImageNotFoundError
    return image


async def _image(
    session: AsyncSession, url_endpoint: str | None, project_id: int, image_id: int
) -> ProjectImageRead:
    return _image_read(await _get_image(session, project_id, image_id), url_endpoint)


async def update_image(
    session: AsyncSession,
    url_endpoint: str | None,
    context: AuditContext,
    project_id: int,
    image_id: int,
    body: ProjectImageUpdate,
) -> ProjectImageRead:
    image = await _get_image(session, project_id, image_id)
    values = body.model_dump(exclude_unset=True)
    await crud.update(session, context, image, values, entity_type=IMAGE_ENTITY_TYPE)
    return await _image(session, url_endpoint, project_id, image_id)


async def delete_image(
    session: AsyncSession, context: AuditContext, project_id: int, image_id: int
) -> None:
    """Removes the image from the gallery; the media file itself stays in the library."""
    image = await _get_image(session, project_id, image_id)
    await crud.delete(
        session,
        context,
        image,
        entity_type=IMAGE_ENTITY_TYPE,
        details={"project_id": project_id, "media_id": image.media_id},
    )
