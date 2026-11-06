from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin, UnsignedBigInt

if TYPE_CHECKING:
    from app.models.profile import Profile


class SocialLink(IdMixin, TimestampMixin, Base):
    __tablename__ = "social_links"

    profile_id: Mapped[int] = mapped_column(
        UnsignedBigInt, ForeignKey("profiles.id", ondelete="CASCADE")
    )
    # e.g. "github", "linkedin"; the frontend maps it to an icon.
    platform: Mapped[str] = mapped_column(String(50))
    url: Mapped[str] = mapped_column(String(2048))
    display_order: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    profile: Mapped[Profile] = relationship(back_populates="social_links", lazy="raise")
