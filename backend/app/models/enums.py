"""Enums shared by models, services and API schemas."""

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


class MediaKind(StrEnum):
    """What a media file is, derived from its MIME type (see app/models/media.py)."""

    IMAGE = "image"
    DOCUMENT = "document"
