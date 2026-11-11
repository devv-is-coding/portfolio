"""Background work for media files."""

import asyncio
import logging

import httpx
from kombu.exceptions import OperationalError as BrokerError

from app.core.config import get_settings
from app.core.imagekit import (
    ImageKitClient,
    ImageKitConfig,
    ImageKitUnavailableError,
    create_http_client,
)
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="media.delete_file",
    autoretry_for=(ImageKitUnavailableError,),
    retry_backoff=True,  # 1s, 2s, 4s, ... with jitter
    retry_backoff_max=600,
    max_retries=10,
)
def delete_file(file_id: str) -> None:
    """Delete a file from ImageKit after its media row was deleted."""
    config = ImageKitConfig.from_settings(get_settings())
    asyncio.run(delete_file_from_imagekit(file_id, config))


async def delete_file_from_imagekit(
    file_id: str, config: ImageKitConfig, transport: httpx.AsyncBaseTransport | None = None
) -> None:
    async with create_http_client(config, transport) as http:
        await ImageKitClient(http).delete_file(file_id)


def enqueue_delete_file(file_id: str) -> None:
    """Queue the ImageKit deletion. If the broker is down, the file stays in ImageKit
    (the database row is already gone): log it, don't fail the request."""
    try:
        delete_file.delay(file_id)
    except BrokerError:
        logger.exception("Could not queue the ImageKit deletion of file %s", file_id)
