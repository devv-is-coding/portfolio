"""Scheduled maintenance for authentication data."""

import asyncio
import logging

from app.core.database import SessionLocal, engine
from app.services.auth import cleanup_refresh_tokens as cleanup
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="auth.cleanup_refresh_tokens")
def cleanup_refresh_tokens() -> int:
    """Daily (Celery beat): delete refresh tokens that expired over a week ago."""
    deleted = asyncio.run(_cleanup())
    logger.info("Deleted %s expired refresh tokens", deleted)
    return deleted


async def _cleanup() -> int:
    try:
        async with SessionLocal() as session:
            return await cleanup(session)
    finally:
        # Each task run has its own event loop; pooled connections belong to the old one.
        await engine.dispose()
