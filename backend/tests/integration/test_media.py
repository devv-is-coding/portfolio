"""Media endpoints against MariaDB, with ImageKit replaced by FakeImageKit (no real
ImageKit calls) and the Celery deletion captured."""

import time
from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.imagekit import (
    UPLOAD_AUTH_TTL_SECONDS,
    ImageKitClient,
    ImageKitConfig,
    create_http_client,
    get_imagekit_client,
    get_imagekit_config,
    sign_upload,
)
from app.main import app
from app.models import AuditLog, Media, Profile, User
from app.routers.media import get_file_deleter
from tests.fakes import FakeImageKit, IsolatedSettings

pytestmark = pytest.mark.anyio

CONFIG = ImageKitConfig(
    public_key="public_test",
    private_key="private_test",
    url_endpoint="https://ik.imagekit.io/portfolio",
)


@pytest.fixture
def imagekit() -> FakeImageKit:
    fake = FakeImageKit()
    fake.add_file("img1", "/projects/shop.webp", "image/webp", 2048, 1200, 800)
    fake.add_file("img2", "/skills/python.svg", "image/svg+xml", 512, 64, 64)
    fake.add_file("pdf1", "/resume.pdf", "application/pdf", 90_000, 0, 0)
    fake.add_file("vid1", "/intro.mp4", "video/mp4", 5_000_000, 1920, 1080)
    return fake


@pytest.fixture
def deleted_files() -> list[str]:
    return []


@pytest.fixture
async def media_api(
    api: AsyncClient, imagekit: FakeImageKit, deleted_files: list[str]
) -> AsyncIterator[AsyncClient]:
    async def _client() -> AsyncIterator[ImageKitClient]:
        async with create_http_client(CONFIG, imagekit.transport) as http:
            yield ImageKitClient(http)

    app.dependency_overrides[get_imagekit_config] = lambda: CONFIG
    app.dependency_overrides[get_imagekit_client] = _client
    app.dependency_overrides[get_file_deleter] = lambda: deleted_files.append
    yield api


async def _register(
    client: AsyncClient, headers: dict[str, str], file_id: str, alt_text: str | None = None
) -> dict[str, object]:
    response = await client.post(
        "/admin/media", json={"file_id": file_id, "alt_text": alt_text}, headers=headers
    )
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


async def _audit(session: AsyncSession, action: str) -> list[AuditLog]:
    return list((await session.scalars(select(AuditLog).where(AuditLog.action == action))).all())


# --- upload-auth -----------------------------------------------------------------------


