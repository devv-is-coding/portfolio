from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import defer, joinedload, selectinload
from sqlalchemy.sql.base import ExecutableOption

from app.core.pagination import PageParams, Sort
from app.models import BlogCategory, BlogPost, BlogTag
from app.models.enums import PublicationStatus
from app.repositories.base import BaseRepository, SortColumns, apply_sort, search_filter


class BlogTermRepository[TermT: (BlogCategory, BlogTag)](BaseRepository[TermT]):
    """Categories and tags: the same columns and queries."""

    async def search(
        self, *, q: str | None, sort: Sort, page: PageParams
    ) -> tuple[list[TermT], int]:
        statement = select(self.model)
        if q:
            statement = statement.where(search_filter([self.model.name], q))
        columns: SortColumns = {"name": self.model.name, "created_at": self.model.created_at}
        statement = apply_sort(statement, sort, columns, self.model.id)
        return await self.paginate(statement, page)


class BlogCategoryRepository(BlogTermRepository[BlogCategory]):
    model = BlogCategory


class BlogTagRepository(BlogTermRepository[BlogTag]):
    model = BlogTag


POST_SORT_COLUMNS: SortColumns = {
    "published_at": BlogPost.published_at,
    "title": BlogPost.title,
    "created_at": BlogPost.created_at,
}


def _post_options() -> list[ExecutableOption]:
    return [
        joinedload(BlogPost.cover),
        joinedload(BlogPost.category),
        selectinload(BlogPost.tags),
    ]


class BlogPostRepository(BaseRepository[BlogPost]):
    model = BlogPost

    async def get_with_details(self, post_id: int) -> BlogPost | None:
        return await self.session.scalar(
            select(BlogPost)
            .where(BlogPost.id == post_id)
            .options(*_post_options())
            .execution_options(populate_existing=True)
        )

    async def get_published_by_slug(self, slug: str) -> BlogPost | None:
        return await self.session.scalar(
            select(BlogPost)
            .where(BlogPost.slug == slug, BlogPost.status == PublicationStatus.PUBLISHED)
            .options(*_post_options())
        )

    async def search(
        self,
        *,
        published_only: bool,
        status: PublicationStatus | None = None,
        category_slug: str | None = None,
        tag_slug: str | None = None,
        q: str | None,
        sort: Sort,
        page: PageParams,
    ) -> tuple[list[BlogPost], int]:
        conditions: list[ColumnElement[bool]] = []
        if published_only:
            conditions.append(BlogPost.status == PublicationStatus.PUBLISHED)
        elif status is not None:
            conditions.append(BlogPost.status == status)
        if category_slug is not None:
            conditions.append(BlogPost.category.has(BlogCategory.slug == category_slug))
        if tag_slug is not None:
            conditions.append(BlogPost.tags.any(BlogTag.slug == tag_slug))
        if q:
            conditions.append(search_filter([BlogPost.title, BlogPost.excerpt], q))
        options = _post_options()
        if published_only:
            # Public lists show no content; don't load the Markdown at all.
            options.append(defer(BlogPost.content, raiseload=True))
        statement = select(BlogPost).where(*conditions).options(*options)
        statement = apply_sort(statement, sort, POST_SORT_COLUMNS, BlogPost.id)
        return await self.paginate(statement, page)
