from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UnsignedBigInt


class BlogPostTag(Base):
    """Links blog posts and tags (`BlogPost.tags`). Composite primary key, no timestamps."""

    __tablename__ = "blog_post_tags"

    post_id: Mapped[int] = mapped_column(
        UnsignedBigInt, ForeignKey("blog_posts.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        UnsignedBigInt, ForeignKey("blog_tags.id", ondelete="CASCADE"), primary_key=True
    )
