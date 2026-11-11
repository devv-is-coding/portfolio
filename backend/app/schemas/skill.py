from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.core.slugs import Slug
from app.schemas.fields import BlankToNone, NotNull, RequiredText
from app.schemas.media import PublicMedia

NAME_MAX_LENGTH = 100
SLUG_MAX_LENGTH = 120

SkillName = Annotated[RequiredText, Field(max_length=NAME_MAX_LENGTH, examples=["FastAPI"])]
SkillSlug = Annotated[Slug, Field(max_length=SLUG_MAX_LENGTH)]
Category = Annotated[
    str | None,
    Field(max_length=100, description="Free text the frontend groups by, e.g. `backend`."),
    BlankToNone,
]
IconMediaId = Annotated[int | None, Field(ge=1, description="An image from the media library.")]
DisplayOrder = Annotated[int, Field(ge=0, le=10_000)]


class SkillCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: SkillName
    slug: SkillSlug | None = Field(default=None, description="Made from the name when left out.")
    category: Category = None
    icon_media_id: IconMediaId = None
    display_order: DisplayOrder = 0


class SkillUpdate(BaseModel):
    """Only the fields sent change; `null` clears `category` or `icon_media_id`."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[SkillName | None, NotNull] = None
    slug: Annotated[SkillSlug | None, NotNull] = None
    category: Category = None
    icon_media_id: IconMediaId = None
    display_order: Annotated[DisplayOrder | None, NotNull] = None


class SkillRead(BaseModel):
    id: int
    name: str
    slug: str
    category: str | None
    icon_media_id: int | None
    icon: PublicMedia | None
    display_order: int
    created_at: datetime
    updated_at: datetime
