from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, false, text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    TABLE_OPTIONS,
    Base,
    IdMixin,
    TimestampMixin,
    UnsignedBigInt,
    status_column,
)
from app.models.enums import PUBLICATION_STATUS_CODES, PublicationStatus

if TYPE_CHECKING:
    from app.models.media import Media
    from app.models.project_image import ProjectImage
    from app.models.skill import Skill


class Project(IdMixin, TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        # Public listing: published projects, newest first.
        Index(None, "status", "published_at"),
        CheckConstraint(
            f"status <> {PUBLICATION_STATUS_CODES[PublicationStatus.PUBLISHED]}"
            " OR published_at IS NOT NULL",
            name="published_at_required",
        ),
        TABLE_OPTIONS,
    )

    title: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(220), unique=True)
    short_description: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(LONGTEXT)
    thumbnail_media_id: Mapped[int | None] = mapped_column(
        UnsignedBigInt, ForeignKey("media.id", ondelete="SET NULL")
    )
    live_url: Mapped[str | None] = mapped_column(String(2048))
    repository_url: Mapped[str | None] = mapped_column(String(2048))
    status: Mapped[PublicationStatus] = status_column(
        PUBLICATION_STATUS_CODES, default=PublicationStatus.DRAFT
    )
    is_featured: Mapped[bool] = mapped_column(default=False, server_default=false())
    display_order: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime)

    thumbnail: Mapped[Media | None] = relationship(lazy="raise")
    images: Mapped[list[ProjectImage]] = relationship(
        back_populates="project",
        lazy="raise",
        # Loaded images are deleted with the project, not orphaned (project_id is NOT NULL).
        cascade="all, delete-orphan",
        passive_deletes=True,
        # Stable order for images with the same display_order.
        order_by="(ProjectImage.display_order, ProjectImage.id)",
    )
    skills: Mapped[list[Skill]] = relationship(
        secondary="project_skills",
        lazy="raise",
        passive_deletes=True,
        order_by="(Skill.display_order, Skill.id)",
    )
