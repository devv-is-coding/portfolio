"""ImageKit: upload signing, the file REST API and file URLs.

The browser uploads files straight to ImageKit (https://upload.imagekit.io/api/v1/files/upload)
with a short-lived signature from `GET /admin/media/upload-auth`, so file bytes never pass
through the API. The API only talks to ImageKit's REST API, over HTTPX with Basic auth
(private key as user name, empty password); no ImageKit SDK is needed. The contracts
below match ImageKit's official SDK (imagekitio 4.x).
"""

import hashlib
import hmac
import logging
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated, Self
from urllib.parse import quote

import httpx
from fastapi import Depends
from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings, SettingsDep
from app.core.errors import ServiceUnavailableError, UpstreamError

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.imagekit.io/v1"
# ImageKit rejects an `expire` more than 1 hour ahead; the official SDK uses 30 minutes.
UPLOAD_AUTH_TTL_SECONDS = 30 * 60
REQUEST_TIMEOUT_SECONDS = 10.0


class ImageKitNotConfiguredError(ServiceUnavailableError):
    default_message = "Media uploads are not configured"


class ImageKitUnavailableError(UpstreamError):
    default_message = "ImageKit is unavailable, try again later"


@dataclass(frozen=True)
class ImageKitConfig:
    public_key: str
    private_key: str
    url_endpoint: str

    @classmethod
    def from_settings(cls, settings: Settings) -> Self:
        if not (
            settings.imagekit_public_key
            and settings.imagekit_private_key
            and settings.imagekit_url_endpoint
        ):
            raise ImageKitNotConfiguredError
        return cls(
            public_key=settings.imagekit_public_key,
            private_key=settings.imagekit_private_key.get_secret_value(),
            url_endpoint=settings.imagekit_url_endpoint.rstrip("/"),
        )


@dataclass(frozen=True)
class UploadAuth:
    token: str
    expire: int
    signature: str


def sign_upload(private_key: str, *, token: str, expire: int) -> str:
    """HMAC-SHA1 of `token + expire`, keyed with the private key, as hex."""
    message = f"{token}{expire}".encode()
    return hmac.new(private_key.encode(), message, hashlib.sha1).hexdigest()


def create_upload_auth(private_key: str, *, now: float | None = None) -> UploadAuth:
    """A one-time token, valid for UPLOAD_AUTH_TTL_SECONDS, and its signature."""
    token = str(uuid.uuid4())
    expire = int(time.time() if now is None else now) + UPLOAD_AUTH_TTL_SECONDS
    return UploadAuth(token, expire, sign_upload(private_key, token=token, expire=expire))


def file_url(url_endpoint: str, file_path: str) -> str:
    """Public URL of a file: the URL endpoint + its path (transformations are added
    by the frontend, e.g. `?tr=w-800`)."""
    path = file_path if file_path.startswith("/") else f"/{file_path}"
    return f"{url_endpoint.rstrip('/')}{quote(path, safe='/')}"


@dataclass(frozen=True)
class FileDetails:
    file_id: str
    file_path: str
    mime_type: str
    size_bytes: int
    width: int | None
    height: int | None


class _FilePayload(BaseModel):
    """The fields we use from ImageKit's file object (camelCase in the API)."""

    file_id: str = Field(alias="fileId")
    file_path: str = Field(alias="filePath")
    mime: str
    size: int = Field(ge=0)
    width: int | None = None
    height: int | None = None


class ImageKitClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def get_file_details(self, file_id: str) -> FileDetails | None:
        """The file as ImageKit stores it, or None when it doesn't exist."""
        response = await self._request("GET", f"/files/{quote(file_id, safe='')}/details")
        if response.status_code == httpx.codes.NOT_FOUND:
            return None
        try:
            payload = _FilePayload.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            logger.warning("Unexpected ImageKit file details for %s", file_id)
            raise ImageKitUnavailableError from exc
        return FileDetails(
            file_id=payload.file_id,
            file_path=payload.file_path,
            mime_type=payload.mime,
            size_bytes=payload.size,
            # Non-images report no (or zero) dimensions.
            width=payload.width or None,
            height=payload.height or None,
        )

    async def delete_file(self, file_id: str) -> None:
        """Delete the file. A file that is already gone counts as deleted."""
        await self._request("DELETE", f"/files/{quote(file_id, safe='')}")

    async def _request(self, method: str, path: str) -> httpx.Response:
        try:
            response = await self._http.request(method, path)
        except httpx.HTTPError as exc:
            logger.warning("ImageKit %s %s failed: %s", method, path, type(exc).__name__)
            raise ImageKitUnavailableError from exc
        if response.is_error and response.status_code != httpx.codes.NOT_FOUND:
            logger.warning("ImageKit %s %s answered %s", method, path, response.status_code)
            raise ImageKitUnavailableError
        return response


def create_http_client(
    config: ImageKitConfig, transport: httpx.AsyncBaseTransport | None = None
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=API_BASE_URL,
        auth=httpx.BasicAuth(config.private_key, ""),
        timeout=REQUEST_TIMEOUT_SECONDS,
        transport=transport,
    )


def get_media_url_endpoint(settings: SettingsDep) -> str | None:
    """Only the URL endpoint, for reads that show media: pages without media still
    work when ImageKit isn't configured."""
    endpoint = settings.imagekit_url_endpoint
    return endpoint.rstrip("/") if endpoint else None


MediaUrlEndpointDep = Annotated[str | None, Depends(get_media_url_endpoint)]


def get_imagekit_config(settings: SettingsDep) -> ImageKitConfig:
    """503 (`ImageKitNotConfiguredError`) when the IMAGEKIT_* settings are missing."""
    return ImageKitConfig.from_settings(settings)


ImageKitConfigDep = Annotated[ImageKitConfig, Depends(get_imagekit_config)]


async def get_imagekit_client(config: ImageKitConfigDep) -> AsyncIterator[ImageKitClient]:
    async with create_http_client(config) as http:
        yield ImageKitClient(http)


ImageKitClientDep = Annotated[ImageKitClient, Depends(get_imagekit_client)]
