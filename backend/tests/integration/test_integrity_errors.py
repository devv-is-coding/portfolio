"""Real MariaDB constraint errors reach the client as 409s in the shared shape."""

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionDep, get_session
from app.core.errors import register_exception_handlers
from app.models import Project, ProjectImage, Skill

pytestmark = pytest.mark.anyio


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/duplicate-slug")
    async def duplicate_slug(session: SessionDep) -> None:
        session.add(Skill(name="Python", slug="python"))
        await session.flush()
        session.add(Skill(name="Python 3", slug="PYTHON"))  # same slug, other case
        await session.flush()

    @app.post("/missing-reference")
    async def missing_reference(session: SessionDep) -> None:
        project = Project(title="Shop", slug="shop")
        session.add(project)
        await session.flush()
        session.add(ProjectImage(project_id=project.id, media_id=999_999_999))
        await session.flush()

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_duplicate_unique_value_is_409_duplicate(client: AsyncClient) -> None:
    response = await client.post("/duplicate-slug")

    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "conflict",
        "message": "A record with these values already exists",
        "details": None,
    }
    assert "uq_skills_slug" not in response.text


async def test_missing_foreign_key_is_409_conflict(client: AsyncClient) -> None:
    response = await client.post("/missing-reference")

    assert response.status_code == 409
    assert response.json()["error"]["message"] == "The request conflicts with existing data"
    assert "fk_" not in response.text
