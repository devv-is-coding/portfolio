from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.models.enums import MediaKind
from app.schemas.fields import BlankToNone

AltText = Annotated[
    str | None,
    Field(max_length=255, description="Describes the image for screen readers."),
    BlankToNone,
]


class PublicMedia(BaseModel):
    """A media file as public pages show it."""

    url: str = Field(description="Public ImageKit URL; add transformations such as `?tr=w-800`.")
    mime_type: str
    width: int | None
    height: int | None
    alt_text: str | None


class UploadAuthResponse(BaseModel):
    """Everything the browser needs to upload one file to ImageKit."""

    token: str = Field(description="One-time token; send it as `token`.")
    expire: int = Field(description="Unix time (seconds) when the signature stops working.")
    signature: str
    public_key: str
    url_endpoint: str = Field(description="Base URL of uploaded files.")
    upload_url: str = Field(description="Where the browser POSTs the file (multipart).")


class MediaCreate(BaseModel):
    """Register a file the browser has just uploaded to ImageKit."""

    file_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="`fileId` from ImageKit's upload response.",
        examples=["6745dd8e432c476416dfe3f0"],
    )
    alt_text: AltText = None


class MediaUpdate(BaseModel):
    alt_text: AltText = None


class MediaRead(BaseModel):
    id: int
    url: str = Field(description="Public ImageKit URL; add transformations such as `?tr=w-800`.")
    kind: MediaKind
    file_id: str
    file_path: str
    mime_type: str
    size_bytes: int
    width: int | None
    height: int | None
    alt_text: str | None
    created_at: datetime
    updated_at: datetime
