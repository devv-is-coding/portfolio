from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UnsignedBigInt


class ProjectSkill(Base):
    """Links projects and skills (`Project.skills`). Composite primary key, no timestamps."""

    __tablename__ = "project_skills"

    project_id: Mapped[int] = mapped_column(
        UnsignedBigInt, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        UnsignedBigInt, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
