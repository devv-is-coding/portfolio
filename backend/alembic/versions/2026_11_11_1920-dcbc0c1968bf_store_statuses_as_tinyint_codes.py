"""store statuses as tinyint codes

Revision ID: dcbc0c1968bf
Revises: 4dd7d371a212
Create Date: 2026-11-11 19:20:44.014005

Hand-written: the status columns of projects, blog_posts and contact_messages change
from VARCHAR(20) values to TINYINT UNSIGNED codes. Existing rows are converted in
place (so the status indexes stay), and the check constraints that compare statuses
are re-created for the new values. The codes are written out here rather than imported
from app/models/enums.py, so this migration never changes.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dcbc0c1968bf"
down_revision: str | Sequence[str] | None = "4dd7d371a212"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PUBLICATION_CODES = {"draft": 0, "published": 1, "archived": 2}
CONTACT_CODES = {"unread": 0, "read": 1, "replied": 2, "archived": 3}
# table -> (codes, default value, has the published_at_required check)
TABLES = {
    "projects": (PUBLICATION_CODES, "draft", True),
    "blog_posts": (PUBLICATION_CODES, "draft", True),
    "contact_messages": (CONTACT_CODES, "unread", False),
}


def _case(mapping: dict[str, str]) -> str:
    """`CASE status WHEN 'a' THEN 'b' … END`. No ELSE: an unknown value becomes NULL
    and fails the NOT NULL column, so the migration stops instead of guessing."""
    whens = " ".join(f"WHEN '{old}' THEN '{new}'" for old, new in mapping.items())
    return f"CASE status {whens} END"


def _drop_checks(table: str, has_published_check: bool) -> None:
    if has_published_check:
        op.drop_constraint(op.f(f"ck_{table}_published_at_required"), table, type_="check")
    op.drop_constraint(op.f(f"ck_{table}_status"), table, type_="check")


def upgrade() -> None:
    for table, (codes, default, has_published_check) in TABLES.items():
        _drop_checks(table, has_published_check)
        op.execute(f"UPDATE {table} SET status = {_case({k: str(v) for k, v in codes.items()})}")
        op.alter_column(
            table,
            "status",
            existing_type=sa.String(length=20),
            type_=mysql.TINYINT(unsigned=True),
            existing_nullable=False,
            server_default=sa.text(str(codes[default])),
        )
        allowed = ", ".join(str(code) for code in sorted(codes.values()))
        op.create_check_constraint(op.f(f"ck_{table}_status"), table, f"status IN ({allowed})")
        if has_published_check:
            op.create_check_constraint(
                op.f(f"ck_{table}_published_at_required"),
                table,
                f"status <> {codes['published']} OR published_at IS NOT NULL",
            )


def downgrade() -> None:
    for table, (codes, default, has_published_check) in TABLES.items():
        _drop_checks(table, has_published_check)
        op.alter_column(
            table,
            "status",
            existing_type=mysql.TINYINT(unsigned=True),
            type_=sa.String(length=20),
            existing_nullable=False,
            server_default=default,
        )
        op.execute(f"UPDATE {table} SET status = {_case({str(v): k for k, v in codes.items()})}")
        allowed = ", ".join(f"'{value}'" for value in codes)
        op.create_check_constraint(op.f(f"ck_{table}_status"), table, f"status IN ({allowed})")
        if has_published_check:
            op.create_check_constraint(
                op.f(f"ck_{table}_published_at_required"),
                table,
                "status <> 'published' OR published_at IS NOT NULL",
            )
