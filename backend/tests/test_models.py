"""Schema conventions every model must follow (checked on the metadata, no database)."""

from collections.abc import Mapping
from enum import StrEnum

import pytest
from sqlalchemy import Table

from app.models import Base
from app.models.base import TABLE_OPTIONS, StatusCode
from app.models.enums import CONTACT_MESSAGE_STATUS_CODES, PUBLICATION_STATUS_CODES

TABLES = sorted(Base.metadata.tables.values(), key=lambda table: table.name)


def _ids(table: Table) -> str:
    return table.name


def test_every_table_is_registered() -> None:
    """A model missing from app/models/__init__.py is invisible to Alembic autogenerate."""
    assert Base.metadata.tables.keys() == {
        "users",
        "refresh_tokens",
        "media",
        "profiles",
        "social_links",
        "skills",
        "projects",
        "project_images",
        "project_skills",
        "experiences",
        "education",
        "certifications",
        "blog_categories",
        "blog_posts",
        "blog_tags",
        "blog_post_tags",
        "contact_messages",
        "site_settings",
        "audit_logs",
    }


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


STATUS_TABLES = [table for table in TABLES if "status" in table.columns]


def test_the_status_tables() -> None:
    assert [table.name for table in STATUS_TABLES] == [
        "blog_posts",
        "contact_messages",
        "projects",
    ]


@pytest.mark.parametrize("table", STATUS_TABLES, ids=_ids)
def test_status_is_a_tinyint_code_for_every_member(table: Table) -> None:
    column_type = table.columns["status"].type
    assert isinstance(column_type, StatusCode), f"{table.name}: use status_column(...)"
    codes: dict[StrEnum, int] = dict(column_type.codes)
    enum: type[StrEnum] = type(next(iter(codes)))
    assert set(codes) == set(enum), f"{enum.__name__}: every member needs a code"
    assert len(set(codes.values())) == len(codes), f"{enum.__name__}: codes must be unique"


@pytest.mark.parametrize(
    ("codes", "expected"),
    [
        (PUBLICATION_STATUS_CODES, {"draft": 0, "published": 1, "archived": 2}),
        (CONTACT_MESSAGE_STATUS_CODES, {"unread": 0, "read": 1, "replied": 2, "archived": 3}),
    ],
)
def test_status_codes_never_change(codes: Mapping[StrEnum, int], expected: dict[str, int]) -> None:
    """Stored rows keep their numbers: renumbering a member would silently change them."""
    assert {member.value: code for member, code in codes.items()} == expected
