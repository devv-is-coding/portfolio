from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.imagekit import get_media_url_endpoint
from app.main import app
from app.models import Media
from tests.integration.factories import audit_entries, create_media, create_via_api

pytestmark = pytest.mark.anyio

ADMIN_URL = "/admin/certifications"
ENDPOINT = "https://ik.imagekit.io/portfolio"


@pytest.fixture
async def client(api: AsyncClient) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_media_url_endpoint] = lambda: ENDPOINT
    yield api


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


async def test_the_certificate_picture_is_shown_in_the_public_list(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    picture = await create_media(db_session, "cert1", "image/webp", "/certs/aws.webp")

    cert = await _create(client, admin_headers, image_media_id=picture.id)
    [listed] = (await client.get("/certifications")).json()["items"]

    assert cert["image_media_id"] == picture.id
    assert listed["image"] == {
        "url": f"{ENDPOINT}/certs/aws.webp",
        "mime_type": "image/webp",
        "width": picture.width,
        "height": picture.height,
        "alt_text": picture.alt_text,
    }


async def test_the_picture_must_be_an_existing_image(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    pdf = await create_media(db_session, "cert-pdf", "application/pdf")
    cert = await _create(client, admin_headers)
    body = {"name": "AWS Developer", "issuing_organization": "AWS"}

    not_image = await client.post(
        ADMIN_URL, json=body | {"image_media_id": pdf.id}, headers=admin_headers
    )
    missing = await client.patch(
        f"{ADMIN_URL}/{cert['id']}", json={"image_media_id": 999_999_999}, headers=admin_headers
    )

    assert not_image.status_code == missing.status_code == 422
    assert not_image.json()["error"]["details"][0]["field"] == "body.image_media_id"
    assert [d["message"] for d in not_image.json()["error"]["details"]] == ["Must be an image"]
    assert [d["message"] for d in missing.json()["error"]["details"]] == ["No media with this id"]


async def test_patch_sets_and_removes_the_picture_and_audits_it(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    picture = await create_media(db_session, "cert2", "image/png", "/certs/gcp.png")
    cert = await _create(client, admin_headers)
    url = f"{ADMIN_URL}/{cert['id']}"

    added = await client.patch(url, json={"image_media_id": picture.id}, headers=admin_headers)
    removed = await client.patch(url, json={"image_media_id": None}, headers=admin_headers)

    assert added.json()["image"]["url"] == f"{ENDPOINT}/certs/gcp.png"
    assert (removed.json()["image_media_id"], removed.json()["image"]) == (None, None)
    first, second = await audit_entries(db_session, "certification.update")
    assert first.details == {"image_media_id": {"old": None, "new": picture.id}}
    assert second.details == {"image_media_id": {"old": picture.id, "new": None}}


async def test_deleting_the_media_file_removes_the_picture(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    picture = await create_media(db_session, "cert3")
    cert = await _create(client, admin_headers, image_media_id=picture.id)

    await db_session.delete(await db_session.get(Media, picture.id))
    await db_session.commit()

    fetched = (await client.get(f"{ADMIN_URL}/{cert['id']}", headers=admin_headers)).json()
    assert (fetched["image_media_id"], fetched["image"]) == (None, None)
