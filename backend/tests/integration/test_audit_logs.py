from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, User

pytestmark = pytest.mark.anyio

URL = "/admin/audit-logs"


@pytest.fixture
async def entries(db_session: AsyncSession, admin: User) -> list[AuditLog]:
    """Three entries a day apart (the admin fixture also writes `auth.admin_created`)."""
    rows = [
        AuditLog(
            user_id=admin.id,
            action="project.create",
            entity_type="project",
            entity_id=1,
            details={"title": "A"},
            created_at=datetime(2025, 1, 1, 12),
        ),
        AuditLog(
            user_id=admin.id,
            action="project.update",
            entity_type="project",
            entity_id=1,
            details={"title": {"old": "A", "new": "B"}},
            created_at=datetime(2025, 1, 2, 12),
        ),
        AuditLog(
            user_id=None,
            action="auth.login_failed",
            ip_address="203.0.113.7",
            created_at=datetime(2025, 1, 3, 12),
        ),
    ]
    db_session.add_all(rows)
    await db_session.flush()
    return rows


async def _actions(api: AsyncClient, headers: dict[str, str], query: str) -> list[str]:
    response = await api.get(f"{URL}?{query}", headers=headers)
    assert response.status_code == 200, response.text
    return [entry["action"] for entry in response.json()["items"]]


async def test_lists_newest_first_with_details(
    api: AsyncClient, admin_headers: dict[str, str], entries: list[AuditLog]
) -> None:
    response = await api.get(f"{URL}?until=2025-01-04T00:00:00Z", headers=admin_headers)

    body = response.json()
    assert [entry["action"] for entry in body["items"]] == [
        "auth.login_failed",
        "project.update",
        "project.create",
    ]
    assert body["items"][1]["details"] == {"title": {"old": "A", "new": "B"}}
    assert body["items"][0]["ip_address"] == "203.0.113.7"
    assert body["total"] == 3


async def test_filters(
    api: AsyncClient, admin: User, admin_headers: dict[str, str], entries: list[AuditLog]
) -> None:
    old = "until=2025-01-04T00:00:00"
    assert await _actions(api, admin_headers, f"{old}&user_id={admin.id}") == [
        "project.update",
        "project.create",
    ]
    assert await _actions(api, admin_headers, "action=project.create") == ["project.create"]
    assert await _actions(api, admin_headers, "entity_type=project&entity_id=1") == [
        "project.update",
        "project.create",
    ]
    assert await _actions(api, admin_headers, "entity_type=project&entity_id=2") == []
    # since inclusive, until exclusive; an offset is converted to UTC.
    assert await _actions(
        api, admin_headers, "since=2025-01-02T12:00:00&until=2025-01-03T20:00:00%2B08:00"
    ) == ["project.update"]
    assert await _actions(api, admin_headers, f"{old}&sort=created_at&size=1") == ["project.create"]


@pytest.mark.parametrize(
    ("query", "field"),
    [
        ("since=2025-01-02T00:00:00&until=2025-01-01T00:00:00", "query.until"),
        ("since=yesterday", "query.since"),
        ("user_id=0", "query.user_id"),
        ("sort=action", "query.sort"),
    ],
)
async def test_invalid_filters_are_422(
    api: AsyncClient, admin_headers: dict[str, str], query: str, field: str
) -> None:
    response = await api.get(f"{URL}?{query}", headers=admin_headers)

    assert response.status_code == 422
    assert [detail["field"] for detail in response.json()["error"]["details"]] == [field]


async def test_the_trail_is_read_only(api: AsyncClient, admin_headers: dict[str, str]) -> None:
    responses = [
        await api.post(URL, json={"action": "x"}, headers=admin_headers),
        await api.patch(f"{URL}/1", json={"action": "x"}, headers=admin_headers),
        await api.delete(f"{URL}/1", headers=admin_headers),
    ]

    assert [r.status_code for r in responses] == [405, 404, 404]
