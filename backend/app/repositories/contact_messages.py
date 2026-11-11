from sqlalchemy import select

from app.core.pagination import PageParams, Sort
from app.models import ContactMessage
from app.models.enums import ContactMessageStatus
from app.repositories.base import BaseRepository, SortColumns, apply_sort, search_filter

SORT_COLUMNS: SortColumns = {"created_at": ContactMessage.created_at, "name": ContactMessage.name}


class ContactMessageRepository(BaseRepository[ContactMessage]):
    model = ContactMessage

    async def search(
        self,
        *,
        status: ContactMessageStatus | None,
        q: str | None,
        sort: Sort,
        page: PageParams,
    ) -> tuple[list[ContactMessage], int]:
        """Filter by status; `q` searches the sender's name and email and the subject."""
        statement = select(ContactMessage)
        if status is not None:
            statement = statement.where(ContactMessage.status == status)
        if q:
            columns = [ContactMessage.name, ContactMessage.email, ContactMessage.subject]
            statement = statement.where(search_filter(columns, q))
        statement = apply_sort(statement, sort, SORT_COLUMNS, ContactMessage.id)
        return await self.paginate(statement, page)
