"""add message queue and schedule tables

Revision ID: 20260323_000005
Revises: 20260323_000004
Create Date: 2026-03-23 14:05:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "20260323_000005"
down_revision = "20260323_000004"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(column.get("name") == column_name for column in inspector.get_columns(table_name))


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if not _has_column("da_agent_task", "source_queue_id"):
        op.add_column("da_agent_task", sa.Column("source_queue_id", sa.String(length=64), nullable=True))
    if not _has_column("da_agent_task", "source_schedule_id"):
        op.add_column("da_agent_task", sa.Column("source_schedule_id", sa.String(length=64), nullable=True))
    if not _has_column("da_agent_task", "source_schedule_log_id"):
        op.add_column("da_agent_task", sa.Column("source_schedule_log_id", sa.String(length=64), nullable=True))

    if not _has_index("da_agent_task", "idx_da_agent_task_source_queue"):
        op.create_index("idx_da_agent_task_source_queue", "da_agent_task", ["source_queue_id"], unique=False)
    if not _has_index("da_agent_task", "idx_da_agent_task_source_schedule"):
        op.create_index("idx_da_agent_task_source_schedule", "da_agent_task", ["source_schedule_id"], unique=False)
    if not _has_index("da_agent_task", "idx_da_agent_task_source_schedule_log"):
        op.create_index("idx_da_agent_task_source_schedule_log", "da_agent_task", ["source_schedule_log_id"], unique=False)

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS da_agent_message_queue (
            queue_id VARCHAR(64) NOT NULL PRIMARY KEY,
            topic_id VARCHAR(64) NOT NULL,
            source_schedule_id VARCHAR(64) NULL,
            source_schedule_log_id VARCHAR(64) NULL,
            message_type VARCHAR(64) NOT NULL,
            message_content_json LONGTEXT NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'queued',
            last_task_id VARCHAR(64) NULL,
            error_message TEXT NULL,
            consumed_at DATETIME NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_da_agent_message_queue_topic_created (topic_id, created_at),
            KEY idx_da_agent_message_queue_status_updated (status, updated_at),
            KEY idx_da_agent_message_queue_last_task (last_task_id),
            KEY idx_da_agent_message_queue_source_schedule (source_schedule_id),
            CONSTRAINT fk_da_agent_message_queue_topic
                FOREIGN KEY (topic_id) REFERENCES da_agent_topic(topic_id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS da_agent_message_schedule (
            schedule_id VARCHAR(64) NOT NULL PRIMARY KEY,
            topic_id VARCHAR(64) NOT NULL,
            name VARCHAR(255) NOT NULL,
            message_type VARCHAR(64) NOT NULL,
            message_content_json LONGTEXT NOT NULL,
            cron_expr VARCHAR(128) NOT NULL,
            timezone VARCHAR(64) NOT NULL,
            enabled TINYINT(1) NOT NULL DEFAULT 1,
            last_task_id VARCHAR(64) NULL,
            last_queue_id VARCHAR(64) NULL,
            last_run_at DATETIME NULL,
            next_run_at DATETIME NULL,
            last_error_message TEXT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_da_agent_message_schedule_topic_updated (topic_id, updated_at),
            KEY idx_da_agent_message_schedule_enabled_next (enabled, next_run_at),
            CONSTRAINT fk_da_agent_message_schedule_topic
                FOREIGN KEY (topic_id) REFERENCES da_agent_topic(topic_id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS da_agent_message_schedule_log (
            schedule_log_id VARCHAR(64) NOT NULL PRIMARY KEY,
            schedule_id VARCHAR(64) NOT NULL,
            queue_id VARCHAR(64) NULL,
            task_id VARCHAR(64) NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'running',
            error_message TEXT NULL,
            started_at DATETIME NULL,
            finished_at DATETIME NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            KEY idx_da_agent_message_schedule_log_schedule_created (schedule_id, created_at),
            KEY idx_da_agent_message_schedule_log_task (task_id),
            CONSTRAINT fk_da_agent_message_schedule_log_schedule
                FOREIGN KEY (schedule_id) REFERENCES da_agent_message_schedule(schedule_id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS da_agent_message_schedule_log")
    op.execute("DROP TABLE IF EXISTS da_agent_message_schedule")
    op.execute("DROP TABLE IF EXISTS da_agent_message_queue")

    if _has_index("da_agent_task", "idx_da_agent_task_source_schedule_log"):
        op.drop_index("idx_da_agent_task_source_schedule_log", table_name="da_agent_task")
    if _has_index("da_agent_task", "idx_da_agent_task_source_schedule"):
        op.drop_index("idx_da_agent_task_source_schedule", table_name="da_agent_task")
    if _has_index("da_agent_task", "idx_da_agent_task_source_queue"):
        op.drop_index("idx_da_agent_task_source_queue", table_name="da_agent_task")

    if _has_column("da_agent_task", "source_schedule_log_id"):
        op.drop_column("da_agent_task", "source_schedule_log_id")
    if _has_column("da_agent_task", "source_schedule_id"):
        op.drop_column("da_agent_task", "source_schedule_id")
    if _has_column("da_agent_task", "source_queue_id"):
        op.drop_column("da_agent_task", "source_queue_id")
