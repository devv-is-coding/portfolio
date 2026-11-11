"""Small reusable value checks for schemas and services."""

from datetime import date

from app.core.errors import ValidationFailedError
from app.schemas.errors import ErrorDetail


def blank_to_none(value: str | None) -> str | None:
    """Strip whitespace; an empty result means "no value"."""
    value = value.strip() if value else None
    return value or None


def ensure_date_order(
    start: date | None,
    end: date | None,
    *,
    field: str,
    message: str = "Must not be before the start date",
) -> None:
    """422 on `body.<field>` when both dates are set and `end` is before `start`.

    Services call it with the stored values merged with the PATCH, before changing
    anything, so a new end date is checked against the stored start date too (the
    database check would otherwise fail the request).
    """
    if start is not None and end is not None and end < start:
        raise ValidationFailedError(
            details=[ErrorDetail(field=f"body.{field}", message=message, type="date_order")]
        )
