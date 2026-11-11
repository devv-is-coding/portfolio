from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.imagekit import get_media_url_endpoint
from app.main import app
from tests.integration.factories import audit_entries, create_media, create_via_api

pytestmark = pytest.mark.anyio

ENDPOINT = "https://ik.imagekit.io/portfolio"


@pytest.fixture
async def client(api: AsyncClient) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_media_url_endpoint] = lambda: ENDPOINT
    yield api


async def _post(client: AsyncClient, headers: dict[str, str], **fields: object) -> dict[str, Any]:
    defaults: dict[str, object] = {"content": "# Hello"}
    return await create_via_api(client, "/admin/blog/posts", headers, **(defaults | fields))


async def _term(client: AsyncClient, headers: dict[str, str], kind: str, name: str) -> int:
    term = await create_via_api(client, f"/admin/blog/{kind}", headers, name=name)
    term_id: int = term["id"]
    return term_id


# --- categories and tags ---------------------------------------------------------------


@pytest.mark.parametrize("kind", ["categories", "tags"])
async def test_terms_crud_unique_names_and_audit(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession, kind: str
) -> None:
    admin_url = f"/admin/blog/{kind}"
    created = await create_via_api(client, admin_url, admin_headers, name="  Web Dev  ")
    await create_via_api(client, admin_url, admin_headers, name="AI", slug="ai")

    same_name = await client.post(admin_url, json={"name": "web dev"}, headers=admin_headers)
    same_slug = await client.post(
        admin_url, json={"name": "Other", "slug": "web-dev"}, headers=admin_headers
    )
    invalid = await client.post(admin_url, json={"name": " "}, headers=admin_headers)
    renamed = await client.patch(
        f"{admin_url}/{created['id']}", json={"name": "Web"}, headers=admin_headers
    )
    no_slug = await client.patch(
        f"{admin_url}/{created['id']}", json={"slug": None}, headers=admin_headers
    )
    missing = await client.get(f"{admin_url}/999999999", headers=admin_headers)
    listed = (await client.get(f"/blog/{kind}")).json()["items"]
    searched = (await client.get(f"/blog/{kind}?q=we")).json()["items"]

    assert (created["name"], created["slug"]) == ("Web Dev", "web-dev")
    assert (same_name.status_code, same_slug.status_code) == (409, 409)
    assert (invalid.status_code, no_slug.status_code, missing.status_code) == (422, 422, 404)
    assert renamed.json()["name"] == "Web"
    assert [t["name"] for t in listed] == ["AI", "Web"]
    assert [t["name"] for t in searched] == ["Web"]
    entity_type = "blog_category" if kind == "categories" else "blog_tag"
    assert len(await audit_entries(db_session, f"{entity_type}.create")) == 2
    [update] = await audit_entries(db_session, f"{entity_type}.update")
    assert update.details == {"name": {"old": "Web Dev", "new": "Web"}}


