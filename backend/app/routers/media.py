from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.core.database import SessionDep
from app.core.errors import error_responses
from app.core.imagekit import ImageKitClientDep, ImageKitConfigDep, create_upload_auth
from app.core.pagination import Page, PageParamsDep, SearchQuery, Sort, sort_query
from app.dependencies import AuditContextDep, get_current_user
from app.models.enums import MediaKind
from app.schemas.media import MediaCreate, MediaRead, MediaUpdate, UploadAuthResponse
from app.services import media as media_service
from app.tasks.media import enqueue_delete_file

UPLOAD_URL = "https://upload.imagekit.io/api/v1/files/upload"

# Router-level auth runs before every other dependency, so an anonymous request is a
# 401 even when ImageKit isn't configured.
router = APIRouter(
    prefix="/admin/media",
    tags=["media"],
    dependencies=[Depends(get_current_user)],
    responses=error_responses(401, 422, 503),
)

MediaId = Annotated[int, Path(ge=1)]
MediaSort = Annotated[
    Sort, Depends(sort_query("created_at", "size_bytes", "file_path", default="-created_at"))
]


def get_file_deleter() -> media_service.FileDeleter:
    """Queues the ImageKit deletion (Celery). Overridden in tests."""
    return enqueue_delete_file


FileDeleterDep = Annotated[media_service.FileDeleter, Depends(get_file_deleter)]


@router.get("/upload-auth")
async def upload_auth(config: ImageKitConfigDep) -> UploadAuthResponse:
    """Sign one browser upload to ImageKit (valid 30 minutes).

    The browser POSTs the file to `upload_url` with `publicKey`, `token`, `expire`,
    `signature` and `fileName`, then registers it with `POST /admin/media`.
    """
    auth = create_upload_auth(config.private_key)
    return UploadAuthResponse(
        token=auth.token,
        expire=auth.expire,
        signature=auth.signature,
        public_key=config.public_key,
        url_endpoint=config.url_endpoint,
        upload_url=UPLOAD_URL,
    )


@router.post("", status_code=status.HTTP_201_CREATED, responses=error_responses(409, 502))
async def register_media(
    body: MediaCreate,
    context: AuditContextDep,
    session: SessionDep,
    config: ImageKitConfigDep,
    imagekit: ImageKitClientDep,
) -> MediaRead:
    """Register an uploaded file. Its path, type, size and dimensions are read from
    ImageKit; only images and PDFs are accepted."""
    return await media_service.register(session, imagekit, config.url_endpoint, context, body)


@router.get("")
async def list_media(
    session: SessionDep,
    config: ImageKitConfigDep,
    page: PageParamsDep,
    sort: MediaSort,
    q: SearchQuery = None,
    kind: Annotated[MediaKind | None, Query(description="Only images or documents.")] = None,
) -> Page[MediaRead]:
    """All media files, newest first by default. `q` searches the path and alt text."""
    return await media_service.list_media(
        session, config.url_endpoint, kind=kind, q=q, sort=sort, page=page
    )


@router.get("/{media_id}", responses=error_responses(404))
async def get_media(media_id: MediaId, session: SessionDep, config: ImageKitConfigDep) -> MediaRead:
    return await media_service.get(session, config.url_endpoint, media_id)


@router.patch("/{media_id}", responses=error_responses(404))
async def update_media(
    media_id: MediaId,
    body: MediaUpdate,
    context: AuditContextDep,
    session: SessionDep,
    config: ImageKitConfigDep,
) -> MediaRead:
    """Change the alt text."""
    return await media_service.update(session, config.url_endpoint, context, media_id, body)


@router.delete(
    "/{media_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404)
)
async def delete_media(
    media_id: MediaId,
    context: AuditContextDep,
    session: SessionDep,
    delete_file: FileDeleterDep,
) -> Response:
    """Delete the file. Uses of it are cleared (avatar, thumbnail, icon, cover) or
    removed (gallery images); the file is then deleted from ImageKit in the background."""
    await media_service.delete(session, context, media_id, delete_file)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
