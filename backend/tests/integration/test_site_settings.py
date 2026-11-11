import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.factories import audit_entries

pytestmark = pytest.mark.anyio

ADMIN_URL = "/admin/settings"


async def test_put_creates_then_replaces_and_audits(
    api: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    url = f"{ADMIN_URL}/seo.default_title"

    created = await api.put(url, json={"value": "My portfolio"}, headers=admin_headers)
    replaced = await api.put(url, json={"value": {"en": "Portfolio"}}, headers=admin_headers)
    unchanged = await api.put(url, json={"value": {"en": "Portfolio"}}, headers=admin_headers)

    assert created.status_code == 201
    assert (created.json()["key"], created.json()["is_public"]) == ("seo.default_title", True)
    assert (replaced.status_code, replaced.json()["value"]) == (200, {"en": "Portfolio"})
    assert unchanged.status_code == 200
    [create] = await audit_entries(db_session, "site_setting.create")
    assert create.details == {"key": "seo.default_title"}
    [update] = await audit_entries(db_session, "site_setting.update")  # the no-op wrote nothing
    assert update.details == {"setting_value": {"old": "My portfolio", "new": {"en": "Portfolio"}}}


async def test_only_public_prefixes_are_public(
    api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    values: dict[str, object] = {
        "site.name": "Ada",
        "seo.keywords": ["python", "fastapi"],
        "site.show_blog": False,
        "admin.notes": "internal",
        "sitemap.enabled": True,  # "site" must be a whole segment
    }
    for key, value in values.items():
        await api.put(f"{ADMIN_URL}/{key}", json={"value": value}, headers=admin_headers)

    public = (await api.get("/settings")).json()
    admin = (await api.get(ADMIN_URL, headers=admin_headers)).json()

    assert public == {
        "seo.keywords": ["python", "fastapi"],
        "site.name": "Ada",
        "site.show_blog": False,
    }
    assert [s["key"] for s in admin["items"]] == sorted(values)
    assert [s["key"] for s in admin["items"] if not s["is_public"]] == [
        "admin.notes",
        "sitemap.enabled",
    ]


@pytest.mark.parametrize(
    "key",
    [
        "smtp.password",
        "imagekit.private_key",
        "stripe.api_key",
        "github.token",
        "site.client_secret",
    ],
)
async def test_secret_like_keys_are_refused(
    api: AsyncClient, admin_headers: dict[str, str], key: str
) -> None:
    response = await api.put(f"{ADMIN_URL}/{key}", json={"value": "x"}, headers=admin_headers)

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "path.key"


@pytest.mark.parametrize(
    ("key", "body", "field"),
    [
        ("Site.Name", {"value": "x"}, "path.key"),
        ("nodot", {"value": "x"}, "path.key"),
        ("site..name", {"value": "x"}, "path.key"),
        ("site." + "a" * 150, {"value": "x"}, "path.key"),
        ("site.name", {}, "body.value"),
        ("site.name", {"value": "x" * 10_001}, "body.value"),
        ("site.name", {"value": "x", "public": True}, "body.public"),
    ],
)
async def test_keys_and_values_are_validated(
    api: AsyncClient, admin_headers: dict[str, str], key: str, body: dict[str, object], field: str
) -> None:
    response = await api.put(f"{ADMIN_URL}/{key}", json=body, headers=admin_headers)

    assert response.status_code == 422
    assert [detail["field"] for detail in response.json()["error"]["details"]] == [field]


async def test_get_delete_and_404(
    api: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    url = f"{ADMIN_URL}/site.name"
    await api.put(url, json={"value": None}, headers=admin_headers)

    fetched = await api.get(url, headers=admin_headers)
    deleted = await api.delete(url, headers=admin_headers)
    missing = [
        await api.get(url, headers=admin_headers),
        await api.delete(url, headers=admin_headers),
    ]

    assert (fetched.status_code, fetched.json()["value"]) == (200, None)
    assert deleted.status_code == 204
    assert [r.status_code for r in missing] == [404, 404]
    assert (await api.get("/settings")).json() == {}
    [entry] = await audit_entries(db_session, "site_setting.delete")
    assert entry.details == {"key": "site.name"}
