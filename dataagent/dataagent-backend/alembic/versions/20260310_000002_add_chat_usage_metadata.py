"""add chat usage metadata

Revision ID: 20260310_000002
Revises: 20260306_000001
Create Date: 2026-03-10 09:25:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260310_000002"
down_revision = "20260306_000001"
branch_labels = None
depends_on = None


def _current_schema() -> str:
    bind = op.get_bind()
    return str(bind.execute(sa.text("SELECT DATABASE()")).scalar() or "").strip()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    schema = _current_schema()
    row = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :schema
              AND TABLE_NAME = :table_name
              AND COLUMN_NAME = :column_name
            LIMIT 1
            """
        ),
        {"schema": schema, "table_name": table_name, "column_name": column_name},
    ).first()
    return row is not None


def upgrade() -> None:
    if not _column_exists("da_chat_message", "stop_reason"):
        op.execute("ALTER TABLE da_chat_message ADD COLUMN stop_reason VARCHAR(64) NULL AFTER status")
    if not _column_exists("da_chat_message", "stop_sequence"):
        op.execute("ALTER TABLE da_chat_message ADD COLUMN stop_sequence VARCHAR(255) NULL AFTER stop_reason")
    if not _column_exists("da_chat_message", "usage_json"):
        op.execute("ALTER TABLE da_chat_message ADD COLUMN usage_json LONGTEXT NULL AFTER content")


def downgrade() -> None:
    if _column_exists("da_chat_message", "usage_json"):
        op.execute("ALTER TABLE da_chat_message DROP COLUMN usage_json")
    if _column_exists("da_chat_message", "stop_sequence"):
        op.execute("ALTER TABLE da_chat_message DROP COLUMN stop_sequence")
    if _column_exists("da_chat_message", "stop_reason"):
        op.execute("ALTER TABLE da_chat_message DROP COLUMN stop_reason")
