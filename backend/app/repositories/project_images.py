from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import ProjectImage
from app.repositories.base import BaseRepository


class ProjectImageRepository(BaseRepository[ProjectImage]):
    model = ProjectImage

    async def get_for_project(self, project_id: int, image_id: int) -> ProjectImage | None:
        """The image, only when it belongs to that project."""
        return await self.session.scalar(
            select(ProjectImage)
            .where(ProjectImage.id == image_id, ProjectImage.project_id == project_id)
            .options(joinedload(ProjectImage.media))
            .execution_options(populate_existing=True)
        )
