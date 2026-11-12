from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.core.slugs import Slug
from app.models.enums import PublicationStatus
from app.schemas.fields import (
    BlankToNone,
    DisplayOrder,
    MediaId,
    NotNull,
    RequiredText,
    UtcDateTime,
    WebUrl,
)
from app.schemas.media import PublicMedia

SLUG_MAX_LENGTH = 220
DESCRIPTION_MAX_LENGTH = 100_000  # Markdown; far below the LONGTEXT limit

Title = Annotated[RequiredText, Field(max_length=200)]
ProjectSlug = Annotated[Slug, Field(max_length=SLUG_MAX_LENGTH)]
ShortDescription = Annotated[str | None, Field(max_length=500), BlankToNone]
Description = Annotated[str | None, Field(max_length=DESCRIPTION_MAX_LENGTH), BlankToNone]


class ProjectCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "title": "Online shop",
                    "short_description": "A small shop with Stripe payments.",
                    "description": "## What it does\n\nCatalog, cart and checkout.",
                    "live_url": "https://shop.example.com",
                    "repository_url": "https://github.com/ada/shop",
                    "status": "published",
                    "is_featured": True,
                    "display_order": 1,
                }
            ]
        },
    )

    title: Title
    slug: ProjectSlug | None = Field(default=None, description="Made from the title when left out.")
    short_description: ShortDescription = None
    description: Description = Field(default=None, description="Markdown.")
    thumbnail_media_id: MediaId | None = Field(default=None, description="An image.")
    live_url: WebUrl | None = None
    repository_url: WebUrl | None = None
    status: PublicationStatus = PublicationStatus.DRAFT
    is_featured: bool = False
    display_order: DisplayOrder = 0
    published_at: UtcDateTime | None = Field(
        default=None, description="Set to now when publishing without one."
    )


class ProjectUpdate(BaseModel):
    """Only the fields sent change; `null` clears optional fields."""

    model_config = ConfigDict(extra="forbid")

    title: Annotated[Title | None, NotNull] = None
    slug: Annotated[ProjectSlug | None, NotNull] = None
    short_description: ShortDescription = None
    description: Description = None
    thumbnail_media_id: MediaId | None = None
    live_url: WebUrl | None = None
    repository_url: WebUrl | None = None
    status: Annotated[PublicationStatus | None, NotNull] = None
    is_featured: Annotated[bool | None, NotNull] = None
    display_order: Annotated[DisplayOrder | None, NotNull] = None
    published_at: UtcDateTime | None = None


class ProjectImageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    media_id: MediaId = Field(description="An image from the media library.")
    alt_text: Annotated[str | None, Field(max_length=255), BlankToNone] = Field(
        default=None, description="Overrides the media's own alt text."
    )
    display_order: DisplayOrder = 0


class ProjectImageUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alt_text: Annotated[str | None, Field(max_length=255), BlankToNone] = None
    display_order: Annotated[DisplayOrder | None, NotNull] = None


class ProjectSkillsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_ids: list[Annotated[int, Field(ge=1)]] = Field(
        max_length=100, description="The complete set; replaces the current skills."
    )


class SkillSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class ProjectImageRead(BaseModel):
    id: int
    media_id: int
    image: PublicMedia = Field(description="`alt_text` is the override, else the media's.")
    display_order: int


class ProjectSummary(BaseModel):
    """A published project in public lists (no long description or gallery)."""

    id: int
    title: str
    slug: str
    short_description: str | None
    thumbnail: PublicMedia | None
    live_url: str | None
    repository_url: str | None
    is_featured: bool
    display_order: int
    published_at: datetime | None
    skills: list[SkillSummary]


class ProjectDetail(ProjectSummary):
    description: str | None
    images: list[ProjectImageRead]
    updated_at: datetime


class ProjectAdminRead(ProjectDetail):
    status: PublicationStatus
    thumbnail_media_id: int | None
    created_at: datetime
