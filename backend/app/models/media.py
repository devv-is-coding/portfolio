from sqlalchemy import String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, TimestampMixin


class Media(IdMixin, TimestampMixin, Base):
    """A file stored in ImageKit (images, and PDFs such as the resume).

    The URL is never stored: it is the ImageKit URL endpoint + `file_path`, with
    transformations added at render time (`?tr=w-800`). `file_id` is what ImageKit's
    API needs to delete or replace the file.
    """

    __tablename__ = "media"

    file_id: Mapped[str] = mapped_column(String(64), unique=True)
    file_path: Mapped[str] = mapped_column(String(1024))
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(INTEGER(unsigned=True))
    # Images only; lets next/image reserve space and avoid layout shift.
    width: Mapped[int | None] = mapped_column(INTEGER(unsigned=True))
    height: Mapped[int | None] = mapped_column(INTEGER(unsigned=True))
    # Default alt text; a use (e.g. project_images.alt_text) can override it.
    alt_text: Mapped[str | None] = mapped_column(String(255))
