"""Background work for contact messages."""

import asyncio
import logging
import smtplib
from dataclasses import asdict

from app.core.config import get_settings
from app.core.email import (
    ContactNotification,
    SmtpConfig,
    SmtpConnector,
    build_contact_email,
    send_email,
)
from app.tasks.inline import run_with_retries
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="contact.notify_admin",
    autoretry_for=(smtplib.SMTPException, OSError),
    retry_backoff=True,  # 1s, 2s, 4s, ... with jitter
    retry_backoff_max=600,
    max_retries=5,
)
def notify_admin(message_id: int, name: str, email: str, subject: str | None, message: str) -> None:
    """Email the site owner about a new contact message."""
    config = SmtpConfig.from_settings(get_settings())
    if config is None:
        logger.warning("Contact message %s: SMTP is not configured, no email sent", message_id)
        return
    notification = ContactNotification(message_id, name, email, subject, message)
    send_email(config, build_contact_email(config, notification))


def enqueue_notification(notification: ContactNotification) -> None:
    """Queue the email. The message is already saved in the inbox, so whatever goes wrong
    here (broker down, broker misconfigured): log it, never fail the visitor's request."""
    try:
        notify_admin.delay(**asdict(notification))
    except Exception:
        logger.exception(
            "Could not queue the email for contact message %s", notification.message_id
        )


async def notify_admin_in_api(
    notification: ContactNotification, config: SmtpConfig, connect: SmtpConnector | None = None
) -> None:
    """The email, sent by the API after the response (TASK_RUNNER=api). smtplib blocks, so
    it runs in a thread."""
    email = build_contact_email(config, notification)
    await run_with_retries(
        lambda: asyncio.to_thread(send_email, config, email, connect),
        retry_on=(smtplib.SMTPException, OSError),
        description=f"Email for contact message {notification.message_id}",
    )
