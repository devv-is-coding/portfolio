"""The create / update / delete steps every admin resource shares: write, audit
(`<entity_type>.create|update|delete`) and commit in one transaction."""

from collections.abc import Mapping, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ValidationFailedError
from app.models.base import IdMixin
from app.schemas.errors import ErrorDetail
from app.services import audit
from app.services.audit import AuditContext, AuditDetails


async def create(
    session: AsyncSession,
    context: AuditContext,
    instance: IdMixin,
    *,
    entity_type: str,
    details: AuditDetails | None = None,
) -> None:
    """Insert `instance`, audit it and commit. Unique conflicts surface as 409."""
    session.add(instance)
    await session.flush()
    audit.record(
        session,
        context,
        f"{entity_type}.create",
        entity_type=entity_type,
        entity_id=instance.id,
        details=details,
    )
    await session.commit()


async def update(
    session: AsyncSession,
    context: AuditContext,
    instance: IdMixin,
    values: Mapping[str, object],
    *,
    entity_type: str,
) -> bool:
    """Apply `values`; audit (old → new) and commit only when something changed."""
    diff = audit.apply_changes(instance, values)
    if not diff:
        return False
    audit.record(
        session,
        context,
        f"{entity_type}.update",
        entity_type=entity_type,
        entity_id=instance.id,
        details=diff,
    )
    await session.commit()
    return True


async def delete(
    session: AsyncSession,
    context: AuditContext,
    instance: IdMixin,
    *,
    entity_type: str,
    details: AuditDetails | None = None,
) -> None:
    entity_id = instance.id
    await session.delete(instance)
    audit.record(
        session,
        context,
        f"{entity_type}.delete",
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    await session.commit()


def require_all_found(requested: Sequence[int], found: Sequence[IdMixin], *, field: str) -> None:
    """422 on `body.<field>` listing the requested ids that don't exist."""
    missing = sorted(set(requested) - {item.id for item in found})
    if missing:
        raise ValidationFailedError(
            details=[
                ErrorDetail(
                    field=f"body.{field}",
                    message=f"Unknown ids: {', '.join(map(str, missing))}",
                    type="unknown_ids",
                )
            ]
        )


async def replace_links[ItemT: IdMixin](
    session: AsyncSession,
    context: AuditContext,
    instance: IdMixin,
    links: list[ItemT],
    items: Sequence[ItemT],
    *,
    action: str,
    entity_type: str,
    field: str,
) -> bool:
    """Make the many-to-many collection `links` (e.g. `project.skills`) exactly `items`;
    audit the ids (`{field: {"old", "new"}}`) and commit only when the set changed."""
    old_ids = sorted(link.id for link in links)
    new_ids = sorted(item.id for item in items)
    if old_ids == new_ids:
        return False
    links[:] = items
    audit.record(
        session,
        context,
        action,
        entity_type=entity_type,
        entity_id=instance.id,
        details={field: {"old": old_ids, "new": new_ids}},
    )
    await session.commit()
    return True
