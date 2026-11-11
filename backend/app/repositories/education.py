from sqlalchemy import select

from app.core.pagination import PageParams
from app.models import Education
from app.repositories.base import BaseRepository, search_filter


class EducationRepository(BaseRepository[Education]):
    model = Education

    async def search(self, *, q: str | None, page: PageParams) -> tuple[list[Education], int]:
        """In progress (no end date) first, then by end and start date, newest first;
        `q` searches the institution, degree and field of study."""
        statement = select(Education).order_by(
            Education.end_date.is_(None).desc(),
            Education.end_date.desc(),
            Education.start_date.desc(),
            Education.id.desc(),
        )
        if q:
            columns = [Education.institution, Education.degree, Education.field_of_study]
            statement = statement.where(search_filter(columns, q))
        return await self.paginate(statement, page)
