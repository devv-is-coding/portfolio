"""Schema conventions every model must follow (checked on the metadata, no database)."""

import pytest
from sqlalchemy import Table

from app.models import Base
from app.models.base import TABLE_OPTIONS

TABLES = sorted(Base.metadata.tables.values(), key=lambda table: table.name)


def _ids(table: Table) -> str:
    return table.name


def test_every_table_is_registered() -> None:
    """A model missing from app/models/__init__.py is invisible to Alembic autogenerate."""
    assert Base.metadata.tables.keys() == {"users", "refresh_tokens"}


@pytest.mark.parametrize("table", TABLES, ids=_ids)
def test_table_uses_innodb_utf8mb4_and_uca1400_collation(table: Table) -> None:
    for option, value in TABLE_OPTIONS.items():
        assert table.kwargs.get(option) == value, (
            f"{table.name}: end __table_args__ with TABLE_OPTIONS"
        )


def _is_association_table(table: Table) -> bool:
    """Pure link tables (`project_skills`): the primary key is all foreign keys."""
    return all(column.foreign_keys for column in table.primary_key.columns)


@pytest.mark.parametrize("table", TABLES, ids=_ids)
def test_table_has_timestamps(table: Table) -> None:
    if _is_association_table(table):
        pytest.skip("association tables have no timestamps")
    for name in ("created_at", "updated_at"):
        column = table.columns[name]
        assert not column.nullable
        assert column.server_default is not None


@pytest.mark.parametrize("table", TABLES, ids=_ids)
def test_every_foreign_key_declares_on_delete(table: Table) -> None:
    for foreign_key in table.foreign_keys:
        assert foreign_key.ondelete in {"CASCADE", "SET NULL", "RESTRICT"}, (
            f"{table.name}.{foreign_key.parent.name}: set ondelete= explicitly"
        )
