"""Media files: registering ImageKit uploads, listing, alt text and deleting."""

from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationFailedError
from app.core.imagekit import ImageKitClient, ImageKitNotConfiguredError, file_url
from app.core.pagination import Page, PageParams, Sort
from app.models import Media
from app.models.enums import MediaKind
from app.models.media import media_kind
from app.repositories.media import MediaRepository
from app.schemas.errors import ErrorDetail
from app.schemas.media import MediaCreate, MediaRead, MediaUpdate, PublicMedia
from app.services import audit
from app.services.audit import AuditContext

ENTITY_TYPE = "media"

type FileDeleter = Callable[[str], None]


class MediaNotFoundError(NotFoundError):
    default_message = "Media not found"


class MediaAlreadyRegisteredError(ConflictError):
    default_message = "This file is already registered"


def to_read(media: Media, url_endpoint: str) -> MediaRead:
    kind = media_kind(media.mime_type)
    if kind is None:  # only accepted types are ever stored (see register)
        raise ValueError(f"media {media.id} has an unsupported MIME type")
    return MediaRead(
        id=media.id,
        url=file_url(url_endpoint, media.file_path),
        kind=kind,
        file_id=media.file_id,
        file_path=media.file_path,
        mime_type=media.mime_type,
        size_bytes=media.size_bytes,
        width=media.width,
        height=media.height,
        alt_text=media.alt_text,
        created_at=media.created_at,
        updated_at=media.updated_at,
    )


def to_public(media: Media | None, url_endpoint: str | None) -> PublicMedia | None:
    """A referenced file for public pages (None when nothing is referenced)."""
    if media is None:
        return None
    if url_endpoint is None:
        raise ImageKitNotConfiguredError
    return PublicMedia(
        url=file_url(url_endpoint, media.file_path),
        mime_type=media.mime_type,
        width=media.width,
        height=media.height,
        alt_text=media.alt_text,
    )


async def require_media(session: AsyncSession, media_id: int, kind: MediaKind, field: str) -> None:
    """422 on `body.<field>` unless media `media_id` exists and is of `kind`
    (e.g. an avatar must be an image, a resume a document)."""
    media = await MediaRepository(session).get(media_id)
    if media is None:
        message = "No media with this id"
    elif media_kind(media.mime_type) is not kind:
        message = f"Must be {'an image' if kind is MediaKind.IMAGE else 'a PDF document'}"
    else:
        return
    raise ValidationFailedError(
        details=[ErrorDetail(field=f"body.{field}", message=message, type="invalid_media")]
    )


def _invalid_file(message: str) -> ValidationFailedError:
    return ValidationFailedError(
        details=[ErrorDetail(field="body.file_id", message=message, type="invalid_file")]
    )


async def register(
    session: AsyncSession,
    imagekit: ImageKitClient,
    url_endpoint: str,
    context: AuditContext,
    body: MediaCreate,
) -> MediaRead:
    """Store a file the browser uploaded. Its path, type, size and dimensions come
    from ImageKit itself, never from the client."""
    media_repo = MediaRepository(session)
    if await media_repo.get_by_file_id(body.file_id) is not None:
        raise MediaAlreadyRegisteredError
    details = await imagekit.get_file_details(body.file_id)
    if details is None:
        raise _invalid_file("No ImageKit file with this id")
    if media_kind(details.mime_type) is None:
        raise _invalid_file(f"Unsupported file type {details.mime_type}: use an image or a PDF")

    media = Media(
        file_id=details.file_id,
        file_path=details.file_path,
        mime_type=details.mime_type,
        size_bytes=details.size_bytes,
        width=details.width,
        height=details.height,
        alt_text=body.alt_text,
    )
    media_repo.add(media)
    await media_repo.flush()
    audit.record(
        session,
        context,
        "media.create",
        entity_type=ENTITY_TYPE,
        entity_id=media.id,
        details={"file_id": media.file_id, "file_path": media.file_path},
    )
    await session.commit()
    await session.refresh(media)  # server-set timestamps
    return to_read(media, url_endpoint)


async def list_media(
    session: AsyncSession,
    url_endpoint: str,
    *,
    kind: MediaKind | None,
    q: str | None,
    sort: Sort,
    page: PageParams,
) -> Page[MediaRead]:
    items, total = await MediaRepository(session).search(kind=kind, q=q, sort=sort, page=page)
    return Page.create([to_read(media, url_endpoint) for media in items], total, page)


async def _get(session: AsyncSession, media_id: int) -> Media:
    media = await MediaRepository(session).get(media_id)
    if media is None:
        raise MediaNotFoundError
    return media


async def get(session: AsyncSession, url_endpoint: str, media_id: int) -> MediaRead:
    return to_read(await _get(session, media_id), url_endpoint)


async def update(
    session: AsyncSession,
    url_endpoint: str,
    context: AuditContext,
    media_id: int,
    body: MediaUpdate,
) -> MediaRead:
    """Change the alt text. Only fields sent in the request change (PATCH)."""
    media = await _get(session, media_id)
    diff = audit.apply_changes(media, body.model_dump(exclude_unset=True))
    if diff:
        audit.record(
            session,
            context,
            "media.update",
            entity_type=ENTITY_TYPE,
            entity_id=media.id,
            details=diff,
        )
        await session.commit()
        await session.refresh(media)
    return to_read(media, url_endpoint)


async def delete(
    session: AsyncSession, context: AuditContext, media_id: int, delete_file: FileDeleter
) -> None:
    """Delete the row (references are cleared or removed by the database rules), then
    queue the deletion in ImageKit, only once the row is really gone."""
    media_repo = MediaRepository(session)
    media = await _get(session, media_id)
    file_id, file_path = media.file_id, media.file_path
    await media_repo.delete(media)
    audit.record(
        session,
        context,
        "media.delete",
        entity_type=ENTITY_TYPE,
        entity_id=media_id,
        details={"file_id": file_id, "file_path": file_path},
    )
    await session.commit()
    delete_file(file_id)
