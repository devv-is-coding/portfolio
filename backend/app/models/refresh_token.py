from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CHAR, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TABLE_OPTIONS, Base, IdMixin, TimestampMixin, UnsignedBigInt

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(IdMixin, TimestampMixin, Base):
    """A refresh token issued at login, stored only as its SHA-256 hash.

    Rotation: using a token revokes it and issues a new one, linked by
    `replaced_by_id`. If an already-revoked token is presented again, it was stolen,
    and every token of that user can be revoked.
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        # Find a user's live tokens, and delete expired ones.
        Index(None, "user_id", "expires_at"),
        TABLE_OPTIONS,
    )

    user_id: Mapped[int] = mapped_column(UnsignedBigInt, ForeignKey("users.id", ondelete="CASCADE"))
    # Hex SHA-256 of the token: always 64 characters.
    token_hash: Mapped[str] = mapped_column(CHAR(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
    replaced_by_id: Mapped[int | None] = mapped_column(
        UnsignedBigInt, ForeignKey("refresh_tokens.id", ondelete="SET NULL")
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens", lazy="raise")
