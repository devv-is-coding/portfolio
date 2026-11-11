"""Small reusable value normalizers for Pydantic fields and query parameters."""


def blank_to_none(value: str | None) -> str | None:
    """Strip whitespace; an empty result means "no value"."""
    value = value.strip() if value else None
    return value or None
