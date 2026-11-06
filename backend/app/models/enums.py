"""Status values shared by models and API schemas (stored via `status_enum`)."""

from enum import StrEnum


class PublicationStatus(StrEnum):
    """Projects and blog posts. `archived` hides a row instead of deleting it."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContactMessageStatus(StrEnum):
    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"