async def test_deleting_a_category_or_tag_keeps_the_posts(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    category = await _term(client, admin_headers, "categories", "News")
    tag = await _term(client, admin_headers, "tags", "Python")
    post = await _post(client, admin_headers, title="Hello", category_id=category)
    await client.put(
        f"/admin/blog/posts/{post['id']}/tags", json={"tag_ids": [tag]}, headers=admin_headers
    )

    deleted = [
        await client.delete(f"/admin/blog/categories/{category}", headers=admin_headers),
        await client.delete(f"/admin/blog/tags/{tag}", headers=admin_headers),
    ]
    after = (await client.get(f"/admin/blog/posts/{post['id']}", headers=admin_headers)).json()

    assert [response.status_code for response in deleted] == [204, 204]
    assert (after["category_id"], after["category"], after["tags"]) == (None, None, [])
    assert len(await audit_entries(db_session, "blog_category.delete")) == 1


# --- posts: create, publish, validate -------------------------------------------------


async def test_create_a_draft_with_category_and_cover(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    cover = await create_media(db_session, "cover1", file_path="/covers/one.webp")
    category = await _term(client, admin_headers, "categories", "News")

    post = await _post(
        client,
        admin_headers,
        title="Hello, World!",
        excerpt="  ",
        category_id=category,
        cover_media_id=cover.id,
    )

    assert (post["slug"], post["status"], post["published_at"], post["excerpt"]) == (
        "hello-world",
        "draft",
        None,
        None,
    )
    assert post["category"] == {"id": category, "name": "News", "slug": "news"}
    assert post["cover"]["url"] == f"{ENDPOINT}/covers/one.webp"
    [entry] = await audit_entries(db_session, "blog_post.create")
    assert entry.details == {"title": "Hello, World!", "slug": "hello-world", "status": "draft"}


@pytest.mark.parametrize(
    ("fields", "field"),
    [
        ({"title": ""}, "body.title"),
        ({"title": "A", "content": "  "}, "body.content"),
        ({"title": "A", "content": "x" * 200_001}, "body.content"),
        ({"title": "日本語"}, "body.slug"),
        ({"title": "A", "excerpt": "x" * 501}, "body.excerpt"),
        ({"title": "A", "category_id": 999_999_999}, "body.category_id"),
        ({"title": "A", "cover_media_id": 999_999_999}, "body.cover_media_id"),
        ({"title": "A", "status": "published", "published_at": None}, "body.published_at"),
        ({"title": "A", "author": "me"}, "body.author"),
    ],
)
async def test_create_validates(
    client: AsyncClient, admin_headers: dict[str, str], fields: dict[str, object], field: str
) -> None:
    body = {"content": "Text"} | fields

    response = await client.post("/admin/blog/posts", json=body, headers=admin_headers)

    assert response.status_code == 422
    assert [detail["field"] for detail in response.json()["error"]["details"]] == [field]


async def test_cover_must_be_an_image_and_slugs_are_unique(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    pdf = await create_media(db_session, "doc1", "application/pdf")
    await _post(client, admin_headers, title="Hello")

    # The cover check first: the 409's rollback also drops the uncommitted media row.
    pdf_cover = await client.post(
        "/admin/blog/posts",
        json={"title": "B", "content": "x", "cover_media_id": pdf.id},
        headers=admin_headers,
    )
    duplicate = await client.post(
        "/admin/blog/posts", json={"title": "HELLO", "content": "x"}, headers=admin_headers
    )

    assert pdf_cover.json()["error"]["details"][0]["message"] == "Must be an image"
    assert duplicate.status_code == 409


async def test_publishing_rules_on_patch(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    post = await _post(client, admin_headers, title="A")
    url = f"/admin/blog/posts/{post['id']}"

    published = await client.patch(url, json={"status": "published"}, headers=admin_headers)
    cleared = await client.patch(url, json={"published_at": None}, headers=admin_headers)
    archived = await client.patch(
        url, json={"status": "archived", "published_at": None}, headers=admin_headers
    )

    assert published.json()["published_at"] is not None
    assert cleared.json()["error"]["details"][0]["field"] == "body.published_at"
    assert (archived.json()["status"], archived.json()["published_at"]) == ("archived", None)
    first, second = await audit_entries(db_session, "blog_post.update")
    assert first.details is not None
    assert first.details["status"] == {"old": "draft", "new": "published"}
    assert second.details is not None
    assert set(second.details) == {"status", "published_at"}


# --- public reads ----------------------------------------------------------------------


async def test_only_published_posts_are_public(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    await _post(client, admin_headers, title="Draft")
    await _post(client, admin_headers, title="Archived", status="archived")
    await _post(client, admin_headers, title="Live", status="published", content="**Bold**")

    listed = (await client.get("/blog/posts")).json()["items"]
    responses = [await client.get(f"/blog/posts/{slug}") for slug in ("draft", "archived")]
    live = (await client.get("/blog/posts/live")).json()

    assert [p["slug"] for p in listed] == ["live"]
    assert "content" not in listed[0]
    assert [r.status_code for r in responses] == [404, 404]
    assert live["content"] == "**Bold**"
    assert "status" not in live


async def test_public_list_filters_searches_and_sorts_newest_first(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    news = await _term(client, admin_headers, "categories", "News")
    python = await _term(client, admin_headers, "tags", "Python")
    old = await _post(
        client,
        admin_headers,
        title="Old",
        excerpt="About FastAPI",
        status="published",
        published_at="2024-01-01T00:00:00Z",
        category_id=news,
    )
    await _post(
        client, admin_headers, title="New", status="published", published_at="2025-01-01T00:00:00Z"
    )
    await client.put(
        f"/admin/blog/posts/{old['id']}/tags", json={"tag_ids": [python]}, headers=admin_headers
    )

    async def slugs(query: str = "") -> list[str]:
        return [p["slug"] for p in (await client.get(f"/blog/posts?{query}")).json()["items"]]

    assert await slugs() == ["new", "old"]
    assert await slugs("category=news") == ["old"]
    assert await slugs("tag=python") == ["old"]
    assert await slugs("q=fastapi") == ["old"]
    assert await slugs("sort=title") == ["new", "old"]
    assert (await client.get("/blog/posts?sort=created_at")).status_code == 422


# --- admin reads, tags, delete --------------------------------------------------------


async def test_admin_lists_every_status_and_filters(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    await _post(client, admin_headers, title="Draft")
    await _post(client, admin_headers, title="Live", status="published")

    every = (await client.get("/admin/blog/posts", headers=admin_headers)).json()["items"]
    drafts = (await client.get("/admin/blog/posts?status=draft", headers=admin_headers)).json()

    assert [p["slug"] for p in every] == ["live", "draft"]  # newest first
    assert [p["slug"] for p in drafts["items"]] == ["draft"]


async def test_replace_tags_sets_exactly_the_list(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    web = await _term(client, admin_headers, "tags", "Web")
    ai = await _term(client, admin_headers, "tags", "AI")
    post = await _post(client, admin_headers, title="A")
    url = f"/admin/blog/posts/{post['id']}/tags"

    both = await client.put(url, json={"tag_ids": [web, ai, ai]}, headers=admin_headers)
    same = await client.put(url, json={"tag_ids": [ai, web]}, headers=admin_headers)
    unknown = await client.put(url, json={"tag_ids": [999_999_999]}, headers=admin_headers)
    missing = await client.put(
        "/admin/blog/posts/999999999/tags", json={"tag_ids": []}, headers=admin_headers
    )

    assert [t["name"] for t in both.json()["tags"]] == ["AI", "Web"]  # by name
    assert same.status_code == 200
    assert unknown.json()["error"]["details"][0]["message"] == "Unknown ids: 999999999"
    assert missing.status_code == 404
    [entry] = await audit_entries(db_session, "blog_post.tags_update")  # the no-op wrote nothing
    assert entry.details == {"tag_ids": {"old": [], "new": sorted([web, ai])}}


async def test_delete_post_and_404s(
    client: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    tag = await _term(client, admin_headers, "tags", "Web")
    post = await _post(client, admin_headers, title="A")
    url = f"/admin/blog/posts/{post['id']}"
    await client.put(f"{url}/tags", json={"tag_ids": [tag]}, headers=admin_headers)

    deleted = await client.delete(url, headers=admin_headers)
    responses = [
        await client.get(url, headers=admin_headers),
        await client.patch(url, json={"title": "B"}, headers=admin_headers),
        await client.delete(url, headers=admin_headers),
    ]

    assert deleted.status_code == 204
    assert [r.status_code for r in responses] == [404, 404, 404]
    assert (await client.get(f"/admin/blog/tags/{tag}", headers=admin_headers)).status_code == 200
    [entry] = await audit_entries(db_session, "blog_post.delete")
    assert entry.details == {"title": "A", "slug": "a"}
