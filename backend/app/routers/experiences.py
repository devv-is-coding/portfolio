from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status

from app.core.database import SessionDep
from app.core.errors import error_responses
from app.core.pagination import Page, PageParamsDep, SearchQuery
from app.dependencies import AuditContextDep, get_current_user
from app.schemas.experience import ExperienceCreate, ExperienceRead, ExperienceUpdate
from app.services import experiences as experiences_service

router = APIRouter(prefix="/experiences", tags=["experience"], responses=error_responses(422, 503))
admin_router = APIRouter(
    prefix="/admin/experiences",
    tags=["experience"],
    dependencies=[Depends(get_current_user)],
    responses=error_responses(401, 422, 503),
)

ExperienceId = Annotated[int, Path(ge=1)]


@router.get("")
async def list_experiences(
    session: SessionDep, page: PageParamsDep, q: SearchQuery = None
) -> Page[ExperienceRead]:
    """The work timeline: current jobs first, then by start date, newest first.
    `q` searches the company and position."""
    return await experiences_service.list_experiences(session, q=q, page=page)


@admin_router.post("", status_code=status.HTTP_201_CREATED)
async def create_experience(
    body: ExperienceCreate, context: AuditContextDep, session: SessionDep
) -> ExperienceRead:
    """Add a job. No `end_date` means it is the current one; an end date before the
    start date is a 422."""
    return await experiences_service.create_experience(session, context, body)


@admin_router.get("/{experience_id}", responses=error_responses(404))
async def get_experience(experience_id: ExperienceId, session: SessionDep) -> ExperienceRead:
    """One job, for editing."""
    return await experiences_service.get_experience(session, experience_id)


@admin_router.patch("/{experience_id}", responses=error_responses(404))
async def update_experience(
    experience_id: ExperienceId,
    body: ExperienceUpdate,
    context: AuditContextDep,
    session: SessionDep,
) -> ExperienceRead:
    """Change only the fields sent; the dates are checked against the stored ones."""
    return await experiences_service.update_experience(session, context, experience_id, body)


@admin_router.delete(
    "/{experience_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404)
)
async def delete_experience(
    experience_id: ExperienceId, context: AuditContextDep, session: SessionDep
) -> Response:
    """Remove the job from the timeline."""
    await experiences_service.delete_experience(session, context, experience_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
