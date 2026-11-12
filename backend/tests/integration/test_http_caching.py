"""The caching headers on the real app: public reads revalidate, admin data isn't stored."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_public_reads_revalidate_and_admin_reads_are_not_stored(
    api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    await api.put("/admin/settings/site.name", json={"value": "Ada"}, headers=admin_headers)

    first = await api.get("/settings")
    unchanged = await api.get("/settings", headers={"If-None-Match": first.headers["ETag"]})
    await api.put("/admin/settings/site.name", json={"value": "Grace"}, headers=admin_headers)
    changed = await api.get("/settings", headers={"If-None-Match": first.headers["ETag"]})
    admin = await api.get("/admin/settings", headers=admin_headers)

    assert first.headers["Cache-Control"] == "public, no-cache"
    assert (unchanged.status_code, unchanged.content) == (304, b"")
    assert (changed.status_code, changed.json()) == (200, {"site.name": "Grace"})
    assert admin.headers["Cache-Control"] == "no-store"
    assert "ETag" not in admin.headers
