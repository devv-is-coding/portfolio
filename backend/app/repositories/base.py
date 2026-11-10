from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import ColumnElement, Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import QueryableAttribute

from app.core.pagination import PageParams, Sort
from app.models.base import Base

type SortColumns = Mapping[str, QueryableAttribute[Any]]


class BaseRepository[ModelT: Base]:
    """The operations every repository needs. Subclasses set `model` and add only
    the queries their service actually uses."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id_: int) -> ModelT | None:
        return await self.session.get(self.model, id_)

    def add(self, instance: ModelT) -> None:
        self.session.add(instance)

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)

    async def flush(self) -> None:
        """Send pending changes, so generated ids and constraint errors appear now."""
        await self.session.flush()

    async def paginate(
        self, statement: Select[ModelT], params: PageParams
    ) -> tuple[list[ModelT], int]:
        """One page of `statement` plus the total row count across all pages."""
        count = select(func.count()).select_from(statement.order_by(None).subquery())
        total = await self.session.scalar(count) or 0
        rows = await self.session.scalars(statement.limit(params.size).offset(params.offset))
        return list(rows.all()), total


def apply_sort[*RowTs](
    statement: Select[*RowTs],
    sort: Sort,
    columns: SortColumns,
    tiebreaker: QueryableAttribute[Any],
) -> Select[*RowTs]:
    """ORDER BY the requested fields, then `tiebreaker` (the id), so rows with equal
    sort values keep a stable order and pages never repeat or skip a row.

    `sort` comes from `parse_sort`, which only allows names that are in `columns`.
    """
    clauses = [
        columns[field.name].desc() if field.descending else columns[field.name].asc()
        for field in sort
    ]
    return statement.order_by(*clauses, tiebreaker.asc())


def search_filter(columns: Sequence[QueryableAttribute[str]], term: str) -> ColumnElement[bool]:
    """Rows where any of `columns` contains `term`. `%` and `_` in the term are
    escaped, so they match literally; the collation makes it case-insensitive."""
    return or_(*(column.contains(term, autoescape=True) for column in columns))
