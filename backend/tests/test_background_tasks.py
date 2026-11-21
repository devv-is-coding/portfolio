"""Who runs background work (TASK_RUNNER) and how it fails safely after the response."""

import logging
import smtplib
import ssl
from typing import Any

import pytest
from fastapi import BackgroundTasks

from app.core.imagekit import ImageKitConfig
from app.routers.contact import get_notifier
from app.routers.media import get_file_deleter
from app.tasks import contact as contact_tasks
from app.tasks import inline as inline_tasks
from app.tasks import media as media_tasks
from app.tasks.contact import enqueue_notification, notify_admin_in_api
from app.tasks.inline import run_with_retries
from app.tasks.media import delete_file_in_api, enqueue_delete_file
from app.worker import redis_ssl_options
from tests.fakes import FakeImageKit, IsolatedSettings
from tests.test_email import CONFIG as SMTP_CONFIG
from tests.test_email import NOTIFICATION, FakeSmtp

pytestmark = pytest.mark.anyio

IMAGEKIT: dict[str, Any] = {
    "imagekit_public_key": "public_test",
    "imagekit_private_key": "private_test",
    "imagekit_url_endpoint": "https://ik.imagekit.io/portfolio",
}
SMTP: dict[str, Any] = {
    "smtp_host": "smtp.example.com",
    "smtp_from": "Portfolio <noreply@example.com>",
    "contact_notify_email": "owner@example.com",
}
NO_DELAYS = (0.0, 0.0)


class Flaky:
    """Fails with `error` the first `failures` times it's awaited, then succeeds."""

    def __init__(self, failures: int, error: Exception) -> None:
        self.failures = failures
        self.error = error
        self.calls = 0

    async def __call__(self) -> None:
        self.calls += 1
        if self.calls <= self.failures:
            raise self.error


async def test_work_that_succeeds_runs_once() -> None:
    work = Flaky(0, OSError())

    await run_with_retries(work, retry_on=(OSError,), description="Job", delays=NO_DELAYS)

    assert work.calls == 1


async def test_retryable_failures_are_retried_until_one_succeeds() -> None:
    work = Flaky(2, OSError("down"))

    await run_with_retries(work, retry_on=(OSError,), description="Job", delays=NO_DELAYS)

    assert work.calls == 3


async def test_after_the_last_attempt_the_failure_is_logged_not_raised(
    caplog: pytest.LogCaptureFixture,
) -> None:
    work = Flaky(5, OSError("down"))

    with caplog.at_level(logging.WARNING, logger="app.tasks.inline"):
        await run_with_retries(work, retry_on=(OSError,), description="Job", delays=NO_DELAYS)

    assert work.calls == 3
    assert caplog.records[-1].levelno == logging.ERROR
    assert caplog.records[-1].getMessage() == "Job failed after 3 attempts"


async def test_other_errors_are_logged_once_without_retrying(
    caplog: pytest.LogCaptureFixture,
) -> None:
    work = Flaky(5, ValueError("bug"))

    with caplog.at_level(logging.ERROR, logger="app.tasks.inline"):
        await run_with_retries(work, retry_on=(OSError,), description="Job", delays=NO_DELAYS)

    assert work.calls == 1
    assert [record.getMessage() for record in caplog.records] == ["Job failed"]


async def test_the_api_deletes_the_imagekit_file_itself() -> None:
    imagekit = FakeImageKit()
    imagekit.add_file("abc123", "/a.png", "image/png", 10, 1, 1)
    config = ImageKitConfig.from_settings(IsolatedSettings(**IMAGEKIT))

    await delete_file_in_api("abc123", config, imagekit.transport)

    assert imagekit.deleted == ["abc123"]
    assert imagekit.files == {}


async def test_the_api_sends_the_contact_email_itself() -> None:
    smtp = FakeSmtp()

    await notify_admin_in_api(NOTIFICATION, SMTP_CONFIG, smtp)

    assert ("send", "owner@example.com") in smtp.calls


async def test_a_failing_smtp_server_is_retried_and_never_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(inline_tasks, "RETRY_DELAYS", NO_DELAYS)
    attempts: list[str] = []

    def refuse(host: str, port: int, *, timeout: float) -> FakeSmtp:
        attempts.append(host)
        raise smtplib.SMTPConnectError(421, "busy")

    await notify_admin_in_api(NOTIFICATION, SMTP_CONFIG, refuse)

    assert attempts == ["smtp.example.com"] * 3


def test_celery_runner_queues_the_imagekit_deletion() -> None:
    background = BackgroundTasks()

    deleter = get_file_deleter(IsolatedSettings(**IMAGEKIT), background)

    assert deleter is enqueue_delete_file
    assert background.tasks == []


def test_api_runner_deletes_the_file_after_the_response() -> None:
    background = BackgroundTasks()
    settings = IsolatedSettings(task_runner="api", **IMAGEKIT)

    get_file_deleter(settings, background)("abc123")

    [task] = background.tasks
    assert task.func is delete_file_in_api
    assert task.args == ("abc123", ImageKitConfig.from_settings(settings))


def test_without_smtp_no_email_is_sent_whatever_the_runner() -> None:
    background = BackgroundTasks()

    assert get_notifier(IsolatedSettings(task_runner="api"), background) is None
    assert get_notifier(IsolatedSettings(), background) is None


def test_celery_runner_queues_the_contact_email() -> None:
    background = BackgroundTasks()

    assert get_notifier(IsolatedSettings(**SMTP), background) is enqueue_notification
    assert background.tasks == []


def test_api_runner_sends_the_contact_email_after_the_response() -> None:
    background = BackgroundTasks()
    notifier = get_notifier(IsolatedSettings(task_runner="api", **SMTP), background)
    assert notifier is not None

    notifier(NOTIFICATION)

    [task] = background.tasks
    assert task.func is notify_admin_in_api
    assert task.args[0] == NOTIFICATION


def test_a_broken_broker_never_fails_the_request(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    # What Celery raised in production for a rediss:// URL without certificate options.
    def misconfigured(*_args: object, **_kwargs: object) -> None:
        raise ValueError("A rediss:// URL must have parameter ssl_cert_reqs")

    monkeypatch.setattr(media_tasks.delete_file, "delay", misconfigured)
    monkeypatch.setattr(contact_tasks.notify_admin, "delay", misconfigured)

    with caplog.at_level(logging.ERROR):
        enqueue_delete_file("abc123")
        enqueue_notification(NOTIFICATION)

    assert [record.getMessage() for record in caplog.records] == [
        "Could not queue the ImageKit deletion of file abc123",
        "Could not queue the email for contact message 7",
    ]


def test_rediss_urls_verify_the_server_certificate() -> None:
    assert redis_ssl_options("rediss://default:secret@redis.example.com:6379") == {
        "ssl_cert_reqs": ssl.CERT_REQUIRED
    }
    assert redis_ssl_options("redis://localhost:6380/0") is None


def test_the_runner_is_celery_unless_set() -> None:
    assert IsolatedSettings().task_runner == "celery"
