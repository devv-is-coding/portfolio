"""Site settings: JSON values under dotted keys. Only keys under the public prefixes are
shown to visitors; secrets never belong here (they live in environment variables)."""

import re

from pydantic import JsonValue
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationFailedError
from app.core.pagination import Page, PageParams, Sort
from app.models import SiteSetting
from app.repositories.site_settings import SiteSettingRepository
from app.schemas.errors import ErrorDetail
from app.schemas.site_setting import SiteSettingRead, SiteSettingWrite
from app.services import crud
from app.services.audit import AuditContext

ENTITY_TYPE = "site_setting"
PUBLIC_PREFIXES = ("site.", "seo.")
# A key containing one of these words looks like a secret and is refused.
SECRET_WORDS = frozenset(
    {"password", "passwd", "secret", "secrets", "token", "tokens", "credential", "credentials"}
)
_WORD_SEPARATORS = re.compile(r"[._]")


class SiteSettingNotFoundError(NotFoundError):
    default_message = "Setting not found"


def is_public(key: str) -> bool:
    return key.startswith(PUBLIC_PREFIXES)


def _refuse_secret_keys(key: str) -> None:
    words = set(_WORD_SEPARATORS.split(key))
    if words & SECRET_WORDS or "private_key" in key or "api_key" in key:
        raise ValidationFailedError(
            details=[
                ErrorDetail(
                    field="path.key",
                    message="Looks like a secret; secrets belong in environment variables",
                    type="secret_key",
                )
            ]
        )


def to_read(setting: SiteSetting) -> SiteSettingRead:
    return SiteSettingRead(
        key=setting.setting_key,
        value=setting.setting_value,
        is_public=is_public(setting.setting_key),
        created_at=setting.created_at,
        updated_at=setting.updated_at,
    )


async def public_settings(session: AsyncSession) -> dict[str, JsonValue]:
    settings = await SiteSettingRepository(session).list_with_prefixes(PUBLIC_PREFIXES)
    return {setting.setting_key: setting.setting_value for setting in settings}


async def list_settings(
    session: AsyncSession, *, q: str | None, sort: Sort, page: PageParams
) -> Page[SiteSettingRead]:
    items, total = await SiteSettingRepository(session).search(q=q, sort=sort, page=page)
    return Page.create([to_read(item) for item in items], total, page)


async def _load(session: AsyncSession, key: str) -> SiteSetting:
    setting = await SiteSettingRepository(session).get_by_key(key)
    if setting is None:
        raise SiteSettingNotFoundError
    return setting


async def get_setting(session: AsyncSession, key: str) -> SiteSettingRead:
    return to_read(await _load(session, key))


async def put_setting(
    session: AsyncSession, context: AuditContext, key: str, body: SiteSettingWrite
) -> tuple[SiteSettingRead, bool]:
    """Create or replace the setting; also returns whether it was created."""
    _refuse_secret_keys(key)
    repository = SiteSettingRepository(session)
    setting = await repository.get_by_key(key)
    if setting is None:
        setting = SiteSetting(setting_key=key, setting_value=body.value)
        await crud.create(session, context, setting, entity_type=ENTITY_TYPE, details={"key": key})
        await repository.refresh(setting)
        return to_read(setting), True
    values = {"setting_value": body.value}
    if await crud.update(session, context, setting, values, entity_type=ENTITY_TYPE):
        await repository.refresh(setting)
    return to_read(setting), False


async def delete_setting(session: AsyncSession, context: AuditContext, key: str) -> None:
    setting = await _load(session, key)
    await crud.delete(session, context, setting, entity_type=ENTITY_TYPE, details={"key": key})
