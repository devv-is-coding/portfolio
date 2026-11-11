from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status

from app.core.database import SessionDep
from app.core.errors import error_responses
from app.core.pagination import Page, PageParamsDep, SearchQuery
from app.dependencies import AuditContextDep, get_current_user
from app.schemas.education import EducationCreate, EducationRead, EducationUpdate
from app.services import education as education_service

router = APIRouter(prefix="/education", tags=["education"], responses=error_responses(422, 503))
admin_router = APIRouter(
    prefix="/admin/education",
    tags=["education"],
    dependencies=[Depends(get_current_user)],
    responses=error_responses(401, 422, 503),
)

EducationId = Annotated[int, Path(ge=1)]


@router.get("")
async def list_education(
    session: SessionDep, page: PageParamsDep, q: SearchQuery = None
) -> Page[EducationRead]:
    """Education, in progress first, then newest first. `q` searches the institution,
    degree and field of study."""
    return await education_service.list_education(session, q=q, page=page)


@admin_router.post("", status_code=status.HTTP_201_CREATED)
async def create_education(
    body: EducationCreate, context: AuditContextDep, session: SessionDep
) -> EducationRead:
    """Add an entry; an end date before the start date is a 422."""
    return await education_service.create_education(session, context, body)


@admin_router.get("/{education_id}", responses=error_responses(404))
async def get_education(education_id: EducationId, session: SessionDep) -> EducationRead:
    return await education_service.get_education(session, education_id)


@admin_router.patch("/{education_id}", responses=error_responses(404))
async def update_education(
    education_id: EducationId,
    body: EducationUpdate,
    context: AuditContextDep,
    session: SessionDep,
) -> EducationRead:
    """Change only the fields sent; the dates are checked against the stored ones."""
    return await education_service.update_education(session, context, education_id, body)


@admin_router.delete(
    "/{education_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404)
)
async def delete_education(
    education_id: EducationId, context: AuditContextDep, session: SessionDep
) -> Response:
    await education_service.delete_education(session, context, education_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
