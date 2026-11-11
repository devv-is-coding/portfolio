from app.models import SocialLink
from app.repositories.base import BaseRepository


class SocialLinkRepository(BaseRepository[SocialLink]):
    model = SocialLink
