"""SQLAlchemy models.

Import every model module here. Alembic's autogenerate only sees models that are
imported when `app.models` is loaded (alembic/env.py uses `Base.metadata`).
"""

from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.blog_category import BlogCategory
from app.models.blog_post import BlogPost
from app.models.blog_post_tag import BlogPostTag
from app.models.blog_tag import BlogTag
from app.models.certification import Certification
from app.models.contact_message import ContactMessage
from app.models.education import Education
from app.models.experience import Experience
from app.models.media import Media
from app.models.profile import Profile
from app.models.project import Project
from app.models.project_image import ProjectImage
from app.models.project_skill import ProjectSkill
from app.models.refresh_token import RefreshToken
from app.models.site_setting import SiteSetting
from app.models.skill import Skill
from app.models.social_link import SocialLink
from app.models.user import User

__all__ = [
    "AuditLog",
    "Base",
    "BlogCategory",
    "BlogPost",
    "BlogPostTag",
    "BlogTag",
    "Certification",
    "ContactMessage",
    "Education",
    "Experience",
    "Media",
    "Profile",
    "Project",
    "ProjectImage",
    "ProjectSkill",
    "RefreshToken",
    "SiteSetting",
    "Skill",
    "SocialLink",
    "User",
]
