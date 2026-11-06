from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin, UnsignedBigInt

if TYPE_CHECKING:
    from app.models.media import Media


class Skill(IdMixin, TimestampMixin, Base):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    # e.g. "frontend", "backend", "devops"; free text, grouped by the frontend.
    category: Mapped[str | None] = mapped_column(String(100))
    icon_media_id: Mapped[int | None] = mapped_column(
        UnsignedBigInt, ForeignKey("media.id", ondelete="SET NULL")
    )
    display_order: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    icon: Mapped[Media | None] = relationship(lazy="raise")
