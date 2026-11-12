from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.core.database import SessionDep
from app.core.errors import error_responses
from app.core.imagekit import MediaUrlEndpointDep
from app.core.pagination import Page, PageParamsDep, SearchQuery, Sort, sort_query
from app.core.slugs import Slug
from app.dependencies import AuditContextDep, get_current_user
from app.models.enums import PublicationStatus
from app.schemas.blog import (
    POST_SLUG_MAX_LENGTH,
    TERM_SLUG_MAX_LENGTH,
    BlogPostAdminRead,
    BlogPostCreate,
    BlogPostDetail,
    BlogPostSummary,
    BlogPostTagsUpdate,
    BlogPostUpdate,
    BlogTermCreate,
    BlogTermRead,
    BlogTermUpdate,
)
from app.services import blog_posts, blog_terms
from app.services.blog_terms import CATEGORY, TAG

router = APIRouter(prefix="/blog", tags=["blog"], responses=error_responses(422, 503))
admin_router = APIRouter(
    prefix="/admin/blog",
    tags=["blog"],
    dependencies=[Depends(get_current_user)],
    responses=error_responses(401, 422, 503),
)

Id = Annotated[int, Path(ge=1)]
TermSort = Annotated[Sort, Depends(sort_query("name", "created_at", default="name"))]
PublicPostSort = Annotated[
    Sort, Depends(sort_query("published_at", "title", default="-published_at"))
]
AdminPostSort = Annotated[
    Sort, Depends(sort_query("published_at", "title", "created_at", default="-created_at"))
]
TermSlugFilter = Annotated[str | None, Query(max_length=TERM_SLUG_MAX_LENGTH)]


# --- public ----------------------------------------------------------------------------


@router.get("/categories")
async def list_categories(
    session: SessionDep, page: PageParamsDep, sort: TermSort, q: SearchQuery = None
) -> Page[BlogTermRead]:
    """Every category, by name. `q` searches the name."""
    return await blog_terms.list_terms(session, CATEGORY, q=q, sort=sort, page=page)


@router.get("/tags")
async def list_tags(
    session: SessionDep, page: PageParamsDep, sort: TermSort, q: SearchQuery = None
) -> Page[BlogTermRead]:
    """Every tag, by name. `q` searches the name."""
    return await blog_terms.list_terms(session, TAG, q=q, sort=sort, page=page)


@router.get("/posts")
async def list_posts(
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
    page: PageParamsDep,
    sort: PublicPostSort,
    q: SearchQuery = None,
    category: Annotated[TermSlugFilter, Query(description="A category slug.")] = None,
    tag: Annotated[TermSlugFilter, Query(description="A tag slug.")] = None,
) -> Page[BlogPostSummary]:
    """Published posts, newest first, without their content. `q` searches the title
    and excerpt."""
    return await blog_posts.list_published(
        session, url_endpoint, category_slug=category, tag_slug=tag, q=q, sort=sort, page=page
    )


