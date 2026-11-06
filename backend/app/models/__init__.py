"""SQLAlchemy models.

Import every model module here. Alembic's autogenerate only sees models that are
imported when `app.models` is loaded (alembic/env.py uses `Base.metadata`).

    from app.models.user import User
"""

from app.models.base import Base

__all__ = ["Base"]
