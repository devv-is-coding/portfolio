from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.imagekit import get_media_url_endpoint
from app.main import app
from app.models import Project, ProjectImage, Skill
from tests.integration.factories import audit_entries, create_media

pytestmark = pytest.mark.anyio

ENDPOINT = "https://ik.imagekit.io/portfolio"


@pytest.fixture
async def client(api: AsyncClient) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_media_url_endpoint] = lambda: ENDPOINT
    yield api


async def _create(
    client: AsyncClient, headers: dict[str, str], **fields: object
) -> dict[str, object]:
    response = await client.post("/admin/projects", json=fields, headers=headers)
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


async def _skill(session: AsyncSession, name: str, order: int = 0) -> Skill:
    skill = Skill(name=name, slug=name.lower(), display_order=order)
    session.add(skill)
    await session.flush()
    return skill


# --- create and publish ----------------------------------------------------------------


async def test_create_a_draft_with_a_slug_from_the_title(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    project = await _create(client, admin_headers, title="Online Shop", live_url="https://shop.dev")

    assert (project["slug"], project["status"], project["published_at"]) == (
        "online-shop",
        "draft",
        None,
    )
    assert project["live_url"] == "https://shop.dev/"
    [entry] = await audit_entries(db_session, "project.create")
    assert entry.details == {"title": "Online Shop", "slug": "online-shop", "status": "draft"}


async def test_publishing_sets_published_at_unless_given(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    now_published = await _create(client, admin_headers, title="A", status="published")
    dated = await _create(
        client,
        admin_headers,
        title="B",
        status="published",
        published_at="2025-01-02T10:00:00+08:00",
    )

    assert now_published["published_at"] is not None
    assert dated["published_at"] == "2025-01-02T02:00:00"  # stored as UTC


async def test_published_at_cannot_be_cleared_while_published(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    project = await _create(client, admin_headers, title="A", status="published")
    url = f"/admin/projects/{project['id']}"

    create = await client.post(
        "/admin/projects",
        json={"title": "B", "status": "published", "published_at": None},
        headers=admin_headers,
    )
    clear = await client.patch(url, json={"published_at": None}, headers=admin_headers)
    archive_and_clear = await client.patch(
        url, json={"status": "archived", "published_at": None}, headers=admin_headers
    )

    for response in (create, clear):
        assert response.status_code == 422
        assert response.json()["error"]["details"][0]["field"] == "body.published_at"
    assert archive_and_clear.status_code == 200


async def test_patch_publishes_and_audits_both_fields(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    project = await _create(client, admin_headers, title="A")

    published = await client.patch(
        f"/admin/projects/{project['id']}", json={"status": "published"}, headers=admin_headers
    )

    assert published.json()["status"] == "published"
    assert published.json()["published_at"] is not None
    [entry] = await audit_entries(db_session, "project.update")
    assert entry.details is not None
    assert entry.details["status"] == {"old": "draft", "new": "published"}
    published_at = entry.details["published_at"]
    assert isinstance(published_at, dict)
    assert published_at["old"] is None


@pytest.mark.parametrize(
    ("fields", "status_code", "field"),
    [
        ({"title": ""}, 422, "body.title"),
        ({"title": "日本語"}, 422, "body.slug"),
        ({"title": "A", "slug": "Not Valid"}, 422, "body.slug"),
        ({"title": "A", "status": "deleted"}, 422, "body.status"),
        ({"title": "A", "live_url": "javascript:alert(1)"}, 422, "body.live_url"),
        ({"title": "A", "short_description": "x" * 501}, 422, "body.short_description"),
        ({"title": "A", "thumbnail_media_id": 999_999_999}, 422, "body.thumbnail_media_id"),
        ({"title": "A", "secret": True}, 422, "body.secret"),
    ],
)
async def test_create_validates(
    client: AsyncClient,
    admin_headers: dict[str, str],
    fields: dict[str, object],
    status_code: int,
    field: str,
) -> None:
    response = await client.post("/admin/projects", json=fields, headers=admin_headers)

    assert response.status_code == status_code
    assert [d["field"] for d in response.json()["error"]["details"]] == [field]


async def test_duplicate_slug_is_409_and_thumbnail_must_be_an_image(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    await _create(client, admin_headers, title="Shop")
    pdf = await create_media(db_session, "doc1", "application/pdf")

    # The thumbnail check first: the 409's rollback also drops the uncommitted media row.
    pdf_thumb = await client.post(
        "/admin/projects", json={"title": "B", "thumbnail_media_id": pdf.id}, headers=admin_headers
    )
    duplicate = await client.post("/admin/projects", json={"title": "SHOP"}, headers=admin_headers)

    assert duplicate.status_code == 409
    assert pdf_thumb.json()["error"]["details"][0]["message"] == "Must be an image"


# --- public visibility -----------------------------------------------------------------


async def test_drafts_and_archived_projects_are_never_public(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    await _create(client, admin_headers, title="Draft")
    await _create(client, admin_headers, title="Archived", status="archived")
    await _create(client, admin_headers, title="Live", status="published")

    listed = (await client.get("/projects")).json()
    draft = await client.get("/projects/draft")
    archived = await client.get("/projects/archived")
    live = await client.get("/projects/live")

    assert [p["slug"] for p in listed["items"]] == ["live"]
    assert (draft.status_code, archived.status_code, live.status_code) == (404, 404, 200)
    assert "status" not in live.json()
    assert "description" not in listed["items"][0]


async def test_public_list_filters_searches_and_sorts(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    python = await _skill(db_session, "Python")
    shop = await _create(
        client, admin_headers, title="Shop", status="published", is_featured=True, display_order=2
    )
    await _create(
        client,
        admin_headers,
        title="Blog engine",
        short_description="A Markdown blog",
        status="published",
        display_order=1,
    )
    await client.put(
        f"/admin/projects/{shop['id']}/skills",
        json={"skill_ids": [python.id]},
        headers=admin_headers,
    )

    async def slugs(query: str = "") -> list[str]:
        return [p["slug"] for p in (await client.get(f"/projects?{query}")).json()["items"]]

    assert await slugs() == ["blog-engine", "shop"]
    assert await slugs("featured=true") == ["shop"]
    assert await slugs("skill=python") == ["shop"]
    assert await slugs("q=markdown") == ["blog-engine"]
    assert await slugs("sort=-display_order") == ["shop", "blog-engine"]
    assert (await client.get("/projects?sort=created_at")).status_code == 422


# --- admin reads, update, delete -------------------------------------------------------


async def test_admin_lists_every_status_and_filters_by_status(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    await _create(client, admin_headers, title="Draft")
    await _create(client, admin_headers, title="Live", status="published")

    every = (await client.get("/admin/projects", headers=admin_headers)).json()
    drafts = (await client.get("/admin/projects?status=draft", headers=admin_headers)).json()

    assert sorted(p["slug"] for p in every["items"]) == ["draft", "live"]
    assert [p["slug"] for p in drafts["items"]] == ["draft"]


async def test_update_validates_and_404s(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    project = await _create(client, admin_headers, title="A")
    url = f"/admin/projects/{project['id']}"

    responses = [
        await client.patch(url, json={"title": None}, headers=admin_headers),
        await client.patch(url, json={"status": None}, headers=admin_headers),
        await client.patch("/admin/projects/999999999", json={"title": "x"}, headers=admin_headers),
        await client.get("/admin/projects/999999999", headers=admin_headers),
    ]

    assert [r.status_code for r in responses] == [422, 422, 404, 404]


async def test_delete_removes_gallery_and_skill_links_but_keeps_media(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    media = await create_media(db_session, "shot1")
    skill = await _skill(db_session, "Python")
    project = await _create(client, admin_headers, title="A")
    await client.post(
        f"/admin/projects/{project['id']}/images",
        json={"media_id": media.id},
        headers=admin_headers,
    )
    await client.put(
        f"/admin/projects/{project['id']}/skills",
        json={"skill_ids": [skill.id]},
        headers=admin_headers,
    )

    deleted = await client.delete(f"/admin/projects/{project['id']}", headers=admin_headers)

    assert deleted.status_code == 204
    assert await db_session.get(Project, project["id"]) is None
    images = await db_session.scalars(select(ProjectImage).where(ProjectImage.media_id == media.id))
    assert images.all() == []
    assert await db_session.get(Skill, skill.id) is not None
    [entry] = await audit_entries(db_session, "project.delete")
    assert entry.details == {"title": "A", "slug": "a"}


# --- skills ------------------------------------------------------------------------------


async def test_replace_skills_sets_exactly_the_list(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    python = await _skill(db_session, "Python", order=2)
    go = await _skill(db_session, "Go", order=1)
    project = await _create(client, admin_headers, title="A")
    url = f"/admin/projects/{project['id']}/skills"

    both = await client.put(
        url, json={"skill_ids": [python.id, go.id, go.id]}, headers=admin_headers
    )
    one = await client.put(url, json={"skill_ids": [python.id]}, headers=admin_headers)
    unknown = await client.put(
        url, json={"skill_ids": [python.id, 999_999_999]}, headers=admin_headers
    )
    missing_project = await client.put(
        "/admin/projects/999999999/skills", json={"skill_ids": []}, headers=admin_headers
    )

    assert [s["name"] for s in both.json()["skills"]] == ["Go", "Python"]  # by display order
    assert [s["name"] for s in one.json()["skills"]] == ["Python"]
    assert unknown.status_code == 422
    assert unknown.json()["error"]["details"][0]["message"] == "Unknown ids: 999999999"
    assert missing_project.status_code == 404
    entries = await audit_entries(db_session, "project.skills_update")
    assert [e.details for e in entries] == [
        {"skill_ids": {"old": [], "new": sorted([python.id, go.id])}},
        {"skill_ids": {"old": sorted([python.id, go.id]), "new": [python.id]}},
    ]


# --- gallery -----------------------------------------------------------------------------


async def test_gallery_add_order_override_and_remove(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    first = await create_media(db_session, "shot1", file_path="/one.webp")
    first.alt_text = "Library alt"
    second = await create_media(db_session, "shot2", file_path="/two.webp")
    project = await _create(client, admin_headers, title="A", status="published")
    images_url = f"/admin/projects/{project['id']}/images"

    one = (
        await client.post(
            images_url, json={"media_id": first.id, "display_order": 2}, headers=admin_headers
        )
    ).json()
    two = (
        await client.post(
            images_url,
            json={"media_id": second.id, "alt_text": "Checkout page", "display_order": 1},
            headers=admin_headers,
        )
    ).json()

    gallery = (await client.get("/projects/a")).json()["images"]
    assert [image["id"] for image in gallery] == [two["id"], one["id"]]
    assert gallery[0]["image"]["alt_text"] == "Checkout page"  # override
    assert gallery[1]["image"]["alt_text"] == "Library alt"  # from the media
    assert gallery[1]["image"]["url"] == f"{ENDPOINT}/one.webp"

    moved = await client.patch(
        f"{images_url}/{one['id']}", json={"display_order": 0}, headers=admin_headers
    )
    removed = await client.delete(f"{images_url}/{two['id']}", headers=admin_headers)

    assert moved.json()["display_order"] == 0
    assert removed.status_code == 204
    assert [i["id"] for i in (await client.get("/projects/a")).json()["images"]] == [one["id"]]


async def test_gallery_rejects_documents_and_images_of_other_projects(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    pdf = await create_media(db_session, "doc1", "application/pdf")
    shot = await create_media(db_session, "shot1")
    a = await _create(client, admin_headers, title="A")
    b = await _create(client, admin_headers, title="B")
    image = (
        await client.post(
            f"/admin/projects/{a['id']}/images", json={"media_id": shot.id}, headers=admin_headers
        )
    ).json()

    document = await client.post(
        f"/admin/projects/{a['id']}/images", json={"media_id": pdf.id}, headers=admin_headers
    )
    other_project = await client.patch(
        f"/admin/projects/{b['id']}/images/{image['id']}",
        json={"display_order": 1},
        headers=admin_headers,
    )
    no_project = await client.post(
        "/admin/projects/999999999/images", json={"media_id": shot.id}, headers=admin_headers
    )

    assert document.status_code == 422
    assert (other_project.status_code, no_project.status_code) == (404, 404)