async def test_upload_auth_signs_a_short_lived_upload(
    media_api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    response = await media_api.get("/admin/media/upload-auth", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["signature"] == sign_upload(
        CONFIG.private_key, token=body["token"], expire=body["expire"]
    )
    assert body["public_key"] == "public_test"
    assert body["url_endpoint"] == CONFIG.url_endpoint
    assert body["upload_url"] == "https://upload.imagekit.io/api/v1/files/upload"
    assert "private_test" not in response.text


async def test_upload_auth_expires_within_the_ttl(
    media_api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    before = int(time.time())
    body = (await media_api.get("/admin/media/upload-auth", headers=admin_headers)).json()

    assert (
        before + UPLOAD_AUTH_TTL_SECONDS <= body["expire"] <= before + UPLOAD_AUTH_TTL_SECONDS + 5
    )


async def test_media_answers_503_when_imagekit_is_not_configured(
    api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    app.dependency_overrides[get_settings] = lambda: IsolatedSettings()

    responses = [
        await api.get("/admin/media/upload-auth", headers=admin_headers),
        await api.get("/admin/media", headers=admin_headers),
        await api.post("/admin/media", json={"file_id": "img1"}, headers=admin_headers),
    ]
    anonymous = await api.get("/admin/media/upload-auth")

    assert [r.status_code for r in responses] == [503, 503, 503]
    assert responses[0].json()["error"]["message"] == "Media uploads are not configured"
    assert anonymous.status_code == 401  # authentication is checked first


# --- register ----------------------------------------------------------------------------


async def test_register_stores_what_imagekit_reports(
    media_api: AsyncClient, admin: User, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    body = await _register(media_api, admin_headers, "img1", alt_text="  Shop homepage  ")

    assert body["url"] == "https://ik.imagekit.io/portfolio/projects/shop.webp"
    assert body["kind"] == "image"
    assert (body["mime_type"], body["size_bytes"]) == ("image/webp", 2048)
    assert (body["width"], body["height"]) == (1200, 800)
    assert body["alt_text"] == "Shop homepage"
    stored = await db_session.get(Media, body["id"])
    assert stored is not None
    assert stored.file_path == "/projects/shop.webp"
    [entry] = await _audit(db_session, "media.create")
    assert (entry.user_id, entry.entity_type, entry.entity_id) == (admin.id, "media", body["id"])


async def test_register_a_pdf_document(
    media_api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    body = await _register(media_api, admin_headers, "pdf1")

    assert (body["kind"], body["width"], body["height"]) == ("document", None, None)


@pytest.mark.parametrize(
    ("file_id", "message"),
    [
        ("missing", "No ImageKit file with this id"),
        ("vid1", "Unsupported file type video/mp4: use an image or a PDF"),
    ],
)
async def test_register_rejects_unknown_and_unsupported_files(
    media_api: AsyncClient, admin_headers: dict[str, str], file_id: str, message: str
) -> None:
    response = await media_api.post(
        "/admin/media", json={"file_id": file_id}, headers=admin_headers
    )

    assert response.status_code == 422
    [detail] = response.json()["error"]["details"]
    assert (detail["field"], detail["message"]) == ("body.file_id", message)


@pytest.mark.parametrize("file_id", ["", "../files", "a b", "x" * 65])
async def test_register_validates_the_file_id(
    media_api: AsyncClient, admin_headers: dict[str, str], imagekit: FakeImageKit, file_id: str
) -> None:
    response = await media_api.post(
        "/admin/media", json={"file_id": file_id}, headers=admin_headers
    )

    assert response.status_code == 422
    assert imagekit.requested_paths == []  # rejected before calling ImageKit


async def test_register_twice_is_a_conflict(
    media_api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    await _register(media_api, admin_headers, "img1")

    response = await media_api.post("/admin/media", json={"file_id": "img1"}, headers=admin_headers)

    assert response.status_code == 409
    assert response.json()["error"]["message"] == "This file is already registered"


async def test_imagekit_outage_is_a_502(
    media_api: AsyncClient, admin_headers: dict[str, str], imagekit: FakeImageKit
) -> None:
    imagekit.files["img1"] = {"broken": True}  # ImageKit answers something unexpected

    response = await media_api.post("/admin/media", json={"file_id": "img1"}, headers=admin_headers)

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "bad_gateway"


# --- list and read -------------------------------------------------------------------------


async def test_list_is_newest_first_and_paginated(
    media_api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    for file_id in ("img1", "img2", "pdf1"):
        await _register(media_api, admin_headers, file_id)

    first = (await media_api.get("/admin/media?size=2", headers=admin_headers)).json()
    second = (await media_api.get("/admin/media?size=2&page=2", headers=admin_headers)).json()

    assert [m["file_id"] for m in first["items"]] == ["pdf1", "img2"]
    assert [m["file_id"] for m in second["items"]] == ["img1"]
    assert (first["total"], first["pages"]) == (3, 2)


async def test_list_filters_by_kind_and_searches_path_and_alt_text(
    media_api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    await _register(media_api, admin_headers, "img1", alt_text="Shop homepage")
    await _register(media_api, admin_headers, "img2")
    await _register(media_api, admin_headers, "pdf1")

    async def file_ids(query: str) -> list[str]:
        body = (await media_api.get(f"/admin/media?{query}", headers=admin_headers)).json()
        return sorted(m["file_id"] for m in body["items"])

    assert await file_ids("kind=document") == ["pdf1"]
    assert await file_ids("kind=image") == ["img1", "img2"]
    assert await file_ids("q=HOMEPAGE") == ["img1"]
    assert await file_ids("q=skills") == ["img2"]
    assert await file_ids("sort=-size_bytes&size=1") == ["pdf1"]


@pytest.mark.parametrize("query", ["kind=video", "sort=file_id", "size=101"])
async def test_list_rejects_invalid_parameters(
    media_api: AsyncClient, admin_headers: dict[str, str], query: str
) -> None:
    response = await media_api.get(f"/admin/media?{query}", headers=admin_headers)

    assert response.status_code == 422


async def test_get_one_and_missing(media_api: AsyncClient, admin_headers: dict[str, str]) -> None:
    body = await _register(media_api, admin_headers, "img1")

    found = await media_api.get(f"/admin/media/{body['id']}", headers=admin_headers)
    missing = await media_api.get("/admin/media/999999999", headers=admin_headers)

    assert found.json() == body | {"updated_at": found.json()["updated_at"]}
    assert missing.status_code == 404
    assert missing.json()["error"]["message"] == "Media not found"


# --- update --------------------------------------------------------------------------------


async def test_update_changes_the_alt_text_and_audits_the_change(
    media_api: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    body = await _register(media_api, admin_headers, "img1")
    url = f"/admin/media/{body['id']}"

    changed = await media_api.patch(url, json={"alt_text": "Shop"}, headers=admin_headers)
    unchanged = await media_api.patch(url, json={"alt_text": "Shop"}, headers=admin_headers)
    untouched = await media_api.patch(url, json={}, headers=admin_headers)
    cleared = await media_api.patch(url, json={"alt_text": "   "}, headers=admin_headers)

    assert [r.json()["alt_text"] for r in (changed, unchanged, untouched, cleared)] == [
        "Shop",
        "Shop",
        "Shop",
        None,
    ]
    updates = await _audit(db_session, "media.update")
    assert [entry.details for entry in updates] == [
        {"alt_text": {"old": None, "new": "Shop"}},
        {"alt_text": {"old": "Shop", "new": None}},
    ]


async def test_update_validates_and_404s(
    media_api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    body = await _register(media_api, admin_headers, "img1")

    too_long = await media_api.patch(
        f"/admin/media/{body['id']}", json={"alt_text": "x" * 256}, headers=admin_headers
    )
    missing = await media_api.patch(
        "/admin/media/999999999", json={"alt_text": "x"}, headers=admin_headers
    )

    assert (too_long.status_code, missing.status_code) == (422, 404)


# --- delete --------------------------------------------------------------------------------


async def test_delete_removes_the_row_clears_uses_and_queues_the_imagekit_deletion(
    media_api: AsyncClient,
    admin_headers: dict[str, str],
    db_session: AsyncSession,
    deleted_files: list[str],
) -> None:
    body = await _register(media_api, admin_headers, "img1")
    profile = Profile(full_name="Devv", avatar_media_id=body["id"])
    db_session.add(profile)
    await db_session.commit()

    response = await media_api.delete(f"/admin/media/{body['id']}", headers=admin_headers)
    again = await media_api.delete(f"/admin/media/{body['id']}", headers=admin_headers)

    assert (response.status_code, again.status_code) == (204, 404)
    assert await db_session.get(Media, body["id"]) is None
    await db_session.refresh(profile)
    assert profile.avatar_media_id is None
    assert deleted_files == ["img1"]  # queued once, after the row was gone
    [entry] = await _audit(db_session, "media.delete")
    assert entry.details == {"file_id": "img1", "file_path": "/projects/shop.webp"}
