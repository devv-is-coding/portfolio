"""Celery app. Start a worker with:  celery -A app.worker worker --loglevel=info
and the scheduler with:              celery -A app.worker beat --schedule /tmp/celerybeat-schedule

Tasks live in app/tasks/; list every task module in `include` below. Scheduled tasks
are in `beat_schedule`; exactly one beat process may run, or tasks run twice.
"""

from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging, task_postrun, task_prerun

from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_var
from app.core.sentry import init_sentry

settings = get_settings()
init_sentry(settings)

celery_app = Celery(
    "portfolio",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.auth", "app.tasks.contact", "app.tasks.media", "app.tasks.system"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    worker_concurrency=settings.celery_worker_concurrency,
    # One task at a time per process: a task waiting to retry (SMTP, ImageKit) never
    # holds back others that an idle process could run.
    worker_prefetch_multiplier=1,
    beat_schedule={
        "cleanup-refresh-tokens": {
            "task": "auth.cleanup_refresh_tokens",
            "schedule": crontab(hour=3, minute=0),  # daily, 03:00 UTC
        },
    },
)


@setup_logging.connect
def _use_app_logging(**_kwargs: object) -> None:
    """Same format and LOG_LEVEL as the API (text or JSON) instead of Celery's own."""
    configure_logging(settings)


@task_prerun.connect
def _log_with_task_id(task_id: str, **_kwargs: object) -> None:
    """Log lines written during a task carry its id where the API puts the request id."""
    request_id_var.set(task_id)


@task_postrun.connect
def _clear_task_id(**_kwargs: object) -> None:
    request_id_var.set(None)
