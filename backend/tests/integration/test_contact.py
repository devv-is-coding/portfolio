from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.email import ContactNotification
from app.main import app
from app.models import ContactMessage
from app.routers.contact import get_notifier
from tests.integration.factories import audit_entries

pytestmark = pytest.mark.anyio

MESSAGE = {"name": "Ada", "email": "ada@example.com", "subject": "Hi", "message": "Hello!"}


@pytest.fixture
def sent() -> list[ContactNotification]:
    return []


@pytest.fixture
async def client(api: AsyncClient, sent: list[ContactNotification]) -> AsyncIterator[AsyncClient]:
    """Notifications are recorded instead of queued; at most 3 messages per IP."""
    app.dependency_overrides[get_notifier] = lambda: sent.append
    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={"contact_max_messages": 3, "contact_window_seconds": 600}
    )
    yield api


async def _stored(session: AsyncSession) -> list[ContactMessage]:
    return list((await session.scalars(select(ContactMessage).order_by(ContactMessage.id))).all())


# --- public form -----------------------------------------------------------------------


async def test_a_message_is_stored_and_notified_without_echoing_data(
    client: AsyncClient, db_session: AsyncSession, sent: list[ContactNotification]
) -> None:
    response = await client.post("/contact", json=MESSAGE | {"subject": "  "})

    assert (response.status_code, response.content) == (202, b"")
    [message] = await _stored(db_session)
    assert (message.name, message.subject, message.status.value) == ("Ada", None, "unread")
    assert message.ip_address == "127.0.0.1"
    assert sent == [ContactNotification(message.id, "Ada", "ada@example.com", None, "Hello!")]


async def test_without_smtp_the_message_is_still_stored(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    app.dependency_overrides[get_notifier] = lambda: None

    response = await api.post("/contact", json=MESSAGE)

    assert response.status_code == 202
    assert len(await _stored(db_session)) == 1


async def test_a_filled_spam_trap_looks_accepted_but_nothing_is_kept(
    client: AsyncClient, db_session: AsyncSession, sent: list[ContactNotification]
) -> None:
    response = await client.post("/contact", json=MESSAGE | {"website": "http://spam.example"})

    assert response.status_code == 202
    assert await _stored(db_session) == []
    assert sent == []


@pytest.mark.parametrize(
    ("fields", "field"),
    [
        ({"name": "Ada\r\nBcc: victim@example.com"}, "body.name"),
        ({"subject": "Hi\nBcc: victim@example.com"}, "body.subject"),
        ({"email": "not-an-email"}, "body.email"),
        ({"message": " "}, "body.message"),
        ({"message": "x" * 5001}, "body.message"),
        ({"name": "x" * 151}, "body.name"),
        ({"phone": "123"}, "body.phone"),
    ],
)
async def test_the_form_is_validated(
    client: AsyncClient, db_session: AsyncSession, fields: dict[str, object], field: str
) -> None:
    response = await client.post("/contact", json=MESSAGE | fields)

    assert response.status_code == 422
    assert [detail["field"] for detail in response.json()["error"]["details"]] == [field]
    assert await _stored(db_session) == []


async def test_too_many_messages_from_one_ip_are_429(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    statuses = [(await client.post("/contact", json=MESSAGE)).status_code for _ in range(3)]
    spam = await client.post("/contact", json=MESSAGE | {"website": "x"})
    limited = await client.post("/contact", json=MESSAGE)

    assert statuses == [202, 202, 202]
    assert (spam.status_code, limited.status_code) == (429, 429)
    assert limited.headers["Retry-After"] == "600"
    assert limited.json()["error"]["code"] == "rate_limited"
    assert len(await _stored(db_session)) == 3


# --- admin inbox -----------------------------------------------------------------------


async def test_inbox_lists_newest_first_filters_and_searches(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    for name in ("Ada", "Grace", "Linus"):
        await client.post("/contact", json=MESSAGE | {"name": name})
    newest = (await client.get("/admin/contact-messages", headers=admin_headers)).json()
    await client.patch(
        f"/admin/contact-messages/{newest['items'][0]['id']}",
        json={"status": "read"},
        headers=admin_headers,
    )

    async def names(query: str) -> list[str]:
        url = f"/admin/contact-messages?{query}"
        return [m["name"] for m in (await client.get(url, headers=admin_headers)).json()["items"]]

    assert [m["name"] for m in newest["items"]] == ["Linus", "Grace", "Ada"]
    assert await names("status=unread") == ["Grace", "Ada"]
    assert await names("q=grac") == ["Grace"]
    assert await names("sort=name") == ["Ada", "Grace", "Linus"]


async def test_read_update_delete_and_audit(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    await client.post("/contact", json=MESSAGE)
    [message] = await _stored(db_session)
    url = f"/admin/contact-messages/{message.id}"

    fetched = await client.get(url, headers=admin_headers)
    replied = await client.patch(url, json={"status": "replied"}, headers=admin_headers)
    invalid = [
        await client.patch(url, json={"status": None}, headers=admin_headers),
        await client.patch(url, json={"status": "spam"}, headers=admin_headers),
    ]
    deleted = await client.delete(url, headers=admin_headers)
    missing = [
        await client.get(url, headers=admin_headers),
        await client.patch(url, json={"status": "read"}, headers=admin_headers),
        await client.delete(url, headers=admin_headers),
    ]

    assert fetched.json()["message"] == "Hello!"
    assert replied.json()["status"] == "replied"
    assert [r.status_code for r in invalid] == [422, 422]
    assert deleted.status_code == 204
    assert [r.status_code for r in missing] == [404, 404, 404]
    [update] = await audit_entries(db_session, "contact_message.update")
    assert update.details == {"status": {"old": "unread", "new": "replied"}}
    [delete] = await audit_entries(db_session, "contact_message.delete")
    assert (delete.entity_id, delete.details) == (message.id, None)
