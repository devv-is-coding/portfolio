from sqlalchemy import select

from app.core.pagination import PageParams
from app.models import Experience
from app.repositories.base import BaseRepository, search_filter


class ExperienceRepository(BaseRepository[Experience]):
    model = Experience

    async def search(self, *, q: str | None, page: PageParams) -> tuple[list[Experience], int]:
        """Current jobs first, then the most recent start; `q` searches company and position."""
        statement = select(Experience).order_by(
            Experience.end_date.is_(None).desc(),
            Experience.start_date.desc(),
            Experience.display_order.asc(),
            Experience.id.desc(),
        )
        if q:
            statement = statement.where(search_filter([Experience.company, Experience.position], q))
        return await self.paginate(statement, page)
