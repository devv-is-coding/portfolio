from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.database import SessionDep
from app.core.errors import error_responses
from app.core.pagination import Page, PageParamsDep, Sort, sort_query
from app.dependencies import get_current_user
from app.schemas.audit_log import AuditLogRead
from app.schemas.fields import UtcDateTime
from app.services import audit

# Read-only on purpose: the audit trail has no create, update or delete endpoints.
admin_router = APIRouter(
    prefix="/admin/audit-logs",
    tags=["audit"],
    dependencies=[Depends(get_current_user)],
    responses=error_responses(401, 422, 503),
)

AuditSort = Annotated[Sort, Depends(sort_query("created_at", default="-created_at"))]


@admin_router.get("")
async def list_audit_logs(
    session: SessionDep,
    page: PageParamsDep,
    sort: AuditSort,
    user_id: Annotated[int | None, Query(ge=1, description="Only this admin's actions.")] = None,
    action: Annotated[
        str | None, Query(max_length=100, description="Exact action, e.g. `project.update`.")
    ] = None,
    entity_type: Annotated[str | None, Query(max_length=100, description="e.g. `project`.")] = None,
    entity_id: Annotated[
        int | None, Query(ge=1, description="With `entity_type`: one record's history.")
    ] = None,
    since: Annotated[
        UtcDateTime | None, Query(description="From this time on (inclusive, UTC if no offset).")
    ] = None,
    until: Annotated[UtcDateTime | None, Query(description="Before this time (exclusive).")] = None,
) -> Page[AuditLogRead]:
    """Who did what, newest first. Details show the changes, never secrets."""
    return await audit.list_entries(
        session,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        since=since,
        until=until,
        sort=sort,
        page=page,
    )
