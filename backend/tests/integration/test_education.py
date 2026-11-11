from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration.factories import audit_entries, create_via_api

pytestmark = pytest.mark.anyio

ADMIN_URL = "/admin/education"


async def _create(client: AsyncClient, headers: dict[str, str], **fields: object) -> dict[str, Any]:
    return await create_via_api(client, ADMIN_URL, headers, **({"institution": "MIT"} | fields))


async def test_create_with_only_the_institution_and_audit(
    api: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    entry = await _create(api, admin_headers, degree="  ")

    assert (entry["institution"], entry["degree"], entry["start_date"]) == ("MIT", None, None)
    [audit] = await audit_entries(db_session, "education.create")
    assert audit.details == {"institution": "MIT", "degree": None}


async def test_public_list_puts_in_progress_first_then_newest(
    api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    await _create(api, admin_headers, institution="School", end_date="2012-06-01")
    await _create(api, admin_headers, institution="College", end_date="2016-06-01")
    await _create(api, admin_headers, institution="Master", start_date="2024-09-01")

    listed = (await api.get("/education")).json()
    searched = (await api.get("/education?q=coll")).json()

    assert [e["institution"] for e in listed["items"]] == ["Master", "College", "School"]
    assert [e["institution"] for e in searched["items"]] == ["College"]


@pytest.mark.parametrize(
    ("fields", "field"),
    [
        ({"institution": "  "}, "body.institution"),
        ({"description": "x" * 16_001}, "body.description"),
        ({"start_date": "2020-01-01", "end_date": "2019-01-01"}, "body.end_date"),
    ],
)
async def test_create_validates(
    api: AsyncClient, admin_headers: dict[str, str], fields: dict[str, object], field: str
) -> None:
    response = await api.post(
        ADMIN_URL, json={"institution": "MIT"} | fields, headers=admin_headers
    )

    assert response.status_code == 422
    assert [detail["field"] for detail in response.json()["error"]["details"]] == [field]


async def test_patch_delete_and_404(
    api: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    entry = await _create(api, admin_headers, end_date="2016-06-01")
    url = f"{ADMIN_URL}/{entry['id']}"

    late_start = await api.patch(url, json={"start_date": "2017-01-01"}, headers=admin_headers)
    no_name = await api.patch(url, json={"institution": None}, headers=admin_headers)
    updated = await api.patch(
        url, json={"start_date": "2012-09-01", "degree": "BSc"}, headers=admin_headers
    )
    deleted = await api.delete(url, headers=admin_headers)
    gone = await api.get(url, headers=admin_headers)

    assert late_start.json()["error"]["details"][0]["field"] == "body.start_date"
    assert no_name.status_code == 422
    assert (updated.json()["start_date"], updated.json()["degree"]) == ("2012-09-01", "BSc")
    assert (deleted.status_code, gone.status_code) == (204, 404)
    [update] = await audit_entries(db_session, "education.update")
    assert update.details == {
        "start_date": {"old": None, "new": "2012-09-01"},
        "degree": {"old": None, "new": "BSc"},
    }
    assert len(await audit_entries(db_session, "education.delete")) == 1
