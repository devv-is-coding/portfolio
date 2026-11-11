"""Background work for contact messages."""

import logging
import smtplib
from dataclasses import asdict

from kombu.exceptions import OperationalError as BrokerError

from app.core.config import get_settings
from app.core.email import ContactNotification, SmtpConfig, build_contact_email, send_email
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
    """Queue the email. If the broker is down the message is still saved in the inbox:
    log it, don't fail the visitor's request."""
    try:
        notify_admin.delay(**asdict(notification))
    except BrokerError:
        logger.exception(
            "Could not queue the email for contact message %s", notification.message_id
        )
