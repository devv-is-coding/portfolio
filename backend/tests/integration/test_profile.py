from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.imagekit import get_media_url_endpoint
from app.main import app
from app.models import AuditLog, Media, Profile, User
from tests.integration.factories import create_media

pytestmark = pytest.mark.anyio

ENDPOINT = "https://ik.imagekit.io/portfolio"
PROFILE = {
    "full_name": "Devv",
    "headline": "Backend developer",
    "biography": "I build APIs.",
    "location": "Manila",
    "email": "devv@example.com",
    "phone": "+63 912 345 6789",
}


@pytest.fixture
async def client(api: AsyncClient) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_media_url_endpoint] = lambda: ENDPOINT
    yield api


@pytest.fixture
async def created(client: AsyncClient, admin_headers: dict[str, str]) -> dict[str, object]:
    response = await client.put("/admin/profile", json=PROFILE, headers=admin_headers)
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


async def _audit(session: AsyncSession, action: str) -> list[AuditLog]:
    return list((await session.scalars(select(AuditLog).where(AuditLog.action == action))).all())


# --- profile -------------------------------------------------------------------------------


async def test_public_profile_is_404_until_created(client: AsyncClient) -> None:
    response = await client.get("/profile")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "The profile hasn't been created yet"


async def test_put_creates_then_replaces_the_single_profile(
    client: AsyncClient,
    admin: User,
    admin_headers: dict[str, str],
    created: dict[str, object],
    db_session: AsyncSession,
) -> None:
    replaced = await client.put(
        "/admin/profile", json={"full_name": "  Devv Coder  "}, headers=admin_headers
    )

    assert replaced.status_code == 200
    body = replaced.json()
    assert body["full_name"] == "Devv Coder"
    assert body["headline"] is None  # fields left out of a PUT become empty
    assert (await client.get("/profile")).json() == body
    count = await db_session.scalar(select(func.count()).select_from(Profile))
    assert count == 1
    assert (await db_session.scalar(select(Profile.id))) == 1
    [create] = await _audit(db_session, "profile.create")
    assert (create.user_id, create.entity_id) == (admin.id, 1)
    [update] = await _audit(db_session, "profile.update")
    assert update.details is not None
    assert update.details["full_name"] == {"old": "Devv", "new": "Devv Coder"}
    assert update.details["headline"] == {"old": "Backend developer", "new": None}


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"full_name": "   "}, "body.full_name"),
        ({"full_name": "x" * 151}, "body.full_name"),
        ({"email": "not-an-email"}, "body.email"),
        ({"phone": "call me"}, "body.phone"),
        ({"biography": "x" * 10_001}, "body.biography"),
        ({"avatar_media_id": 0}, "body.avatar_media_id"),
        ({"is_admin": True}, "body.is_admin"),
    ],
)
async def test_put_validates_every_field(
    client: AsyncClient, admin_headers: dict[str, str], change: dict[str, object], field: str
) -> None:
    response = await client.put("/admin/profile", json=PROFILE | change, headers=admin_headers)

    assert response.status_code == 422
    assert [d["field"] for d in response.json()["error"]["details"]] == [field]


