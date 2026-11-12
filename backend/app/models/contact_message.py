from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TABLE_OPTIONS, Base, IdMixin, TimestampMixin, status_column
from app.models.enums import CONTACT_MESSAGE_STATUS_CODES, ContactMessageStatus


class ContactMessage(IdMixin, TimestampMixin, Base):
    """A message from the public contact form."""

    __tablename__ = "contact_messages"
    __table_args__ = (
        # Admin inbox: newest first, with or without a status filter.
        Index(None, "status", "created_at"),
        Index(None, "created_at"),
        TABLE_OPTIONS,
    )

    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[ContactMessageStatus] = status_column(
        CONTACT_MESSAGE_STATUS_CODES, default=ContactMessageStatus.UNREAD
    )
    # Sender's IP (IPv6 fits in 45 characters), for spam rate limiting.
    ip_address: Mapped[str | None] = mapped_column(String(45))
