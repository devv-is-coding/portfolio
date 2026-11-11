"""Field types and validators shared by request schemas.

Optional text: `Annotated[str | None, Field(max_length=255), BlankToNone]`. The `Field`
must come before `BlankToNone`: placed after it, Pydantic applies the limit to `None`.
"""

from typing import Annotated

from pydantic import AfterValidator, HttpUrl, StringConstraints, UrlConstraints

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

# http(s) only (HttpUrl), within the URL column length.
WebUrl = Annotated[HttpUrl, UrlConstraints(max_length=2048)]
