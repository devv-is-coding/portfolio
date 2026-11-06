from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.refresh_token import RefreshToken


class User(IdMixin, TimestampMixin, Base):
    """Admin account. Only admins log in; visitors never have accounts."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True)
    # pwdlib (argon2) hash, never the password itself.
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)

    # lazy="raise": async sessions can't lazy-load, so load explicitly with
    # selectinload(User.refresh_tokens) when needed.
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user", lazy="raise", passive_deletes=True
    )
