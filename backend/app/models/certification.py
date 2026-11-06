from datetime import date

from sqlalchemy import CheckConstraint, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TABLE_OPTIONS, Base, IdMixin, TimestampMixin


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
