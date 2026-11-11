"""Blog categories and tags. Both are a unique name and slug, so one set of functions
serves both, told apart by a `TermKind`."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import Page, PageParams, Sort
from app.core.slugs import slug_or_explicit
from app.models import BlogCategory, BlogTag
from app.repositories.blog import BlogCategoryRepository, BlogTagRepository, BlogTermRepository
from app.schemas.blog import TERM_SLUG_MAX_LENGTH, BlogTermCreate, BlogTermRead, BlogTermUpdate
from app.services import crud
from app.services.audit import AuditContext


@dataclass(frozen=True)
class TermKind[TermT: (BlogCategory, BlogTag)]:
    model: type[TermT]
    repository: type[BlogTermRepository[TermT]]
    entity_type: str
    not_found_message: str


CATEGORY = TermKind(BlogCategory, BlogCategoryRepository, "blog_category", "Category not found")
TAG = TermKind(BlogTag, BlogTagRepository, "blog_tag", "Tag not found")


async def list_terms[TermT: (BlogCategory, BlogTag)](
    session: AsyncSession, kind: TermKind[TermT], *, q: str | None, sort: Sort, page: PageParams
) -> Page[BlogTermRead]:
    items, total = await kind.repository(session).search(q=q, sort=sort, page=page)
    return Page.create([BlogTermRead.model_validate(item) for item in items], total, page)


async def _load[TermT: (BlogCategory, BlogTag)](
    session: AsyncSession, kind: TermKind[TermT], term_id: int
) -> TermT:
    term = await kind.repository(session).get(term_id)
    if term is None:
        raise NotFoundError(kind.not_found_message)
    return term


async def get_term[TermT: (BlogCategory, BlogTag)](
    session: AsyncSession, kind: TermKind[TermT], term_id: int
) -> BlogTermRead:
    return BlogTermRead.model_validate(await _load(session, kind, term_id))


async def create_term[TermT: (BlogCategory, BlogTag)](
    session: AsyncSession, context: AuditContext, kind: TermKind[TermT], body: BlogTermCreate
) -> BlogTermRead:
    """Duplicate names or slugs fail on the unique indexes and come back as 409."""
    term = kind.model(
        name=body.name, slug=slug_or_explicit(body.slug, body.name, TERM_SLUG_MAX_LENGTH)
    )
    await crud.create(
        session,
        context,
        term,
        entity_type=kind.entity_type,
        details={"name": term.name, "slug": term.slug},
    )
    await kind.repository(session).refresh(term)
    return BlogTermRead.model_validate(term)


async def update_term[TermT: (BlogCategory, BlogTag)](
    session: AsyncSession,
    context: AuditContext,
    kind: TermKind[TermT],
    term_id: int,
    body: BlogTermUpdate,
) -> BlogTermRead:
    term = await _load(session, kind, term_id)
    values = body.model_dump(exclude_unset=True)
    if await crud.update(session, context, term, values, entity_type=kind.entity_type):
        await kind.repository(session).refresh(term)
    return BlogTermRead.model_validate(term)


async def delete_term[TermT: (BlogCategory, BlogTag)](
    session: AsyncSession, context: AuditContext, kind: TermKind[TermT], term_id: int
) -> None:
    """A deleted category leaves its posts uncategorized; a deleted tag is removed from
    its posts (both by the database's foreign key rules)."""
    term = await _load(session, kind, term_id)
    await crud.delete(
        session,
        context,
        term,
        entity_type=kind.entity_type,
        details={"name": term.name, "slug": term.slug},
    )
