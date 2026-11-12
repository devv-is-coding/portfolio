from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.core.slugs import Slug
from app.models.enums import PublicationStatus
from app.schemas.fields import BlankToNone, MediaId, NotNull, RequiredText, UtcDateTime
from app.schemas.media import PublicMedia

# --- categories and tags (same shape: a unique name and slug) -------------------------

TERM_SLUG_MAX_LENGTH = 120

TermName = Annotated[RequiredText, Field(max_length=100, examples=["Python"])]
TermSlug = Annotated[Slug, Field(max_length=TERM_SLUG_MAX_LENGTH)]


class BlogTermCreate(BaseModel):
    """A category or a tag. Name and slug are unique (409)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"name": "Python"}]},
    )

    name: TermName
    slug: TermSlug | None = Field(default=None, description="Made from the name when left out.")


class BlogTermUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[TermName | None, NotNull] = None
    slug: Annotated[TermSlug | None, NotNull] = None


class BlogTermSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class BlogTermRead(BlogTermSummary):
    created_at: datetime
    updated_at: datetime


# --- posts -----------------------------------------------------------------------------

POST_SLUG_MAX_LENGTH = 280
CONTENT_MAX_LENGTH = 200_000  # Markdown; far below the LONGTEXT limit

Title = Annotated[RequiredText, Field(max_length=255)]
PostSlug = Annotated[Slug, Field(max_length=POST_SLUG_MAX_LENGTH)]
Excerpt = Annotated[str | None, Field(max_length=500), BlankToNone]
Content = Annotated[
    RequiredText,
    Field(max_length=CONTENT_MAX_LENGTH, description="Markdown, stored as sent."),
]
CategoryId = Annotated[int, Field(ge=1)]


class BlogPostCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "title": "Why I moved to FastAPI",
                    "excerpt": "Typed endpoints and fewer surprises.",
                    "content": "## The short version\n\nPydantic does the validation.",
                    "status": "draft",
                }
            ]
        },
    )

    title: Title
    slug: PostSlug | None = Field(default=None, description="Made from the title when left out.")
    excerpt: Excerpt = None
    content: Content
    category_id: CategoryId | None = None
    cover_media_id: MediaId | None = Field(default=None, description="An image.")
    status: PublicationStatus = PublicationStatus.DRAFT
    published_at: UtcDateTime | None = Field(
        default=None, description="Set to now when publishing without one."
    )


class BlogPostUpdate(BaseModel):
    """Only the fields sent change; `null` clears optional fields."""

    model_config = ConfigDict(extra="forbid")

    title: Annotated[Title | None, NotNull] = None
    slug: Annotated[PostSlug | None, NotNull] = None
    excerpt: Excerpt = None
    content: Annotated[Content | None, NotNull] = None
    category_id: CategoryId | None = None
    cover_media_id: MediaId | None = None
    status: Annotated[PublicationStatus | None, NotNull] = None
    published_at: UtcDateTime | None = None


class BlogPostTagsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag_ids: list[Annotated[int, Field(ge=1)]] = Field(
        max_length=50, description="The complete set; replaces the current tags."
    )


class BlogPostSummary(BaseModel):
    """A published post in public lists (no content)."""

    id: int
    title: str
    slug: str
    excerpt: str | None
    cover: PublicMedia | None
    category: BlogTermSummary | None
    tags: list[BlogTermSummary]
    published_at: datetime | None


class BlogPostDetail(BlogPostSummary):
    content: str = Field(description="Markdown; the frontend renders and sanitizes it.")
    updated_at: datetime


class BlogPostAdminRead(BlogPostDetail):
    status: PublicationStatus
    category_id: int | None
    cover_media_id: int | None
    created_at: datetime
