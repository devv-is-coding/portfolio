from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin, UnsignedBigInt

if TYPE_CHECKING:
    from app.models.media import Media
    from app.models.social_link import SocialLink


class Profile(IdMixin, TimestampMixin, Base):
    """The portfolio owner's public details. A single row; the API treats it as one record."""

    __tablename__ = "profiles"

    full_name: Mapped[str] = mapped_column(String(150))
    headline: Mapped[str | None] = mapped_column(String(255))
    biography: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(150))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30))
    avatar_media_id: Mapped[int | None] = mapped_column(
        UnsignedBigInt, ForeignKey("media.id", ondelete="SET NULL")
    )
    resume_media_id: Mapped[int | None] = mapped_column(
        UnsignedBigInt, ForeignKey("media.id", ondelete="SET NULL")
    )

    avatar: Mapped[Media | None] = relationship(foreign_keys=[avatar_media_id], lazy="raise")
    resume: Mapped[Media | None] = relationship(foreign_keys=[resume_media_id], lazy="raise")
    social_links: Mapped[list[SocialLink]] = relationship(
        back_populates="profile",
        lazy="raise",
        passive_deletes=True,
        order_by="SocialLink.display_order",
    )
