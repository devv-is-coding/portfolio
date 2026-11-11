from datetime import datetime

from sqlalchemy import ColumnElement, select

from app.core.pagination import PageParams, Sort
from app.models import AuditLog
from app.repositories.base import BaseRepository, SortColumns, apply_sort

SORT_COLUMNS: SortColumns = {"created_at": AuditLog.created_at}


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    async def search(
        self,
        *,
        user_id: int | None,
        action: str | None,
        entity_type: str | None,
        entity_id: int | None,
        since: datetime | None,
        until: datetime | None,
        sort: Sort,
        page: PageParams,
    ) -> tuple[list[AuditLog], int]:
        """Exact-match filters; `since` is inclusive, `until` exclusive."""
        conditions: list[ColumnElement[bool]] = []
        if user_id is not None:
            conditions.append(AuditLog.user_id == user_id)
        if action is not None:
            conditions.append(AuditLog.action == action)
        if entity_type is not None:
            conditions.append(AuditLog.entity_type == entity_type)
        if entity_id is not None:
            conditions.append(AuditLog.entity_id == entity_id)
        if since is not None:
            conditions.append(AuditLog.created_at >= since)
        if until is not None:
            conditions.append(AuditLog.created_at < until)
        statement = apply_sort(select(AuditLog).where(*conditions), sort, SORT_COLUMNS, AuditLog.id)
        return await self.paginate(statement, page)
