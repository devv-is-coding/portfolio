from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    TABLE_OPTIONS,
    Base,
    IdMixin,
    TimestampMixin,
    UnsignedBigInt,
    status_enum,
)
from app.models.enums import PublicationStatus

if TYPE_CHECKING:
    from app.models.blog_category import BlogCategory
    from app.models.blog_tag import BlogTag
    from app.models.media import Media


class BlogPost(IdMixin, TimestampMixin, Base):
    __tablename__ = "blog_posts"
    __table_args__ = (
        # Public listing: published posts, newest first.
        Index(None, "status", "published_at"),
        CheckConstraint(
            "status <> 'published' OR published_at IS NOT NULL",
            name="published_at_required",
        ),
        TABLE_OPTIONS,
    )

    # Deleting a category leaves its posts uncategorized.
    category_id: Mapped[int | None] = mapped_column(
        UnsignedBigInt, ForeignKey("blog_categories.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(280), unique=True)
    excerpt: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(LONGTEXT)
    cover_media_id: Mapped[int | None] = mapped_column(
        UnsignedBigInt, ForeignKey("media.id", ondelete="SET NULL")
    )
    status: Mapped[PublicationStatus] = mapped_column(
        status_enum(PublicationStatus),
        default=PublicationStatus.DRAFT,
        server_default=PublicationStatus.DRAFT.value,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime)

    category: Mapped[BlogCategory | None] = relationship(lazy="raise")
    cover: Mapped[Media | None] = relationship(lazy="raise")
    tags: Mapped[list[BlogTag]] = relationship(
        secondary="blog_post_tags", lazy="raise", passive_deletes=True
    )
