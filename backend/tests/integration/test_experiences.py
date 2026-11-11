from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from tests.integration.factories import audit_entries, create_via_api

pytestmark = pytest.mark.anyio

ADMIN_URL = "/admin/experiences"


async def _create(client: AsyncClient, headers: dict[str, str], **fields: object) -> dict[str, Any]:
    defaults: dict[str, object] = {"company": "Acme", "position": "Developer"}
    return await create_via_api(client, ADMIN_URL, headers, **(defaults | fields))


async def test_create_trims_text_flags_the_current_job_and_audits(
    api: AsyncClient, admin: User, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    job = await _create(
        api, admin_headers, company="  Acme  ", location="  ", start_date="2024-03-01"
    )

    assert (job["company"], job["location"], job["end_date"]) == ("Acme", None, None)
    assert job["is_current"] is True
    [entry] = await audit_entries(db_session, "experience.create")
    assert (entry.user_id, entry.entity_id) == (admin.id, job["id"])
    assert entry.details == {"company": "Acme", "position": "Developer"}


async def test_public_timeline_puts_current_jobs_first_then_newest(
    api: AsyncClient, admin_headers: dict[str, str]
) -> None:
    await _create(api, admin_headers, company="Old", start_date="2018-01-01", end_date="2020-01-01")
    await _create(api, admin_headers, company="Now", start_date="2023-01-01")
    await _create(
        api, admin_headers, company="Prev", start_date="2020-02-01", end_date="2022-12-01"
    )

    listed = (await api.get("/experiences")).json()
    searched = (await api.get("/experiences?q=pre")).json()
    second_page = (await api.get("/experiences?size=2&page=2")).json()

    assert [job["company"] for job in listed["items"]] == ["Now", "Prev", "Old"]
    assert [job["company"] for job in searched["items"]] == ["Prev"]
    assert ([job["company"] for job in second_page["items"]], second_page["pages"]) == (["Old"], 2)


@pytest.mark.parametrize(
    ("fields", "field"),
    [
        ({"company": ""}, "body.company"),
        ({"company": "x" * 201}, "body.company"),
        ({"start_date": "not a date"}, "body.start_date"),
        ({"end_date": "2023-12-31"}, "body.end_date"),  # before the start date
        ({"salary": 1}, "body.salary"),
    ],
)
async def test_create_validates(
    api: AsyncClient, admin_headers: dict[str, str], fields: dict[str, object], field: str
) -> None:
    body = {"company": "Acme", "position": "Dev", "start_date": "2024-01-01"} | fields

    response = await api.post(ADMIN_URL, json=body, headers=admin_headers)

    assert response.status_code == 422
    assert [detail["field"] for detail in response.json()["error"]["details"]] == [field]


async def test_patch_checks_dates_against_the_stored_ones_and_audits_changes(
    api: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    job = await _create(api, admin_headers, start_date="2024-01-01")
    url = f"{ADMIN_URL}/{job['id']}"

    early_end = await api.patch(url, json={"end_date": "2023-01-01"}, headers=admin_headers)
    late_start = await api.patch(
        url, json={"start_date": "2025-01-01", "end_date": "2024-06-01"}, headers=admin_headers
    )
    no_start = await api.patch(url, json={"start_date": None}, headers=admin_headers)
    ended = await api.patch(url, json={"end_date": "2024-06-30"}, headers=admin_headers)
    unchanged = await api.patch(url, json={"end_date": "2024-06-30"}, headers=admin_headers)

    assert early_end.json()["error"]["details"][0]["field"] == "body.end_date"
    assert late_start.status_code == 422
    assert no_start.status_code == 422
    assert ended.status_code == 200
    assert (ended.json()["end_date"], ended.json()["is_current"]) == ("2024-06-30", False)
    assert unchanged.status_code == 200
    [entry] = await audit_entries(db_session, "experience.update")  # the no-op wrote nothing
    assert entry.details == {"end_date": {"old": None, "new": "2024-06-30"}}


async def test_get_delete_and_404(
    api: AsyncClient, admin_headers: dict[str, str], db_session: AsyncSession
) -> None:
    job = await _create(api, admin_headers, start_date="2024-01-01")
    url = f"{ADMIN_URL}/{job['id']}"

    fetched = await api.get(url, headers=admin_headers)
    deleted = await api.delete(url, headers=admin_headers)
    gone = await api.get(url, headers=admin_headers)
    missing = [
        await api.patch(f"{ADMIN_URL}/999999999", json={"company": "x"}, headers=admin_headers),
        await api.delete(f"{ADMIN_URL}/999999999", headers=admin_headers),
    ]

    assert fetched.json()["company"] == "Acme"
    assert (deleted.status_code, gone.status_code) == (204, 404)
    assert [response.status_code for response in missing] == [404, 404]
    assert (await api.get("/experiences")).json()["items"] == []
    [entry] = await audit_entries(db_session, "experience.delete")
    assert entry.entity_id == job["id"]
