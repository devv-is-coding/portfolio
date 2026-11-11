"""Field types and validators shared by request schemas.

Optional text: `Annotated[str | None, Field(max_length=255), BlankToNone]`. The `Field`
must come before `BlankToNone`: placed after it, Pydantic applies the limit to `None`.
"""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, Field, HttpUrl, StringConstraints, UrlConstraints

from app.core.validators import blank_to_none


def _not_null(value: object) -> object:
    if value is None:
        raise ValueError("may be left out, but not set to null")
    return value


# Trimmed; must not be empty.
RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

# Trims optional text; empty or whitespace-only becomes null.
BlankToNone = AfterValidator(blank_to_none)

# PATCH fields for NOT NULL columns: leaving them out keeps the value, null is rejected.
# (Pydantic doesn't validate defaults, so an omitted field stays None without error.)
NotNull = AfterValidator(_not_null)


def _to_naive_utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is None:
        return value  # naive input is taken as UTC already
    return value.astimezone(UTC).replace(tzinfo=None)


# Stored as naive UTC (the database convention); an offset in the input is converted.
UtcDateTime = Annotated[datetime, AfterValidator(_to_naive_utc)]

DisplayOrder = Annotated[int, Field(ge=0, le=10_000, description="Lower comes first.")]

# A media library id (checked to exist and be the right kind by the service).
MediaId = Annotated[int, Field(ge=1)]

# http(s) only (HttpUrl), within the URL column length.
WebUrl = Annotated[HttpUrl, UrlConstraints(max_length=2048)]
