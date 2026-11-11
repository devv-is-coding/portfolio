"""Pagination, sorting and search parameters shared by every list endpoint.

    GET /projects?page=2&size=20&sort=-published_at,title&q=fastapi

Routers declare `page: PageParamsDep`, `sort: Annotated[Sort, Depends(sort_query(...))]`
and `q: SearchQuery`; repositories apply them with the helpers in
app/repositories/base.py and return a `Page`.
"""

from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass
from math import ceil
from typing import Annotated

from fastapi import Query
from pydantic import AfterValidator, BaseModel, Field

from app.core.errors import ValidationFailedError
from app.core.validators import blank_to_none
from app.schemas.errors import ErrorDetail

MAX_PAGE_SIZE = 100
MAX_SEARCH_LENGTH = 100


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number, starting at 1.")
    size: int = Field(default=20, ge=1, le=MAX_PAGE_SIZE, description="Items per page.")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


PageParamsDep = Annotated[PageParams, Query()]


class Page[ItemT](BaseModel):
    items: list[ItemT]
    total: int = Field(description="Items across all pages.")
    page: int
    size: int
    pages: int = Field(description="Number of pages (0 when there are no items).")

    @classmethod
    def create(cls, items: Sequence[ItemT], total: int, params: PageParams) -> "Page[ItemT]":
        return cls(
            items=list(items),
            total=total,
            page=params.page,
            size=params.size,
            pages=ceil(total / params.size),
        )


@dataclass(frozen=True)
class SortField:
    name: str
    descending: bool


type Sort = tuple[SortField, ...]


def parse_sort(raw: str, allowed: Collection[str]) -> Sort:
    """`-published_at,title` → (published_at desc, title asc). Unknown or repeated
    fields raise a 422 that lists the allowed ones."""
    fields: list[SortField] = []
    for part in raw.split(","):
        part = part.strip()
        name = part.removeprefix("-")
        if name not in allowed or any(field.name == name for field in fields):
            raise ValidationFailedError(
                details=[
                    ErrorDetail(
                        field="query.sort",
                        message=f"Invalid sort field {name!r}. Allowed: {', '.join(allowed)}",
                        type="invalid_sort",
                    )
                ]
            )
        fields.append(SortField(name=name, descending=part.startswith("-")))
    return tuple(fields)


def sort_query(*allowed: str, default: str) -> Callable[[str | None], Sort]:
    """A dependency parsing `?sort=` against this resource's allowed fields.

    The default is checked once, when the router module is imported.
    """
    parse_sort(default, allowed)
    description = (
        f"Comma-separated fields, `-` prefix for descending. "
        f"Allowed: {', '.join(allowed)}. Default: `{default}`."
    )

    def dependency(
        sort: Annotated[str | None, Query(max_length=200, description=description)] = None,
    ) -> Sort:
        return parse_sort(sort or default, allowed)

    return dependency


SearchQuery = Annotated[
    str | None,
    Query(max_length=MAX_SEARCH_LENGTH, description="Case-insensitive text search."),
    AfterValidator(blank_to_none),
]
