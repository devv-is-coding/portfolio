"""Test data builders for integration tests. Plain functions, no factory library.

Add a builder here when a second test needs the same kind of row.
"""

from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token
from app.models import AuditLog, Media, User
from app.services.auth import create_admin

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "correct horse battery staple"


async def create_admin_user(session: AsyncSession) -> User:
    """The admin through the real service (argon2 hash, audit entry)."""
    return await create_admin(session, ADMIN_EMAIL, ADMIN_PASSWORD)


def bearer_headers(user: User) -> dict[str, str]:
    """`Authorization` header with a valid access token, without a login round trip."""
    return {"Authorization": f"Bearer {create_access_token(user.id, get_settings())}"}


async def create_media(
    session: AsyncSession, file_id: str, mime_type: str = "image/webp", file_path: str = ""
) -> Media:
    """A registered media file (no ImageKit call: the row as `POST /admin/media` stores it)."""
    is_image = mime_type.startswith("image/")
    media = Media(
        file_id=file_id,
        file_path=file_path or f"/test/{file_id}",
        mime_type=mime_type,
        size_bytes=1024,
        width=800 if is_image else None,
        height=600 if is_image else None,
    )
    session.add(media)
    await session.flush()
    return media


async def audit_entries(session: AsyncSession, action: str) -> list[AuditLog]:
    """The audit rows with this action, e.g. `skill.create`, oldest first."""
    statement = select(AuditLog).where(AuditLog.action == action).order_by(AuditLog.id)
    return list((await session.scalars(statement)).all())


async def create_via_api(
    client: AsyncClient, path: str, headers: dict[str, str], **fields: object
) -> dict[str, Any]:
    """POST `fields` to an admin create endpoint and return the created JSON (asserts 201)."""
    response = await client.post(path, json=fields, headers=headers)
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body
