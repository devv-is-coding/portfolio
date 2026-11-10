from sqlalchemy import select

from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        """Case-insensitive: the column's collation makes `A@x.com` match `a@x.com`."""
        return await self.session.scalar(select(User).where(User.email == email))
