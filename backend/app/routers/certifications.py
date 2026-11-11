from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status

from app.core.database import SessionDep
from app.core.errors import error_responses
from app.core.pagination import Page, PageParamsDep, SearchQuery
from app.dependencies import AuditContextDep, get_current_user
from app.schemas.certification import CertificationCreate, CertificationRead, CertificationUpdate
from app.services import certifications as certifications_service

router = APIRouter(
    prefix="/certifications", tags=["certifications"], responses=error_responses(422, 503)
)
admin_router = APIRouter(
    prefix="/admin/certifications",
    tags=["certifications"],
    dependencies=[Depends(get_current_user)],
    responses=error_responses(401, 422, 503),
)

CertificationId = Annotated[int, Path(ge=1)]


@router.get("")
async def list_certifications(
    session: SessionDep, page: PageParamsDep, q: SearchQuery = None
) -> Page[CertificationRead]:
    """Certifications, newest first. Expired ones are listed with `is_expired: true`.
    `q` searches the name and issuing organization."""
    return await certifications_service.list_certifications(session, q=q, page=page)


@admin_router.post("", status_code=status.HTTP_201_CREATED)
async def create_certification(
    body: CertificationCreate, context: AuditContextDep, session: SessionDep
) -> CertificationRead:
    """Add a certification; an expiry before the issue date is a 422."""
    return await certifications_service.create_certification(session, context, body)


@admin_router.get("/{certification_id}", responses=error_responses(404))
async def get_certification(
    certification_id: CertificationId, session: SessionDep
) -> CertificationRead:
    return await certifications_service.get_certification(session, certification_id)


@admin_router.patch("/{certification_id}", responses=error_responses(404))
async def update_certification(
    certification_id: CertificationId,
    body: CertificationUpdate,
    context: AuditContextDep,
    session: SessionDep,
) -> CertificationRead:
    """Change only the fields sent; the dates are checked against the stored ones."""
    return await certifications_service.update_certification(
        session, context, certification_id, body
    )


@admin_router.delete(
    "/{certification_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404)
)
async def delete_certification(
    certification_id: CertificationId, context: AuditContextDep, session: SessionDep
) -> Response:
    await certifications_service.delete_certification(session, context, certification_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
