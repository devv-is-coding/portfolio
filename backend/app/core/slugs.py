"""URL slugs: `my-first-project`.

Schemas use `Slug` with the column's max length, e.g.
`slug: Annotated[Slug, Field(max_length=220)] | None = None`; services call
`slugify(title, max_length)` when the client sends none. A duplicate slug fails the
unique index and comes back as a 409 (app/core/errors.py).
"""

import re
import unicodedata
from typing import Annotated

from pydantic import Field

from app.core.errors import ValidationFailedError
from app.schemas.errors import ErrorDetail

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"

Slug = Annotated[
    str,
    Field(
        min_length=1,
        pattern=SLUG_PATTERN,
        description="Lowercase letters, digits and single hyphens, e.g. `my-first-project`.",
        examples=["my-first-project"],
    ),
]

_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")


def slugify(text: str, max_length: int) -> str:
    """`Café Déjà-vu!` → `cafe-deja-vu`, cut at a hyphen boundary to fit `max_length`.

    Returns "" when nothing usable is left (e.g. a title with only non-Latin letters);
    the caller must then ask for an explicit slug.
    """
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = _NON_ALPHANUMERIC.sub("-", ascii_text.lower()).strip("-")
    if len(slug) <= max_length:
        return slug
    cut = slug[:max_length]
    if slug[max_length] != "-" and "-" in cut:
        cut = cut[: cut.rindex("-")]
    return cut.strip("-")


def slug_or_explicit(slug: str | None, text: str, max_length: int) -> str:
    """The client's slug, or one made from `text`. 422 on `body.slug` when `text`
    gives nothing usable (e.g. only non-Latin letters): the client must send a slug."""
    if slug:
        return slug
    made = slugify(text, max_length)
    if not made:
        raise ValidationFailedError(
            details=[
                ErrorDetail(
                    field="body.slug",
                    message="Can't make a slug from this text; send one explicitly",
                    type="invalid_slug",
                )
            ]
        )
    return made
