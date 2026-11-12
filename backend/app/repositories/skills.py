from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.pagination import PageParams, Sort
from app.models import Skill
from app.repositories.base import BaseRepository, SortColumns, apply_sort, search_filter

SORT_COLUMNS: SortColumns = {
    "display_order": Skill.display_order,
    "name": Skill.name,
    "created_at": Skill.created_at,
}


class SkillRepository(BaseRepository[Skill]):
    model = Skill

    async def get_with_icon(self, skill_id: int) -> Skill | None:
        return await self.session.scalar(
            select(Skill)
            .where(Skill.id == skill_id)
            .options(joinedload(Skill.icon))
            .execution_options(populate_existing=True)
        )

    async def search(
        self, *, category: str | None, q: str | None, sort: Sort, page: PageParams
    ) -> tuple[list[Skill], int]:
        """Filter by category (exact, case-insensitive by collation), search the name."""
        statement = select(Skill).options(joinedload(Skill.icon))
        if category is not None:
            statement = statement.where(Skill.category == category)
        if q:
            statement = statement.where(search_filter([Skill.name], q))
        statement = apply_sort(statement, sort, SORT_COLUMNS, Skill.id)
        return await self.paginate(statement, page)
