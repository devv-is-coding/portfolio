from collections.abc import Sequence

from sqlalchemy import or_, select

from app.core.pagination import PageParams, Sort
from app.models import SiteSetting
from app.repositories.base import BaseRepository, SortColumns, apply_sort, search_filter

SORT_COLUMNS: SortColumns = {
    "key": SiteSetting.setting_key,
    "updated_at": SiteSetting.updated_at,
}


class SiteSettingRepository(BaseRepository[SiteSetting]):
    model = SiteSetting

    async def get_by_key(self, key: str) -> SiteSetting | None:
        return await self.session.scalar(select(SiteSetting).where(SiteSetting.setting_key == key))

    async def list_with_prefixes(self, prefixes: Sequence[str]) -> list[SiteSetting]:
        """Every setting whose key starts with one of `prefixes`, by key."""
        statement = (
            select(SiteSetting)
            .where(or_(*(SiteSetting.setting_key.startswith(p, autoescape=True) for p in prefixes)))
            .order_by(SiteSetting.setting_key)
        )
        return list((await self.session.scalars(statement)).all())

    async def search(
        self, *, q: str | None, sort: Sort, page: PageParams
    ) -> tuple[list[SiteSetting], int]:
        statement = select(SiteSetting)
        if q:
            statement = statement.where(search_filter([SiteSetting.setting_key], q))
        statement = apply_sort(statement, sort, SORT_COLUMNS, SiteSetting.id)
        return await self.paginate(statement, page)
