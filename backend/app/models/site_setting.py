from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, TimestampMixin


class SiteSetting(IdMixin, TimestampMixin, Base):
    """A key/value site setting (e.g. `seo.default_title`). Never store secrets here."""

    __tablename__ = "site_settings"

    setting_key: Mapped[str] = mapped_column(String(150), unique=True)
    # Any JSON value: string, number, list or object.
    setting_value: Mapped[Any | None] = mapped_column(JSON)
