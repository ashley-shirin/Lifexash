"""convert timestamps to utc

Data migration: no table changes. Until now, created_at / updated_at / completed_at were written in
the MySQL server's local time zone ('SYSTEM'). From this revision on the app writes UTC (see
core/database.py), so existing rows are converted to UTC too. DATE columns are not touched.

Run it together with the code change: rows written by the OLD code after this migration would stay in
local time. On an empty database (e.g. a fresh production DB) it changes nothing.

CONVERT_TZ with 'SYSTEM' and '+00:00' works without MySQL's time zone tables. It's exact for zones
without daylight saving time (like India, +05:30).

Revision ID: 81878a6609ca
Revises: 210aeb747de7
Create Date: 2026-09-26 16:22:41.823970

"""
from collections.abc import Sequence

from alembic import op


revision: str = '81878a6609ca'
down_revision: str | None = '210aeb747de7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# table → its timestamp columns
TIMESTAMP_COLUMNS = {
    "users": ["created_at"],
    "tasks": ["created_at", "updated_at", "completed_at"],
    "notes": ["created_at", "updated_at"],
    "journal_entries": ["created_at", "updated_at"],
}


def _convert(from_zone: str, to_zone: str) -> None:
    for table, columns in TIMESTAMP_COLUMNS.items():
        # updated_at is set explicitly in the same UPDATE, so "ON UPDATE CURRENT_TIMESTAMP" doesn't
        # overwrite it with the current time. CONVERT_TZ(NULL, …) stays NULL (open tasks).
        assignments = ", ".join(f"{col} = CONVERT_TZ({col}, '{from_zone}', '{to_zone}')" for col in columns)
        op.execute(f"UPDATE {table} SET {assignments}")


def upgrade() -> None:
    _convert("SYSTEM", "+00:00")


def downgrade() -> None:
    _convert("+00:00", "SYSTEM")