async def test_blank_optional_text_becomes_null(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    body = {"full_name": "Devv", "headline": "   ", "location": ""}

    profile = (await client.put("/admin/profile", json=body, headers=admin_headers)).json()

    assert (profile["headline"], profile["location"]) == (None, None)


async def test_avatar_and_resume_must_be_the_right_kind_of_media(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    image = await create_media(db_session, "avatar1", "image/webp", "/me.webp")
    pdf = await create_media(db_session, "resume1", "application/pdf", "/cv.pdf")

    async def put(**media: int) -> tuple[int, list[tuple[str, str]]]:
        response = await client.put("/admin/profile", json=PROFILE | media, headers=admin_headers)
        details = response.json().get("error", {}).get("details") or []
        return response.status_code, [(d["field"], d["message"]) for d in details]

    assert await put(avatar_media_id=pdf.id) == (
        422,
        [("body.avatar_media_id", "Must be an image")],
    )
    assert await put(resume_media_id=image.id) == (
        422,
        [("body.resume_media_id", "Must be a PDF document")],
    )
    assert await put(avatar_media_id=999_999_999) == (
        422,
        [("body.avatar_media_id", "No media with this id")],
    )
    assert (await put(avatar_media_id=image.id, resume_media_id=pdf.id))[0] == 201

    profile = (await client.get("/profile")).json()
    assert profile["avatar"]["url"] == f"{ENDPOINT}/me.webp"
    assert (profile["avatar"]["width"], profile["avatar"]["height"]) == (800, 600)
    assert profile["resume"]["url"] == f"{ENDPOINT}/cv.pdf"


async def test_deleting_the_avatar_media_clears_it_from_the_profile(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    image = await create_media(db_session, "avatar1")
    await client.put(
        "/admin/profile", json=PROFILE | {"avatar_media_id": image.id}, headers=admin_headers
    )

    await db_session.delete(await db_session.get(Media, image.id))
    await db_session.commit()

    profile = (await client.get("/profile")).json()
    assert (profile["avatar_media_id"], profile["avatar"]) == (None, None)


async def test_profile_needs_the_url_endpoint_only_when_it_shows_media(
    api: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    app.dependency_overrides[get_media_url_endpoint] = lambda: None
    await api.put("/admin/profile", json=PROFILE, headers=admin_headers)
    without_media = await api.get("/profile")
    image = await create_media(db_session, "avatar1")
    await api.patch("/admin/profile", json={"avatar_media_id": image.id}, headers=admin_headers)

    with_media = await api.get("/profile")

    assert without_media.status_code == 200
    assert with_media.status_code == 503


async def test_patch_changes_only_what_is_sent(
    client: AsyncClient,
    admin_headers: dict[str, str],
    created: dict[str, object],
    db_session: AsyncSession,
) -> None:
    changed = await client.patch(
        "/admin/profile", json={"headline": None, "location": "Cebu"}, headers=admin_headers
    )
    unchanged = await client.patch(
        "/admin/profile", json={"location": "Cebu"}, headers=admin_headers
    )

    body = changed.json()
    assert (body["full_name"], body["headline"], body["location"]) == ("Devv", None, "Cebu")
    assert unchanged.json() == body
    [update] = await _audit(db_session, "profile.update")  # the no-op wrote nothing
    assert update.details == {
        "headline": {"old": "Backend developer", "new": None},
        "location": {"old": "Manila", "new": "Cebu"},
    }


async def test_patch_rejects_null_for_required_fields_and_404s_without_profile(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    missing = await client.patch("/admin/profile", json={"headline": "x"}, headers=admin_headers)
    await client.put("/admin/profile", json=PROFILE, headers=admin_headers)

    null_name = await client.patch(
        "/admin/profile", json={"full_name": None}, headers=admin_headers
    )

    assert missing.status_code == 404
    assert null_name.status_code == 422
    assert null_name.json()["error"]["details"][0]["field"] == "body.full_name"


# --- social links ---------------------------------------------------------------------------


async def test_social_links_are_listed_in_order_on_the_profile(
    client: AsyncClient,
    admin: User,
    admin_headers: dict[str, str],
    created: dict[str, object],
    db_session: AsyncSession,
) -> None:
    for platform, order in (("github", 2), ("linkedin", 1), ("x", 2)):
        response = await client.post(
            "/admin/profile/social-links",
            json={"platform": platform, "url": f"https://{platform}.com", "display_order": order},
            headers=admin_headers,
        )
        assert response.status_code == 201

    links = (await client.get("/profile")).json()["social_links"]

    assert [link["platform"] for link in links] == ["linkedin", "github", "x"]
    assert links[0]["url"] == "https://linkedin.com/"
    created_entries = await _audit(db_session, "social_link.create")
    assert [entry.user_id for entry in created_entries] == [admin.id] * 3


@pytest.mark.parametrize(
    ("link", "field"),
    [
        ({"platform": "GitHub", "url": "https://github.com"}, "body.platform"),
        ({"platform": "github", "url": "ftp://github.com"}, "body.url"),
        ({"platform": "github", "url": "javascript:alert(1)"}, "body.url"),
        ({"platform": "github", "url": "https://x.com/" + "a" * 2048}, "body.url"),
        (
            {"platform": "github", "url": "https://github.com", "display_order": -1},
            "body.display_order",
        ),
    ],
)
async def test_social_links_are_validated(
    client: AsyncClient,
    admin_headers: dict[str, str],
    created: dict[str, object],
    link: dict[str, object],
    field: str,
) -> None:
    response = await client.post("/admin/profile/social-links", json=link, headers=admin_headers)

    assert response.status_code == 422
    assert [d["field"] for d in response.json()["error"]["details"]] == [field]


async def test_social_links_need_the_profile(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/admin/profile/social-links",
        json={"platform": "github", "url": "https://github.com"},
        headers=admin_headers,
    )

    assert response.status_code == 404


async def test_update_and_delete_a_social_link(
    client: AsyncClient,
    admin_headers: dict[str, str],
    created: dict[str, object],
    db_session: AsyncSession,
) -> None:
    link = (
        await client.post(
            "/admin/profile/social-links",
            json={"platform": "github", "url": "https://github.com/old"},
            headers=admin_headers,
        )
    ).json()
    url = f"/admin/profile/social-links/{link['id']}"

    updated = await client.patch(url, json={"url": "https://github.com/new"}, headers=admin_headers)
    null_platform = await client.patch(url, json={"platform": None}, headers=admin_headers)
    deleted = await client.delete(url, headers=admin_headers)
    again = await client.delete(url, headers=admin_headers)
    missing_update = await client.patch(url, json={"display_order": 1}, headers=admin_headers)

    assert updated.json()["url"] == "https://github.com/new"
    assert updated.json()["platform"] == "github"
    assert null_platform.status_code == 422
    assert (deleted.status_code, again.status_code, missing_update.status_code) == (204, 404, 404)
    assert (await client.get("/profile")).json()["social_links"] == []
    [update] = await _audit(db_session, "social_link.update")
    assert update.details == {
        "url": {"old": "https://github.com/old", "new": "https://github.com/new"}
    }
    [delete] = await _audit(db_session, "social_link.delete")
    assert delete.entity_id == link["id"]
