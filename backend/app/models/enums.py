"""Enums shared by models, services and API schemas.

Status enums are stored as TINYINT codes (app/models/base.py, `status_column`); the
`*_CODES` mappings below fix those numbers. Never renumber a member: stored rows keep
their numbers.
"""

from collections.abc import Mapping
from enum import StrEnum
from typing import Final


class PublicationStatus(StrEnum):
    """Projects and blog posts. `archived` hides a row instead of deleting it."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


PUBLICATION_STATUS_CODES: Final[Mapping[PublicationStatus, int]] = {
    PublicationStatus.DRAFT: 0,
    PublicationStatus.PUBLISHED: 1,
    PublicationStatus.ARCHIVED: 2,
}


class ContactMessageStatus(StrEnum):
    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"


CONTACT_MESSAGE_STATUS_CODES: Final[Mapping[ContactMessageStatus, int]] = {
    ContactMessageStatus.UNREAD: 0,
    ContactMessageStatus.READ: 1,
    ContactMessageStatus.REPLIED: 2,
    ContactMessageStatus.ARCHIVED: 3,
}


class MediaKind(StrEnum):
    """What a media file is, derived from its MIME type (see app/models/media.py)."""

    IMAGE = "image"
    DOCUMENT = "document"
