"""add chat run table

Revision ID: 20260312_000003
Revises: 20260310_000002
Create Date: 2026-03-12 15:20:00
"""
from __future__ import annotations

from alembic import op


revision = "20260312_000003"
down_revision = "20260310_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS da_chat_run (
            run_id VARCHAR(64) NOT NULL PRIMARY KEY,
            session_id VARCHAR(64) NOT NULL,
            user_message_id VARCHAR(64) NOT NULL,
            assistant_message_id VARCHAR(64) NOT NULL,
            mode VARCHAR(16) NOT NULL DEFAULT 'interactive',
            status VARCHAR(32) NOT NULL DEFAULT 'queued',
            provider_id VARCHAR(64) NOT NULL,
            model_name VARCHAR(255) NOT NULL,
            question LONGTEXT NOT NULL,
            history_json LONGTEXT NULL,
            database_hint VARCHAR(255) NULL,
            debug_enabled TINYINT(1) NOT NULL DEFAULT 0,
            timeout_seconds INT NOT NULL DEFAULT 0,
            idle_timeout_seconds INT NOT NULL DEFAULT 0,
            wait_timeout_seconds INT NOT NULL DEFAULT 0,
            sql_read_timeout_seconds INT NOT NULL DEFAULT 0,
            sql_write_timeout_seconds INT NOT NULL DEFAULT 0,
            last_event_seq INT NOT NULL DEFAULT 0,
            error_json LONGTEXT NULL,
            started_at DATETIME NULL,
            heartbeat_at DATETIME NULL,
            finished_at DATETIME NULL,
            cancel_requested_at DATETIME NULL,
            lease_owner VARCHAR(128) NULL,
            lease_expires_at DATETIME NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_chat_run_session (session_id, created_at),
            KEY idx_chat_run_status_lease (status, lease_expires_at, created_at),
            KEY idx_chat_run_assistant_message (assistant_message_id),
            CONSTRAINT fk_da_chat_run_session
                FOREIGN KEY (session_id) REFERENCES da_chat_session(session_id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS da_chat_run")
