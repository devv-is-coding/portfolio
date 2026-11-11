from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.factories import audit_entries, create_via_api

pytestmark = pytest.mark.anyio

ADMIN_URL = "/admin/certifications"


async def _create(client: AsyncClient, headers: dict[str, str], **fields: object) -> dict[str, Any]:
    defaults: dict[str, object] = {"name": "AWS Developer", "issuing_organization": "AWS"}
    return await create_via_api(client, ADMIN_URL, headers, **(defaults | fields))


async def test_create_stores_the_url_and_audits(
    api: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    cert = await _create(
        api, admin_headers, credential_url="https://verify.example.com/abc", issued_at="2024-01-01"
    )

    assert cert["credential_url"] == "https://verify.example.com/abc"
    assert (cert["expires_at"], cert["is_expired"]) == (None, False)
    [entry] = await audit_entries(db_session, "certification.create")
    assert entry.details == {"name": "AWS Developer", "issuing_organization": "AWS"}


async def test_expired_ones_are_flagged_not_hidden_and_newest_come_first(
    api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    await _create(api, admin_headers, name="Undated")
    await _create(
        api, admin_headers, name="Expired", issued_at="2019-01-01", expires_at="2021-01-01"
    )
    await _create(api, admin_headers, name="Valid", issued_at="2024-01-01", expires_at="2999-01-01")

    listed = (await api.get("/certifications")).json()["items"]
    searched = (await api.get("/certifications?q=expir")).json()["items"]

    assert [(c["name"], c["is_expired"]) for c in listed] == [
        ("Valid", False),
        ("Expired", True),
        ("Undated", False),
    ]
    assert [c["name"] for c in searched] == ["Expired"]


@pytest.mark.parametrize(
    ("fields", "field"),
    [
        ({"name": ""}, "body.name"),
        ({"issuing_organization": "x" * 201}, "body.issuing_organization"),
        ({"credential_url": "javascript:alert(1)"}, "body.credential_url"),
        ({"credential_id": "x" * 151}, "body.credential_id"),
        ({"issued_at": "2024-01-01", "expires_at": "2023-01-01"}, "body.expires_at"),
    ],
)
async def test_create_validates(
    api: AsyncClient, admin_headers: dict[str, str], fields: dict[str, object], field: str
) -> None:
    body = {"name": "AWS Developer", "issuing_organization": "AWS"} | fields

    response = await api.post(ADMIN_URL, json=body, headers=admin_headers)

    assert response.status_code == 422
    assert [detail["field"] for detail in response.json()["error"]["details"]] == [field]


async def test_patch_checks_expiry_against_the_stored_issue_date(
    api: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    cert = await _create(api, admin_headers, issued_at="2024-01-01")
    url = f"{ADMIN_URL}/{cert['id']}"

    too_early = await api.patch(url, json={"expires_at": "2023-01-01"}, headers=admin_headers)
    updated = await api.patch(
        url,
        json={"expires_at": "2027-01-01", "credential_url": "https://example.com/c"},
        headers=admin_headers,
    )
    cleared = await api.patch(url, json={"credential_url": None}, headers=admin_headers)

    assert too_early.json()["error"]["details"][0] == {
        "field": "body.expires_at",
        "message": "Must not be before the issue date",
        "type": "date_order",
    }
    assert updated.json()["expires_at"] == "2027-01-01"
    assert cleared.json()["credential_url"] is None
    first, second = await audit_entries(db_session, "certification.update")
    assert first.details == {
        "expires_at": {"old": None, "new": "2027-01-01"},
        "credential_url": {"old": None, "new": "https://example.com/c"},
    }
    assert second.details == {"credential_url": {"old": "https://example.com/c", "new": None}}


async def test_get_delete_and_404(
    api: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    cert = await _create(api, admin_headers)
    url = f"{ADMIN_URL}/{cert['id']}"

    fetched = await api.get(url, headers=admin_headers)
    deleted = await api.delete(url, headers=admin_headers)
    missing = await api.patch(url, json={"name": "x"}, headers=admin_headers)

    assert fetched.json()["name"] == "AWS Developer"
    assert (deleted.status_code, missing.status_code) == (204, 404)
    assert len(await audit_entries(db_session, "certification.delete")) == 1
