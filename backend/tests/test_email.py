from dataclasses import replace
from email.message import EmailMessage
from typing import Self

import pytest
from pydantic import SecretStr

from app.core.email import ContactNotification, SmtpConfig, build_contact_email, send_email
from app.worker import celery_app
from tests.fakes import IsolatedSettings

CONFIG = SmtpConfig(
    host="smtp.example.com",
    port=587,
    username="user",
    password="app-password",
    starttls=True,
    sender="Portfolio <noreply@example.com>",
    recipient="owner@example.com",
)
NOTIFICATION = ContactNotification(7, "Ada Lovelace", "ada@example.com", "Job offer", "Hello!")


class FakeSmtp:
    """Records the SMTP conversation instead of opening a connection."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def __call__(self, host: str, port: int, *, timeout: float) -> Self:
        self.calls.append(("connect", (host, port, timeout)))
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.calls.append(("quit", None))

    def starttls(self) -> None:
        self.calls.append(("starttls", None))

    def login(self, user: str, password: str) -> None:
        self.calls.append(("login", (user, password)))

    def send_message(self, msg: EmailMessage) -> None:
        self.calls.append(("send", msg["To"]))


def test_config_needs_host_sender_and_recipient() -> None:
    complete = IsolatedSettings(
        smtp_host="smtp.example.com",
        smtp_from="noreply@example.com",
        contact_notify_email="owner@example.com",
        smtp_password=SecretStr("app-password"),
    )

    assert SmtpConfig.from_settings(IsolatedSettings()) is None
    assert SmtpConfig.from_settings(complete.model_copy(update={"smtp_from": None})) is None
    config = SmtpConfig.from_settings(complete)
    assert config is not None
    assert (config.host, config.port, config.password) == ("smtp.example.com", 587, "app-password")


def test_the_notice_replies_to_the_visitor() -> None:
    email = build_contact_email(CONFIG, NOTIFICATION)

    assert email["From"] == "Portfolio <noreply@example.com>"
    assert email["To"] == "owner@example.com"
    assert email["Reply-To"] == "Ada Lovelace <ada@example.com>"
    assert email["Subject"] == "Portfolio contact: Job offer"
    assert "Hello!" in email.get_content()
    assert "Message 7" in email.get_content()


def test_without_a_subject_the_name_is_used() -> None:
    email = build_contact_email(CONFIG, ContactNotification(1, "Ada", "a@example.com", None, "x"))

    assert email["Subject"] == "Portfolio contact: Ada"


def test_line_breaks_in_headers_are_refused() -> None:
    notification = ContactNotification(1, "Ada", "a@example.com", "Hi\r\nBcc: x@example.com", "x")

    with pytest.raises(ValueError):
        build_contact_email(CONFIG, notification).as_string()


@pytest.mark.parametrize(
    ("starttls", "username", "expected"),
    [
        (True, "user", ["connect", "starttls", "login", "send", "quit"]),
        (False, "user", ["connect", "login", "send", "quit"]),
        (True, None, ["connect", "starttls", "send", "quit"]),
    ],
)
def test_send_email_conversation(starttls: bool, username: str | None, expected: list[str]) -> None:
    smtp = FakeSmtp()
    config = replace(CONFIG, starttls=starttls, username=username)

    send_email(config, build_contact_email(config, NOTIFICATION), connect=smtp)

    assert [name for name, _ in smtp.calls] == expected
    assert smtp.calls[0] == ("connect", ("smtp.example.com", 587, 15))


def test_notify_task_is_registered_and_retries_smtp_failures() -> None:
    assert "app.tasks.contact" in celery_app.conf.include
    options = vars(type(celery_app.tasks["contact.notify_admin"]))
    assert OSError in options["autoretry_for"]
    assert options["max_retries"] == 5
