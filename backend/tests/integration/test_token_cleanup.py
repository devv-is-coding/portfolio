from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import utc_now
from app.models import RefreshToken, User
from app.services.auth import REFRESH_TOKEN_RETENTION, cleanup_refresh_tokens

pytestmark = pytest.mark.anyio


async def test_deletes_only_tokens_expired_beyond_the_retention(
    db_session: AsyncSession, admin: User
) -> None:
    now = utc_now()
    week = REFRESH_TOKEN_RETENTION
    tokens = {
        "expired long ago": RefreshToken(expires_at=now - week - timedelta(days=1)),
        "expired and revoked long ago": RefreshToken(
            expires_at=now - week - timedelta(hours=1), revoked_at=now - timedelta(days=30)
        ),
        "expired recently": RefreshToken(expires_at=now - week + timedelta(hours=1)),
        # Still unexpired: kept, so reusing it is still detected as theft.
        "revoked long ago, not expired": RefreshToken(
            expires_at=now + timedelta(days=1), revoked_at=now - timedelta(days=20)
        ),
        "live": RefreshToken(expires_at=now + timedelta(days=30)),
    }
    for index, token in enumerate(tokens.values()):
        token.user_id = admin.id
        token.token_hash = f"{index:064d}"
    db_session.add_all(tokens.values())
    await db_session.flush()
    kept_ids = {
        tokens[name].id for name in ("expired recently", "revoked long ago, not expired", "live")
    }

    deleted = await cleanup_refresh_tokens(db_session)
    remaining = set((await db_session.scalars(select(RefreshToken.id))).all())

    assert deleted == 2
    assert remaining == kept_ids
    assert await cleanup_refresh_tokens(db_session) == 0  # nothing left to delete
