from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.fields import BlankToNone, DisplayOrder, NotNull, RequiredText, WebUrl
from app.schemas.media import PublicMedia

BIOGRAPHY_MAX_LENGTH = 10_000  # fits the TEXT column (65,535 bytes) in any UTF-8

FullName = Annotated[RequiredText, Field(max_length=150)]
Headline = Annotated[str | None, Field(max_length=255), BlankToNone]
Biography = Annotated[str | None, Field(max_length=BIOGRAPHY_MAX_LENGTH), BlankToNone]
Location = Annotated[str | None, Field(max_length=150), BlankToNone]
Phone = Annotated[str | None, Field(max_length=30, pattern=r"^\+?[0-9 ().-]{3,30}$"), BlankToNone]
MediaId = Annotated[int | None, Field(ge=1)]
Platform = Annotated[
    str,
    Field(
        min_length=1,
        max_length=50,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="Lowercase name the frontend maps to an icon, e.g. `github`, `linkedin`.",
    ),
]


class ProfileWrite(BaseModel):
    """`PUT /admin/profile`: the whole profile; fields left out become empty."""

    model_config = ConfigDict(extra="forbid")

    full_name: FullName
    headline: Headline = None
    biography: Biography = None
    location: Location = None
    email: EmailStr | None = None
    phone: Phone = None
    avatar_media_id: MediaId = Field(default=None, description="An image from the media library.")
    resume_media_id: MediaId = Field(default=None, description="A PDF from the media library.")


class ProfileUpdate(BaseModel):
    """`PATCH /admin/profile`: only the fields sent change; `null` clears a field."""

    model_config = ConfigDict(extra="forbid")

    full_name: Annotated[FullName | None, NotNull] = None
    headline: Headline = None
    biography: Biography = None
    location: Location = None
    email: EmailStr | None = None
    phone: Phone = None
    avatar_media_id: MediaId = None
    resume_media_id: MediaId = None


class SocialLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: Platform
    url: WebUrl
    display_order: DisplayOrder = 0


class SocialLinkUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: Annotated[Platform | None, NotNull] = None
    url: Annotated[WebUrl | None, NotNull] = None
    display_order: Annotated[DisplayOrder | None, NotNull] = None


class SocialLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    url: str
    display_order: int


class ProfileRead(BaseModel):
    full_name: str
    headline: str | None
    biography: str | None
    location: str | None
    email: str | None
    phone: str | None
    avatar_media_id: int | None
    avatar: PublicMedia | None
    resume_media_id: int | None
    resume: PublicMedia | None
    social_links: list[SocialLinkRead]
    updated_at: datetime
