"""The Celery app: registered tasks, the beat schedule and log lines with task ids."""

import logging

import pytest
from celery.schedules import crontab

from app.core.logging import request_id_var
from app.worker import _clear_task_id, _log_with_task_id, _use_app_logging, celery_app


@pytest.fixture(autouse=True)
def _tasks_loaded() -> None:
    """Import the `include` modules, as a starting worker or beat does."""
    celery_app.loader.import_default_modules()


def test_every_task_module_is_included() -> None:
    assert celery_app.conf.include == [
        "app.tasks.auth",
        "app.tasks.contact",
        "app.tasks.media",
        "app.tasks.system",
    ]


def test_refresh_tokens_are_cleaned_up_daily() -> None:
    entry = celery_app.conf.beat_schedule["cleanup-refresh-tokens"]

    assert entry["task"] == "auth.cleanup_refresh_tokens"
    assert entry["task"] in celery_app.tasks
    assert entry["schedule"] == crontab(hour=3, minute=0)


def test_every_scheduled_task_exists() -> None:
    for name, entry in celery_app.conf.beat_schedule.items():
        assert entry["task"] in celery_app.tasks, name


def test_task_log_lines_use_the_app_format_with_the_task_id() -> None:
    _use_app_logging()
    [handler] = logging.getLogger().handlers
    logger = logging.getLogger("app.tasks.test")

    _log_with_task_id(task_id="task-123")
    during = handler.format(
        logger.makeRecord(logger.name, logging.INFO, __file__, 1, "hi", (), None)
    )
    _clear_task_id()
    after = handler.format(
        logger.makeRecord(logger.name, logging.INFO, __file__, 1, "hi", (), None)
    )

    assert "INFO [task-123] app.tasks.test: hi" in during
    assert "[-]" in after
    assert request_id_var.get() is None


def test_each_process_takes_one_task_at_a_time() -> None:
    assert celery_app.conf.worker_prefetch_multiplier == 1
