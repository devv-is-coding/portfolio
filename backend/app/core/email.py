"""Outgoing email over SMTP (standard library only): the new-contact-message notice.

Sending happens in the Celery worker (app/tasks/contact.py), never in a request.
"""

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr
from types import TracebackType
from typing import Protocol, Self

from app.core.config import Settings

SMTP_TIMEOUT_SECONDS = 15


class SmtpConnection(Protocol):
    """The part of `smtplib.SMTP` used here (tests pass a fake)."""

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
        /,
    ) -> None: ...
    def starttls(self) -> object: ...
    def login(self, user: str, password: str) -> object: ...
    def send_message(self, msg: EmailMessage) -> object: ...


class SmtpConnector(Protocol):
    def __call__(self, host: str, port: int, *, timeout: float) -> SmtpConnection: ...


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    username: str | None
    password: str | None
    starttls: bool
    sender: str
    recipient: str

    @classmethod
    def from_settings(cls, settings: Settings) -> "SmtpConfig | None":
        """None unless SMTP_HOST, SMTP_FROM and CONTACT_NOTIFY_EMAIL are all set."""
        if not (settings.smtp_host and settings.smtp_from and settings.contact_notify_email):
            return None
        return cls(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password.get_secret_value() if settings.smtp_password else None,
            starttls=settings.smtp_starttls,
            sender=settings.smtp_from,
            recipient=settings.contact_notify_email,
        )


@dataclass(frozen=True)
class ContactNotification:
    message_id: int
    name: str
    email: str
    subject: str | None
    message: str


def build_contact_email(config: SmtpConfig, notification: ContactNotification) -> EmailMessage:
    """The notice to the site owner; replying answers the visitor directly.

    The visitor's name and subject are single-line (the schema rejects line breaks),
    and the email package refuses to write headers containing them anyway.
    """
    email = EmailMessage()
    email["From"] = config.sender
    email["To"] = config.recipient
    email["Reply-To"] = formataddr((notification.name, notification.email))
    email["Subject"] = f"Portfolio contact: {notification.subject or notification.name}"
    email.set_content(
        f"From: {notification.name} <{notification.email}>\n"
        f"Subject: {notification.subject or '-'}\n\n"
        f"{notification.message}\n\n"
        f"(Message {notification.message_id} in the admin inbox.)\n"
    )
    return email


def send_email(
    config: SmtpConfig, email: EmailMessage, connect: SmtpConnector | None = None
) -> None:
    """Send through the configured server: STARTTLS (port 587) or implicit TLS (465).

    `connect` replaces the SMTP client in tests.
    """
    connector: SmtpConnector = connect or (smtplib.SMTP if config.starttls else smtplib.SMTP_SSL)
    with connector(config.host, config.port, timeout=SMTP_TIMEOUT_SECONDS) as smtp:
        if config.starttls:
            smtp.starttls()
        if config.username and config.password:
            smtp.login(config.username, config.password)
        smtp.send_message(email)
