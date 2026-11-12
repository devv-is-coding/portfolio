from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.core.database import SessionDep
from app.core.errors import error_responses
from app.core.imagekit import MediaUrlEndpointDep
from app.core.pagination import Page, PageParamsDep, SearchQuery, Sort, sort_query
from app.core.slugs import Slug
from app.dependencies import AuditContextDep, get_current_user
from app.models.enums import PublicationStatus
from app.schemas.project import (
    ProjectAdminRead,
    ProjectCreate,
    ProjectDetail,
    ProjectImageCreate,
    ProjectImageRead,
    ProjectImageUpdate,
    ProjectSkillsUpdate,
    ProjectSummary,
    ProjectUpdate,
)
from app.services import projects as projects_service

router = APIRouter(prefix="/projects", tags=["projects"], responses=error_responses(422, 503))
admin_router = APIRouter(
    prefix="/admin/projects",
    tags=["projects"],
    dependencies=[Depends(get_current_user)],
    responses=error_responses(401, 422, 503),
)

ProjectId = Annotated[int, Path(ge=1)]
ImageId = Annotated[int, Path(ge=1)]
PublicSort = Annotated[
    Sort, Depends(sort_query("display_order", "published_at", "title", default="display_order"))
]
AdminSort = Annotated[
    Sort,
    Depends(
        sort_query("display_order", "published_at", "title", "created_at", default="-created_at")
    ),
]


@router.get("")
async def list_projects(
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
    page: PageParamsDep,
    sort: PublicSort,
    q: SearchQuery = None,
    featured: Annotated[bool | None, Query(description="Only featured (or not).")] = None,
    skill: Annotated[str | None, Query(max_length=120, description="A skill slug.")] = None,
) -> Page[ProjectSummary]:
    """Published projects. `q` searches the title and short description."""
    return await projects_service.list_published(
        session, url_endpoint, featured=featured, skill_slug=skill, q=q, sort=sort, page=page
    )


@router.get("/{slug}", responses=error_responses(404))
async def get_project(
    slug: Annotated[Slug, Path(max_length=220)],
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> ProjectDetail:
    """A published project with its gallery and skills. Drafts and archived ones are 404."""
    return await projects_service.get_published(session, url_endpoint, slug)


@admin_router.get("")
async def list_all_projects(
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
    page: PageParamsDep,
    sort: AdminSort,
    q: SearchQuery = None,
    project_status: Annotated[
        PublicationStatus | None, Query(alias="status", description="Only this status.")
    ] = None,
) -> Page[ProjectAdminRead]:
    """Every project, whatever its status, newest first by default."""
    return await projects_service.list_all(
        session, url_endpoint, status=project_status, q=q, sort=sort, page=page
    )


@admin_router.post("", status_code=status.HTTP_201_CREATED, responses=error_responses(409))
async def create_project(
    body: ProjectCreate,
    context: AuditContextDep,
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> ProjectAdminRead:
    """Create a project. The slug is made from the title when left out (409 if taken);
    publishing without `published_at` sets it to now."""
    return await projects_service.create(session, url_endpoint, context, body)


@admin_router.get("/{project_id}", responses=error_responses(404))
async def get_any_project(
    project_id: ProjectId, session: SessionDep, url_endpoint: MediaUrlEndpointDep
) -> ProjectAdminRead:
    """One project in any status, with gallery and skills, for editing."""
    return await projects_service.get(session, url_endpoint, project_id)


@admin_router.patch("/{project_id}", responses=error_responses(404, 409))
async def update_project(
    project_id: ProjectId,
    body: ProjectUpdate,
    context: AuditContextDep,
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> ProjectAdminRead:
    """Change only the fields sent. Publishing without `published_at` sets it to now;
    clearing it while published is a 422."""
    return await projects_service.update(session, url_endpoint, context, project_id, body)


@admin_router.delete(
    "/{project_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404)
)
async def delete_project(
    project_id: ProjectId, context: AuditContextDep, session: SessionDep
) -> Response:
    """Delete the project with its gallery and skill links (media files stay)."""
    await projects_service.delete(session, context, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_router.put("/{project_id}/skills", responses=error_responses(404))
async def replace_project_skills(
    project_id: ProjectId,
    body: ProjectSkillsUpdate,
    context: AuditContextDep,
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> ProjectAdminRead:
    """Set the project's skills to exactly this list; unknown ids are a 422."""
    return await projects_service.replace_skills(session, url_endpoint, context, project_id, body)


@admin_router.post(
    "/{project_id}/images", status_code=status.HTTP_201_CREATED, responses=error_responses(404)
)
async def add_project_image(
    project_id: ProjectId,
    body: ProjectImageCreate,
    context: AuditContextDep,
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> ProjectImageRead:
    """Add an image from the media library to the gallery."""
    return await projects_service.add_image(session, url_endpoint, context, project_id, body)


@admin_router.patch("/{project_id}/images/{image_id}", responses=error_responses(404))
async def update_project_image(
    project_id: ProjectId,
    image_id: ImageId,
    body: ProjectImageUpdate,
    context: AuditContextDep,
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> ProjectImageRead:
    """Change the alt text override or the position in the gallery."""
    return await projects_service.update_image(
        session, url_endpoint, context, project_id, image_id, body
    )


@admin_router.delete(
    "/{project_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(404),
)
async def delete_project_image(
    project_id: ProjectId, image_id: ImageId, context: AuditContextDep, session: SessionDep
) -> Response:
    """Remove the image from the gallery; the media file stays in the library."""
    await projects_service.delete_image(session, context, project_id, image_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
