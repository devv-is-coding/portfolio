"""Celery app. Start a worker with:  celery -A app.worker worker --loglevel=info

Tasks live in app/tasks/; list every task module in `include` below.
"""

from celery import Celery

from app.core.config import get_settings
from app.core.sentry import init_sentry

settings = get_settings()
init_sentry(settings)

celery_app = Celery(
    "portfolio",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.media", "app.tasks.system"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)
