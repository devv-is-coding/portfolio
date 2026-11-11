"""Blog posts: public reads (published only), admin CRUD and tags. Content is Markdown,
stored as sent; the frontend renders and sanitizes it."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationFailedError
from app.core.pagination import Page, PageParams, Sort
from app.core.slugs import slug_or_explicit
from app.models import BlogPost
from app.models.enums import MediaKind, PublicationStatus
from app.repositories.blog import BlogCategoryRepository, BlogPostRepository, BlogTagRepository
from app.schemas.blog import (
    POST_SLUG_MAX_LENGTH,
    BlogPostAdminRead,
    BlogPostCreate,
    BlogPostDetail,
    BlogPostSummary,
    BlogPostTagsUpdate,
    BlogPostUpdate,
    BlogTermSummary,
)
from app.schemas.errors import ErrorDetail
from app.services import crud
from app.services.audit import AuditContext
from app.services.media import require_media, to_public
from app.services.publishing import publication_values, resolve_published_at

ENTITY_TYPE = "blog_post"


class BlogPostNotFoundError(NotFoundError):
    default_message = "Post not found"


# --- reads -----------------------------------------------------------------------------


def _summary_fields(post: BlogPost, url_endpoint: str | None) -> dict[str, object]:
    return {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "excerpt": post.excerpt,
        "cover": to_public(post.cover, url_endpoint),
        "category": BlogTermSummary.model_validate(post.category) if post.category else None,
        "tags": [BlogTermSummary.model_validate(tag) for tag in post.tags],
        "published_at": post.published_at,
    }


def _detail_fields(post: BlogPost, url_endpoint: str | None) -> dict[str, object]:
    return _summary_fields(post, url_endpoint) | {
        "content": post.content,
        "updated_at": post.updated_at,
    }


def to_admin_read(post: BlogPost, url_endpoint: str | None) -> BlogPostAdminRead:
    return BlogPostAdminRead.model_validate(
        _detail_fields(post, url_endpoint)
        | {
            "status": post.status,
            "category_id": post.category_id,
            "cover_media_id": post.cover_media_id,
            "created_at": post.created_at,
        }
    )


async def list_published(
    session: AsyncSession,
    url_endpoint: str | None,
    *,
    category_slug: str | None,
    tag_slug: str | None,
    q: str | None,
    sort: Sort,
    page: PageParams,
) -> Page[BlogPostSummary]:
    items, total = await BlogPostRepository(session).search(
        published_only=True,
        category_slug=category_slug,
        tag_slug=tag_slug,
        q=q,
        sort=sort,
        page=page,
    )
    summaries = [BlogPostSummary.model_validate(_summary_fields(p, url_endpoint)) for p in items]
    return Page.create(summaries, total, page)


async def get_published(
    session: AsyncSession, url_endpoint: str | None, slug: str
) -> BlogPostDetail:
    """Drafts and archived posts are a 404, exactly like missing ones."""
    post = await BlogPostRepository(session).get_published_by_slug(slug)
    if post is None:
        raise BlogPostNotFoundError
    return BlogPostDetail.model_validate(_detail_fields(post, url_endpoint))


async def list_all(
    session: AsyncSession,
    url_endpoint: str | None,
    *,
    status: PublicationStatus | None,
    q: str | None,
    sort: Sort,
    page: PageParams,
) -> Page[BlogPostAdminRead]:
    items, total = await BlogPostRepository(session).search(
        published_only=False, status=status, q=q, sort=sort, page=page
    )
    return Page.create([to_admin_read(p, url_endpoint) for p in items], total, page)


async def _load(session: AsyncSession, post_id: int) -> BlogPost:
    post = await BlogPostRepository(session).get_with_details(post_id)
    if post is None:
        raise BlogPostNotFoundError
    return post


async def get(session: AsyncSession, url_endpoint: str | None, post_id: int) -> BlogPostAdminRead:
    return to_admin_read(await _load(session, post_id), url_endpoint)


# --- writes ----------------------------------------------------------------------------


async def _check_references(
    session: AsyncSession, category_id: int | None, cover_media_id: int | None
) -> None:
    """422 when the category doesn't exist or the cover isn't an image."""
    if category_id is not None and await BlogCategoryRepository(session).get(category_id) is None:
        raise ValidationFailedError(
            details=[
                ErrorDetail(
                    field="body.category_id",
                    message="No category with this id",
                    type="unknown_id",
                )
            ]
        )
    if cover_media_id is not None:
        await require_media(session, cover_media_id, MediaKind.IMAGE, "cover_media_id")


async def create(
    session: AsyncSession, url_endpoint: str | None, context: AuditContext, body: BlogPostCreate
) -> BlogPostAdminRead:
    await _check_references(session, body.category_id, body.cover_media_id)
    post = BlogPost(
        **body.model_dump(exclude={"slug", "published_at"}),
        slug=slug_or_explicit(body.slug, body.title, POST_SLUG_MAX_LENGTH),
        published_at=resolve_published_at(
            body.status, body.published_at, sent="published_at" in body.model_fields_set
        ),
    )
    await crud.create(
        session,
        context,
        post,
        entity_type=ENTITY_TYPE,
        details={"title": post.title, "slug": post.slug, "status": post.status.value},
    )
    return to_admin_read(await _load(session, post.id), url_endpoint)


async def update(
    session: AsyncSession,
    url_endpoint: str | None,
    context: AuditContext,
    post_id: int,
    body: BlogPostUpdate,
) -> BlogPostAdminRead:
    await _check_references(session, body.category_id, body.cover_media_id)
    post = await _load(session, post_id)
    values = body.model_dump(exclude_unset=True, exclude={"status", "published_at"})
    values |= publication_values(post, body.status, body.published_at, body.model_fields_set)
    if await crud.update(session, context, post, values, entity_type=ENTITY_TYPE):
        post = await _load(session, post_id)
    return to_admin_read(post, url_endpoint)


async def delete(session: AsyncSession, context: AuditContext, post_id: int) -> None:
    """Tag links go with it; the category, tags and cover image stay."""
    post = await _load(session, post_id)
    await crud.delete(
        session,
        context,
        post,
        entity_type=ENTITY_TYPE,
        details={"title": post.title, "slug": post.slug},
    )


async def replace_tags(
    session: AsyncSession,
    url_endpoint: str | None,
    context: AuditContext,
    post_id: int,
    body: BlogPostTagsUpdate,
) -> BlogPostAdminRead:
    """Set the post's tags to exactly these ids (duplicates ignored)."""
    requested = list(dict.fromkeys(body.tag_ids))
    tags = await BlogTagRepository(session).get_many(requested)
    crud.require_all_found(requested, tags, field="tag_ids")
    post = await _load(session, post_id)
    changed = await crud.replace_links(
        session,
        context,
        post,
        post.tags,
        tags,
        action=f"{ENTITY_TYPE}.tags_update",
        entity_type=ENTITY_TYPE,
        field="tag_ids",
    )
    if changed:
        post = await _load(session, post_id)
    return to_admin_read(post, url_endpoint)
