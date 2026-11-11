from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.imagekit import get_media_url_endpoint
from app.main import app
from app.models import Project, ProjectSkill, Skill, User
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
    response = await client.post("/admin/skills", json=fields, headers=headers)
    assert response.status_code == 201, response.text
    body: dict[str, object] = response.json()
    return body


async def test_create_makes_the_slug_from_the_name_and_audits(
    client: AsyncClient, admin: User, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    skill = await _create(client, admin_headers, name="  Next.js & React  ", category="frontend")

    assert (skill["name"], skill["slug"], skill["category"]) == (
        "Next.js & React",
        "next-js-react",
        "frontend",
    )
    assert (skill["display_order"], skill["icon"]) == (0, None)
    [entry] = await audit_entries(db_session, "skill.create")
    assert (entry.user_id, entry.entity_id) == (admin.id, skill["id"])


async def test_create_with_an_explicit_slug_and_an_icon(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    icon = await create_media(db_session, "py-icon", "image/svg+xml", "/icons/python.svg")

    skill = await _create(
        client, admin_headers, name="Python", slug="python-3", icon_media_id=icon.id
    )

    assert skill["slug"] == "python-3"
    assert skill["icon"] == {
        "url": f"{ENDPOINT}/icons/python.svg",
        "mime_type": "image/svg+xml",
        "width": 800,
        "height": 600,
        "alt_text": None,
    }


@pytest.mark.parametrize(
    ("fields", "status"),
    [
        ({"name": "python"}, 409),  # same name, other case
        ({"name": "Python 3", "slug": "python"}, 409),  # same slug
    ],
)
async def test_names_and_slugs_are_unique(
    client: AsyncClient, admin_headers: dict[str, str], fields: dict[str, object], status: int
) -> None:
    await _create(client, admin_headers, name="Python")

    response = await client.post("/admin/skills", json=fields, headers=admin_headers)

    assert response.status_code == status
    assert response.json()["error"]["message"] == "A record with these values already exists"


@pytest.mark.parametrize(
    ("fields", "field"),
    [
        ({"name": ""}, "body.name"),
        ({"name": "x" * 101}, "body.name"),
        ({"name": "Go", "slug": "Go Lang"}, "body.slug"),
        ({"name": "日本語"}, "body.slug"),  # nothing to make a slug from
        ({"name": "Go", "display_order": -1}, "body.display_order"),
        ({"name": "Go", "level": "expert"}, "body.level"),
    ],
)
async def test_create_validates(
    client: AsyncClient, admin_headers: dict[str, str], fields: dict[str, object], field: str
) -> None:
    response = await client.post("/admin/skills", json=fields, headers=admin_headers)

    assert response.status_code == 422
    assert [d["field"] for d in response.json()["error"]["details"]] == [field]


async def test_icon_must_be_an_existing_image(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    pdf = await create_media(db_session, "doc1", "application/pdf")

    not_image = await client.post(
        "/admin/skills", json={"name": "Go", "icon_media_id": pdf.id}, headers=admin_headers
    )
    missing = await client.post(
        "/admin/skills", json={"name": "Go", "icon_media_id": 999_999_999}, headers=admin_headers
    )

    assert [d["message"] for d in not_image.json()["error"]["details"]] == ["Must be an image"]
    assert [d["message"] for d in missing.json()["error"]["details"]] == ["No media with this id"]


async def test_public_list_is_ordered_filtered_searched_and_paginated(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    for name, category, order in (
        ("FastAPI", "backend", 2),
        ("Next.js", "frontend", 1),
        ("Python", "backend", 1),
        ("Docker", None, 3),
    ):
        await _create(client, admin_headers, name=name, category=category, display_order=order)

    async def names(query: str = "") -> list[str]:
        body = (await client.get(f"/skills?{query}")).json()
        return [skill["name"] for skill in body["items"]]

    assert await names() == ["Next.js", "Python", "FastAPI", "Docker"]  # order, then id
    assert await names("category=BACKEND") == ["Python", "FastAPI"]
    assert await names("q=py") == ["Python"]
    assert await names("sort=name") == ["Docker", "FastAPI", "Next.js", "Python"]
    page = (await client.get("/skills?size=3&page=2")).json()
    assert ([s["name"] for s in page["items"]], page["total"], page["pages"]) == (["Docker"], 4, 2)
    assert (await client.get("/skills?sort=slug")).status_code == 422


async def test_get_update_and_audit(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    skill = await _create(client, admin_headers, name="Python", category="backend")
    url = f"/admin/skills/{skill['id']}"

    fetched = await client.get(url, headers=admin_headers)
    updated = await client.patch(
        url, json={"category": None, "display_order": 5}, headers=admin_headers
    )
    unchanged = await client.patch(url, json={"display_order": 5}, headers=admin_headers)

    assert fetched.json() == skill
    assert (updated.json()["category"], updated.json()["display_order"]) == (None, 5)
    assert updated.json()["slug"] == "python"
    assert unchanged.status_code == 200
    [entry] = await audit_entries(db_session, "skill.update")
    assert entry.details == {
        "category": {"old": "backend", "new": None},
        "display_order": {"old": 0, "new": 5},
    }


async def test_update_rejects_nulls_bad_values_and_duplicates(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    await _create(client, admin_headers, name="Python")
    go = await _create(client, admin_headers, name="Go")
    url = f"/admin/skills/{go['id']}"

    responses = [
        await client.patch(url, json={"name": None}, headers=admin_headers),
        await client.patch(url, json={"slug": "Not Valid"}, headers=admin_headers),
        await client.patch(url, json={"slug": "python"}, headers=admin_headers),
        await client.patch("/admin/skills/999999999", json={"name": "x"}, headers=admin_headers),
    ]

    assert [r.status_code for r in responses] == [422, 422, 409, 404]


async def test_delete_removes_the_skill_from_projects(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    skill = await _create(client, admin_headers, name="Python")
    project = Project(title="Shop", slug="shop")
    db_session.add(project)
    await db_session.flush()
    db_session.add(ProjectSkill(project_id=project.id, skill_id=skill["id"]))
    await db_session.commit()

    deleted = await client.delete(f"/admin/skills/{skill['id']}", headers=admin_headers)
    again = await client.delete(f"/admin/skills/{skill['id']}", headers=admin_headers)

    assert (deleted.status_code, again.status_code) == (204, 404)
    assert await db_session.get(Skill, skill["id"]) is None
    links = await db_session.scalars(
        select(ProjectSkill).where(ProjectSkill.project_id == project.id)
    )
    assert links.all() == []
    [entry] = await audit_entries(db_session, "skill.delete")
    assert entry.details == {"name": "Python", "slug": "python"}
