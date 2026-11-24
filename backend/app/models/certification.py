from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TABLE_OPTIONS, Base, IdMixin, TimestampMixin, UnsignedBigInt

if TYPE_CHECKING:
    from app.models.media import Media


class Certification(IdMixin, TimestampMixin, Base):
    __tablename__ = "certifications"
    __table_args__ = (
        CheckConstraint(
            "issued_at IS NULL OR expires_at IS NULL OR expires_at >= issued_at",
            name="expires_after_issued",
        ),
        TABLE_OPTIONS,
    )

    name: Mapped[str] = mapped_column(String(200))
    issuing_organization: Mapped[str] = mapped_column(String(200))
    credential_id: Mapped[str | None] = mapped_column(String(150))
    credential_url: Mapped[str | None] = mapped_column(String(2048))
    issued_at: Mapped[date | None] = mapped_column(Date)
    # NULL: the certification doesn't expire.
    expires_at: Mapped[date | None] = mapped_column(Date)
    # A picture of the certificate from the media library.
    image_media_id: Mapped[int | None] = mapped_column(
        UnsignedBigInt, ForeignKey("media.id", ondelete="SET NULL")
    )

    image: Mapped[Media | None] = relationship(lazy="raise")
