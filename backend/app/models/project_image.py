from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin, UnsignedBigInt

if TYPE_CHECKING:
    from app.models.media import Media
    from app.models.project import Project


class ProjectImage(IdMixin, TimestampMixin, Base):
    """A screenshot in a project's gallery."""

    __tablename__ = "project_images"

    project_id: Mapped[int] = mapped_column(
        UnsignedBigInt, ForeignKey("projects.id", ondelete="CASCADE")
    )
    # Deleting the media file removes it from every gallery.
    media_id: Mapped[int] = mapped_column(
        UnsignedBigInt, ForeignKey("media.id", ondelete="CASCADE")
    )
    # Overrides media.alt_text for this project.
    alt_text: Mapped[str | None] = mapped_column(String(255))
    display_order: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    project: Mapped[Project] = relationship(back_populates="images", lazy="raise")
    media: Mapped[Media] = relationship(lazy="raise")
