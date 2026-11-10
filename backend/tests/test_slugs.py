from typing import Annotated

import pytest
from pydantic import Field, TypeAdapter, ValidationError

from app.core.slugs import Slug, slugify


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("My First Project", "my-first-project"),
        ("Café Déjà-vu!", "cafe-deja-vu"),
        ("  --Hello,   World--  ", "hello-world"),
        ("FastAPI & Next.js 16", "fastapi-next-js-16"),
        ("Straße", "strae"),  # ß has no ASCII decomposition and is dropped
        ("日本語", ""),
        ("", ""),
    ],
)
def test_slugify(text: str, expected: str) -> None:
    assert slugify(text, max_length=100) == expected


@pytest.mark.parametrize(
    ("text", "max_length", "expected"),
    [
        ("alpha beta gamma", 10, "alpha-beta"),  # cut falls on a hyphen
        ("alpha beta gamma", 12, "alpha-beta"),  # never ends mid-word
        ("alphabetagamma", 5, "alpha"),  # one long word is cut
        ("alpha beta", 10, "alpha-beta"),  # fits exactly
    ],
)
def test_slugify_fits_max_length_without_trailing_hyphen(
    text: str, max_length: int, expected: str
) -> None:
    slug = slugify(text, max_length)

    assert slug == expected
    assert len(slug) <= max_length
    assert not slug.endswith("-")


_ProjectSlug = TypeAdapter(Annotated[Slug, Field(max_length=20)])


@pytest.mark.parametrize("value", ["a", "my-project", "v2-release-2026"])
def test_valid_slugs(value: str) -> None:
    assert _ProjectSlug.validate_python(value) == value


@pytest.mark.parametrize(
    "value",
    ["", "My-Project", "my--project", "-project", "project-", "my project", "café", "a" * 21],
)
def test_invalid_slugs(value: str) -> None:
    with pytest.raises(ValidationError):
        _ProjectSlug.validate_python(value)
