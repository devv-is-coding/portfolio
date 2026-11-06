from typing import Any

from sqlalchemy import JSON, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TABLE_OPTIONS, Base, IdMixin, TimestampMixin, UnsignedBigInt


class AuditLog(IdMixin, TimestampMixin, Base):
    """An admin action (`project.update`). Append-only: rows are never updated."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        # History of one record: entity_type="project", entity_id=42.
        Index(None, "entity_type", "entity_id"),
        TABLE_OPTIONS,
    )

    # Kept when the user is deleted, so the history survives.
    user_id: Mapped[int | None] = mapped_column(
        UnsignedBigInt, ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str | None] = mapped_column(String(100))
    # No foreign key: it points at a row of whichever table entity_type names.
    entity_id: Mapped[int | None] = mapped_column(UnsignedBigInt)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
