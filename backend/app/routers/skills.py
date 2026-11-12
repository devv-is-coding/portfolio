from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.core.database import SessionDep
from app.core.errors import error_responses
from app.core.imagekit import MediaUrlEndpointDep
from app.core.pagination import Page, PageParamsDep, SearchQuery, Sort, sort_query
from app.dependencies import AuditContextDep, get_current_user
from app.schemas.skill import SkillCreate, SkillRead, SkillUpdate
from app.services import skills as skills_service

router = APIRouter(prefix="/skills", tags=["skills"], responses=error_responses(422, 503))
admin_router = APIRouter(
    prefix="/admin/skills",
    tags=["skills"],
    dependencies=[Depends(get_current_user)],
    responses=error_responses(401, 422, 503),
)

SkillId = Annotated[int, Path(ge=1)]
SkillSort = Annotated[
    Sort, Depends(sort_query("display_order", "name", "created_at", default="display_order"))
]


@router.get("")
async def list_skills(
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
    page: PageParamsDep,
    sort: SkillSort,
    q: SearchQuery = None,
    category: Annotated[
        str | None, Query(max_length=100, description="Only this category.")
    ] = None,
) -> Page[SkillRead]:
    """Skills in display order, with icon URLs. `q` searches the name."""
    return await skills_service.list_skills(
        session, url_endpoint, category=category, q=q, sort=sort, page=page
    )


@admin_router.post("", status_code=status.HTTP_201_CREATED, responses=error_responses(409))
async def create_skill(
    body: SkillCreate,
    context: AuditContextDep,
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> SkillRead:
    """Add a skill. The slug is made from the name when left out; name and slug must be
    unique (409). The icon must be an image from the media library."""
    return await skills_service.create_skill(session, url_endpoint, context, body)


@admin_router.get("/{skill_id}", responses=error_responses(404))
async def get_skill(
    skill_id: SkillId, session: SessionDep, url_endpoint: MediaUrlEndpointDep
) -> SkillRead:
    """One skill with its icon, for editing."""
    return await skills_service.get_skill(session, url_endpoint, skill_id)


@admin_router.patch("/{skill_id}", responses=error_responses(404, 409))
async def update_skill(
    skill_id: SkillId,
    body: SkillUpdate,
    context: AuditContextDep,
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> SkillRead:
    """Change only the fields sent."""
    return await skills_service.update_skill(session, url_endpoint, context, skill_id, body)


@admin_router.delete(
    "/{skill_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404)
)
async def delete_skill(
    skill_id: SkillId, context: AuditContextDep, session: SessionDep
) -> Response:
    """Delete the skill; it disappears from every project that listed it."""
    await skills_service.delete_skill(session, context, skill_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
