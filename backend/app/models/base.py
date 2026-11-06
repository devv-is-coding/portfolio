from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Enum, MetaData, text
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Deterministic constraint names, so Alembic autogenerate produces stable,
# reversible migrations (MariaDB needs names to drop constraints).
# `column_0_N_name` joins every column, so composite indexes get distinct names:
# ix_refresh_tokens_user_id_expires_at.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Every table: InnoDB, utf8mb4, and MariaDB's current Unicode collation
# (accent- and case-insensitive, so `A@x.com` and `a@x.com` collide on UNIQUE).
TABLE_OPTIONS: dict[str, Any] = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_uca1400_ai_ci",
}

# Primary and foreign keys are BIGINT UNSIGNED; a foreign key column must use the
# same type as the key it references.
UnsignedBigInt = BIGINT(unsigned=True)


def status_enum(enum: type[StrEnum]) -> Enum:
    """A status column: VARCHAR(20) + CHECK constraint `ck_<table>_status`, not a native ENUM.

    Stores the member values (`"draft"`), not the names (`"DRAFT"`). Adding a value later
    needs a migration that drops and re-creates the check constraint by hand; Alembic
    doesn't detect check constraint changes.
    """
    return Enum(
        enum,
        name="status",
        native_enum=False,
        create_constraint=True,
        length=20,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Models that need their own `__table_args__` (indexes, check constraints) must end
    the tuple with `TABLE_OPTIONS`: `__table_args__ = (Index(...), TABLE_OPTIONS)`.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    __table_args__: Any = TABLE_OPTIONS


class IdMixin:
    """`id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY`."""

    # sort_order: `id` is the first column, timestamps the last.
    id: Mapped[int] = mapped_column(
        UnsignedBigInt, primary_key=True, autoincrement=True, sort_order=-10
    )


class TimestampMixin:
    """`created_at` / `updated_at`, set by MariaDB (UTC, see app/core/database.py).

    `updated_at` uses `ON UPDATE CURRENT_TIMESTAMP`, so it also changes on updates
    that don't go through the ORM. Values are naive datetimes in UTC.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), sort_order=10
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        sort_order=10,
    )
