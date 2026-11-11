"""Test data builders for integration tests. Plain functions, no factory library.

Add a builder here when a second test needs the same kind of row.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token
from app.models import Media, User
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