@router.get("/posts/{slug}", responses=error_responses(404))
async def get_post(
    slug: Annotated[Slug, Path(max_length=POST_SLUG_MAX_LENGTH)],
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> BlogPostDetail:
    """A published post with its Markdown content. Drafts and archived ones are 404."""
    return await blog_posts.get_published(session, url_endpoint, slug)


# --- admin: categories and tags --------------------------------------------------------


@admin_router.post(
    "/categories", status_code=status.HTTP_201_CREATED, responses=error_responses(409)
)
async def create_category(
    body: BlogTermCreate, context: AuditContextDep, session: SessionDep
) -> BlogTermRead:
    """The slug is made from the name when left out; name and slug are unique (409)."""
    return await blog_terms.create_term(session, context, CATEGORY, body)


@admin_router.get("/categories/{category_id}", responses=error_responses(404))
async def get_category(category_id: Id, session: SessionDep) -> BlogTermRead:
    """One category, for editing."""
    return await blog_terms.get_term(session, CATEGORY, category_id)


@admin_router.patch("/categories/{category_id}", responses=error_responses(404, 409))
async def update_category(
    category_id: Id, body: BlogTermUpdate, context: AuditContextDep, session: SessionDep
) -> BlogTermRead:
    """Rename the category or change its slug (409 if taken)."""
    return await blog_terms.update_term(session, context, CATEGORY, category_id, body)


@admin_router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(404),
)
async def delete_category(
    category_id: Id, context: AuditContextDep, session: SessionDep
) -> Response:
    """Its posts stay, uncategorized."""
    await blog_terms.delete_term(session, context, CATEGORY, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_router.post("/tags", status_code=status.HTTP_201_CREATED, responses=error_responses(409))
async def create_tag(
    body: BlogTermCreate, context: AuditContextDep, session: SessionDep
) -> BlogTermRead:
    """The slug is made from the name when left out; name and slug are unique (409)."""
    return await blog_terms.create_term(session, context, TAG, body)


@admin_router.get("/tags/{tag_id}", responses=error_responses(404))
async def get_tag(tag_id: Id, session: SessionDep) -> BlogTermRead:
    """One tag, for editing."""
    return await blog_terms.get_term(session, TAG, tag_id)


@admin_router.patch("/tags/{tag_id}", responses=error_responses(404, 409))
async def update_tag(
    tag_id: Id, body: BlogTermUpdate, context: AuditContextDep, session: SessionDep
) -> BlogTermRead:
    """Rename the tag or change its slug (409 if taken)."""
    return await blog_terms.update_term(session, context, TAG, tag_id, body)


@admin_router.delete(
    "/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404)
)
async def delete_tag(tag_id: Id, context: AuditContextDep, session: SessionDep) -> Response:
    """The tag is removed from every post."""
    await blog_terms.delete_term(session, context, TAG, tag_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- admin: posts ----------------------------------------------------------------------


@admin_router.get("/posts")
async def list_all_posts(
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
    page: PageParamsDep,
    sort: AdminPostSort,
    q: SearchQuery = None,
    post_status: Annotated[
        PublicationStatus | None, Query(alias="status", description="Only this status.")
    ] = None,
) -> Page[BlogPostAdminRead]:
    """Every post, whatever its status, newest first by default."""
    return await blog_posts.list_all(
        session, url_endpoint, status=post_status, q=q, sort=sort, page=page
    )


@admin_router.post("/posts", status_code=status.HTTP_201_CREATED, responses=error_responses(409))
async def create_post(
    body: BlogPostCreate,
    context: AuditContextDep,
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> BlogPostAdminRead:
    """Create a post. The slug is made from the title when left out (409 if taken);
    publishing without `published_at` sets it to now."""
    return await blog_posts.create(session, url_endpoint, context, body)


@admin_router.get("/posts/{post_id}", responses=error_responses(404))
async def get_any_post(
    post_id: Id, session: SessionDep, url_endpoint: MediaUrlEndpointDep
) -> BlogPostAdminRead:
    """One post in any status, with its Markdown, for editing."""
    return await blog_posts.get(session, url_endpoint, post_id)


@admin_router.patch("/posts/{post_id}", responses=error_responses(404, 409))
async def update_post(
    post_id: Id,
    body: BlogPostUpdate,
    context: AuditContextDep,
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> BlogPostAdminRead:
    """Change only the fields sent. Publishing without `published_at` sets it to now;
    clearing it while published is a 422."""
    return await blog_posts.update(session, url_endpoint, context, post_id, body)


@admin_router.delete(
    "/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404)
)
async def delete_post(post_id: Id, context: AuditContextDep, session: SessionDep) -> Response:
    """Delete the post; its tag links go with it, the category and tags stay."""
    await blog_posts.delete(session, context, post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_router.put("/posts/{post_id}/tags", responses=error_responses(404))
async def replace_post_tags(
    post_id: Id,
    body: BlogPostTagsUpdate,
    context: AuditContextDep,
    session: SessionDep,
    url_endpoint: MediaUrlEndpointDep,
) -> BlogPostAdminRead:
    """Set the post's tags to exactly this list; unknown ids are a 422."""
    return await blog_posts.replace_tags(session, url_endpoint, context, post_id, body)
