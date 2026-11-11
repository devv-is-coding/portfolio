from sqlalchemy import ColumnElement, select

from app.core.pagination import PageParams, Sort
from app.models import Media
from app.models.enums import MediaKind
from app.models.media import DOCUMENT_MIME_TYPES, IMAGE_MIME_PREFIX
from app.repositories.base import BaseRepository, SortColumns, apply_sort, search_filter

SORT_COLUMNS: SortColumns = {
    "created_at": Media.created_at,
    "size_bytes": Media.size_bytes,
    "file_path": Media.file_path,
}


def _kind_filter(kind: MediaKind) -> ColumnElement[bool]:
    if kind is MediaKind.IMAGE:
        return Media.mime_type.startswith(IMAGE_MIME_PREFIX)
    return Media.mime_type.in_(DOCUMENT_MIME_TYPES)


class MediaRepository(BaseRepository[Media]):
    model = Media

    async def get_by_file_id(self, file_id: str) -> Media | None:
        return await self.session.scalar(select(Media).where(Media.file_id == file_id))

    async def search(
        self, *, kind: MediaKind | None, q: str | None, sort: Sort, page: PageParams
    ) -> tuple[list[Media], int]:
        """Filter by kind, search the path and alt text, sort and paginate."""
        statement = select(Media)
        if kind is not None:
            statement = statement.where(_kind_filter(kind))
        if q:
            statement = statement.where(search_filter([Media.file_path, Media.alt_text], q))
        statement = apply_sort(statement, sort, SORT_COLUMNS, Media.id)
        return await self.paginate(statement, page)
