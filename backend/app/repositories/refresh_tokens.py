from datetime import datetime

from sqlalchemy import CursorResult, delete, select, update

from app.models import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    async def get_by_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        """Lock the row (SELECT ... FOR UPDATE), so two concurrent refreshes with the
        same token can't both rotate it."""
        return await self.session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
        )

    async def revoke_all_for_user(self, user_id: int, revoked_at: datetime) -> None:
        """Revoke every live token of the user; already revoked ones keep their time."""
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
        )

    async def delete_expired_before(self, cutoff: datetime) -> int:
        """Delete the tokens that expired before `cutoff`; returns how many."""
        result = await self.session.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < cutoff)
        )
        if not isinstance(result, CursorResult):  # a DELETE always returns one
            raise TypeError(f"unexpected result type {type(result).__name__}")
        return result.rowcount
