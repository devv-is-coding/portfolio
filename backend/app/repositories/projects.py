from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from app.core.pagination import PageParams, Sort
from app.models import Project, ProjectImage, Skill
from app.models.enums import PublicationStatus
from app.repositories.base import BaseRepository, SortColumns, apply_sort, search_filter

SORT_COLUMNS: SortColumns = {
    "display_order": Project.display_order,
    "published_at": Project.published_at,
    "title": Project.title,
    "created_at": Project.created_at,
}


def _summary_options() -> list[ExecutableOption]:
    return [selectinload(Project.thumbnail), selectinload(Project.skills)]


def _detail_options() -> list[ExecutableOption]:
    return [
        *_summary_options(),
        selectinload(Project.images).selectinload(ProjectImage.media),
    ]


class ProjectRepository(BaseRepository[Project]):
    model = Project

    async def get_with_details(self, project_id: int) -> Project | None:
        return await self.session.scalar(
            select(Project)
            .where(Project.id == project_id)
            .options(*_detail_options())
            .execution_options(populate_existing=True)
        )

    async def get_published_by_slug(self, slug: str) -> Project | None:
        return await self.session.scalar(
            select(Project)
            .where(Project.slug == slug, Project.status == PublicationStatus.PUBLISHED)
            .options(*_detail_options())
        )

    async def search(
        self,
        *,
        published_only: bool,
        status: PublicationStatus | None = None,
        featured: bool | None = None,
        skill_slug: str | None = None,
        q: str | None,
        sort: Sort,
        page: PageParams,
    ) -> tuple[list[Project], int]:
        conditions: list[ColumnElement[bool]] = []
        if published_only:
            conditions.append(Project.status == PublicationStatus.PUBLISHED)
        elif status is not None:
            conditions.append(Project.status == status)
        if featured is not None:
            conditions.append(Project.is_featured.is_(featured))
        if skill_slug is not None:
            conditions.append(Project.skills.any(Skill.slug == skill_slug))
        if q:
            conditions.append(search_filter([Project.title, Project.short_description], q))
        options = _summary_options() if published_only else _detail_options()
        statement = select(Project).where(*conditions).options(*options)
        statement = apply_sort(statement, sort, SORT_COLUMNS, Project.id)
        return await self.paginate(statement, page)
