from sqlalchemy import select

from app.core.pagination import PageParams
from app.models import Certification
from app.repositories.base import BaseRepository, search_filter


class CertificationRepository(BaseRepository[Certification]):
    model = Certification

    async def search(self, *, q: str | None, page: PageParams) -> tuple[list[Certification], int]:
        """Newest issue date first (undated last); `q` searches the name and issuer."""
        statement = select(Certification).order_by(
            Certification.issued_at.is_(None).asc(),
            Certification.issued_at.desc(),
            Certification.id.desc(),
        )
        if q:
            columns = [Certification.name, Certification.issuing_organization]
            statement = statement.where(search_filter(columns, q))
        return await self.paginate(statement, page)
