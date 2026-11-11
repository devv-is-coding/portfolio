from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from pydantic import JsonValue

from app.core.database import SessionDep
from app.core.errors import error_responses
from app.core.pagination import Page, PageParamsDep, SearchQuery, Sort, sort_query
from app.dependencies import AuditContextDep, get_current_user
from app.schemas.site_setting import (
    KEY_MAX_LENGTH,
    KEY_PATTERN,
    SiteSettingRead,
    SiteSettingWrite,
)
from app.services import site_settings as settings_service

router = APIRouter(prefix="/settings", tags=["settings"], responses=error_responses(503))
admin_router = APIRouter(
    prefix="/admin/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_user)],
    responses=error_responses(401, 422, 503),
)

SettingKey = Annotated[
    str,
    Path(
        max_length=KEY_MAX_LENGTH,
        pattern=KEY_PATTERN,
        description="Dotted lowercase segments, e.g. `seo.default_title`.",
    ),
]
SettingSort = Annotated[Sort, Depends(sort_query("key", "updated_at", default="key"))]


@router.get("")
async def public_settings(session: SessionDep) -> dict[str, JsonValue]:
    """The public settings (keys under `site.` and `seo.`) as one object:
    `{"site.name": "…", "seo.default_title": "…"}`."""
    return await settings_service.public_settings(session)


@admin_router.get("")
async def list_settings(
    session: SessionDep, page: PageParamsDep, sort: SettingSort, q: SearchQuery = None
) -> Page[SiteSettingRead]:
    """Every setting, public or not. `q` searches the key."""
    return await settings_service.list_settings(session, q=q, sort=sort, page=page)


@admin_router.get("/{key}", responses=error_responses(404))
async def get_setting(key: SettingKey, session: SessionDep) -> SiteSettingRead:
    return await settings_service.get_setting(session, key)


@admin_router.put(
    "/{key}",
    responses={201: {"description": "Setting created"}, **error_responses(409)},
)
async def put_setting(
    key: SettingKey,
    body: SiteSettingWrite,
    response: Response,
    context: AuditContextDep,
    session: SessionDep,
) -> SiteSettingRead:
    """Create (201) or replace (200) the setting. Keys that look like secrets
    (`password`, `token`, `api_key`, …) are a 422: secrets belong in environment
    variables."""
    setting, created = await settings_service.put_setting(session, context, key, body)
    if created:
        response.status_code = status.HTTP_201_CREATED
    return setting


@admin_router.delete(
    "/{key}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404)
)
async def delete_setting(
    key: SettingKey, context: AuditContextDep, session: SessionDep
) -> Response:
    await settings_service.delete_setting(session, context, key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
