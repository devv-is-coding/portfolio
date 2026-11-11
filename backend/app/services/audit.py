"""The audit trail: who did what to which record, from which IP.

`record` adds the row to the caller's session without committing, so the audit
entry is saved or rolled back together with the change it describes.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog
from app.repositories.audit_logs import AuditLogRepository

# Values under these keys (at any depth, any letter case) are never stored.
SENSITIVE_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "token",
        "token_hash",
        "access_token",
        "refresh_token",
        "secret",
        "private_key",
        "authorization",
    }
)
REDACTED = "[redacted]"

type AuditDetails = Mapping[str, object]


@dataclass(frozen=True)
class AuditContext:
    """Who is acting: the admin's id (None for anonymous or CLI actions) and their IP."""

    user_id: int | None
    ip_address: str | None


def record(
    session: AsyncSession,
    context: AuditContext,
    action: str,
    *,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: AuditDetails | None = None,
) -> None:
    """Add an audit entry such as `project.update` to the current transaction."""
    AuditLogRepository(session).add(
        AuditLog(
            user_id=context.user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=redact(details) if details is not None else None,
            ip_address=context.ip_address,
        )
    )


def changes(
    before: Mapping[str, object], after: Mapping[str, object]
) -> dict[str, dict[str, object]]:
    """The fields of `after` whose value differs from `before`, as audit details:
    `{"alt_text": {"old": "A", "new": "B"}}`. Dates and enums become JSON values."""
    return {
        name: {"old": _json_value(before.get(name)), "new": _json_value(value)}
        for name, value in after.items()
        if before.get(name) != value
    }


def apply_changes(instance: object, values: Mapping[str, object]) -> dict[str, dict[str, object]]:
    """Set `values` on `instance` and return the audit diff of what really changed
    (empty when nothing did)."""
    diff = changes({name: getattr(instance, name) for name in values}, values)
    for name, value in values.items():
        setattr(instance, name, value)
    return diff


def _json_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, date):  # datetime is a date subclass
        return value.isoformat()
    return value


def redact(details: Mapping[str, object]) -> dict[str, object]:
    """Copy of `details` with every sensitive key's value replaced by `[redacted]`."""
    return {
        key: REDACTED if key.lower() in SENSITIVE_KEYS else _redact_value(value)
        for key, value in details.items()
    }


def _redact_value(value: object) -> object:
    if isinstance(value, Mapping):
        return redact({str(key): item for key, item in value.items()})
    if isinstance(value, list | tuple):
        return [_redact_value(item) for item in value]
    return value
