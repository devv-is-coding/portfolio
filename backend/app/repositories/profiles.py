from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Profile
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    model = Profile

    async def get_with_details(self, profile_id: int) -> Profile | None:
        """The profile with its avatar, resume and social links loaded (fresh from the
        database, also when the session already holds the row)."""
        return await self.session.scalar(
            select(Profile)
            .where(Profile.id == profile_id)
            .options(
                selectinload(Profile.avatar),
                selectinload(Profile.resume),
                selectinload(Profile.social_links),
            )
            .execution_options(populate_existing=True)
        )
