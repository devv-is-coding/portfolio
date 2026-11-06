from datetime import date

from sqlalchemy import CheckConstraint, Date, String, text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TABLE_OPTIONS, Base, IdMixin, TimestampMixin


class Experience(IdMixin, TimestampMixin, Base):
    """A job. `end_date IS NULL` means it is the current one (no separate is_current flag)."""

    __tablename__ = "experiences"
    __table_args__ = (
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="end_date_after_start"),
        TABLE_OPTIONS,
    )

    company: Mapped[str] = mapped_column(String(200))
    position: Mapped[str] = mapped_column(String(200))
    # e.g. "full-time", "contract", "freelance".
    employment_type: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(LONGTEXT)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    display_order: Mapped[int] = mapped_column(default=0, server_default=text("0"))
