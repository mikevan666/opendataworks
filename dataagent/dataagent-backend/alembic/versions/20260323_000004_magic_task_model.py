"""switch to magic task model

Revision ID: 20260323_000004
Revises: 20260312_000003
Create Date: 2026-03-23 10:30:00
"""
from __future__ import annotations

from alembic import op


revision = "20260323_000004"
down_revision = "20260312_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS da_chat_event")
    op.execute("DROP TABLE IF EXISTS da_chat_block")
    op.execute("DROP TABLE IF EXISTS da_chat_run")
    op.execute("DROP TABLE IF EXISTS da_chat_message")
    op.execute("DROP TABLE IF EXISTS da_chat_session")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS da_agent_topic (
            topic_id VARCHAR(64) NOT NULL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            chat_topic_id VARCHAR(64) NOT NULL,
            chat_conversation_id VARCHAR(64) NOT NULL,
            current_task_id VARCHAR(64) NULL,
            current_task_status VARCHAR(32) NULL,
            last_message_seq BIGINT NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_da_agent_topic_chat_topic (chat_topic_id),
            KEY idx_da_agent_topic_updated (updated_at),
            KEY idx_da_agent_topic_current_task (current_task_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS da_agent_task (
            task_id VARCHAR(64) NOT NULL PRIMARY KEY,
            topic_id VARCHAR(64) NOT NULL,
            from_task_id VARCHAR(64) NULL,
            source_queue_id VARCHAR(64) NULL,
            source_schedule_id VARCHAR(64) NULL,
            source_schedule_log_id VARCHAR(64) NULL,
            task_status VARCHAR(32) NOT NULL DEFAULT 'waiting',
            prompt LONGTEXT NOT NULL,
            provider_id VARCHAR(64) NOT NULL,
            model_name VARCHAR(255) NOT NULL,
            database_hint VARCHAR(255) NULL,
            debug_enabled TINYINT(1) NOT NULL DEFAULT 0,
            timeout_seconds INT NOT NULL DEFAULT 0,
            sql_read_timeout_seconds INT NOT NULL DEFAULT 0,
            sql_write_timeout_seconds INT NOT NULL DEFAULT 0,
            last_event_seq BIGINT NOT NULL DEFAULT 0,
            cancel_requested_at DATETIME NULL,
            started_at DATETIME NULL,
            heartbeat_at DATETIME NULL,
            finished_at DATETIME NULL,
            error_json LONGTEXT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_da_agent_task_topic_created (topic_id, created_at),
            KEY idx_da_agent_task_status_updated (task_status, updated_at),
            KEY idx_da_agent_task_parent (from_task_id),
            KEY idx_da_agent_task_source_queue (source_queue_id),
            KEY idx_da_agent_task_source_schedule (source_schedule_id),
            KEY idx_da_agent_task_source_schedule_log (source_schedule_log_id),
            CONSTRAINT fk_da_agent_task_topic
                FOREIGN KEY (topic_id) REFERENCES da_agent_topic(topic_id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS da_agent_message (
            message_id VARCHAR(64) NOT NULL PRIMARY KEY,
            topic_id VARCHAR(64) NOT NULL,
            task_id VARCHAR(64) NULL,
            sender_type VARCHAR(16) NOT NULL,
            type VARCHAR(64) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'success',
            content LONGTEXT NOT NULL,
            event VARCHAR(64) NOT NULL DEFAULT '',
            steps_json LONGTEXT NULL,
            tool_json LONGTEXT NULL,
            seq_id BIGINT NOT NULL DEFAULT 0,
            correlation_id VARCHAR(128) NULL,
            parent_correlation_id VARCHAR(128) NULL,
            content_type VARCHAR(64) NULL,
            usage_json LONGTEXT NULL,
            error_json LONGTEXT NULL,
            show_in_ui TINYINT(1) NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            KEY idx_da_agent_message_topic_seq (topic_id, show_in_ui, seq_id),
            KEY idx_da_agent_message_task_seq (task_id, show_in_ui, seq_id),
            KEY idx_da_agent_message_task_ui (task_id, sender_type, show_in_ui),
            KEY idx_da_agent_message_correlation (correlation_id),
            CONSTRAINT fk_da_agent_message_topic
                FOREIGN KEY (topic_id) REFERENCES da_agent_topic(topic_id)
                ON DELETE CASCADE,
            CONSTRAINT fk_da_agent_message_task
                FOREIGN KEY (task_id) REFERENCES da_agent_task(task_id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS da_agent_chunk (
            id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            topic_id VARCHAR(64) NOT NULL,
            task_id VARCHAR(64) NOT NULL,
            seq_id BIGINT NOT NULL DEFAULT 0,
            request_id VARCHAR(128) NOT NULL,
            chunk_id BIGINT NOT NULL,
            content LONGTEXT NULL,
            delta_status VARCHAR(16) NOT NULL,
            finish_reason VARCHAR(64) NULL,
            delta_extra_json LONGTEXT NULL,
            correlation_id VARCHAR(128) NULL,
            parent_correlation_id VARCHAR(128) NULL,
            model_id VARCHAR(255) NULL,
            content_type VARCHAR(64) NULL,
            metadata_extra_json LONGTEXT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            KEY idx_da_agent_chunk_task_seq (task_id, seq_id),
            KEY idx_da_agent_chunk_topic_seq (topic_id, seq_id),
            KEY idx_da_agent_chunk_correlation (correlation_id),
            CONSTRAINT fk_da_agent_chunk_topic
                FOREIGN KEY (topic_id) REFERENCES da_agent_topic(topic_id)
                ON DELETE CASCADE,
            CONSTRAINT fk_da_agent_chunk_task
                FOREIGN KEY (task_id) REFERENCES da_agent_task(task_id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )

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
    op.execute("DROP TABLE IF EXISTS da_agent_chunk")
    op.execute("DROP TABLE IF EXISTS da_agent_message")
    op.execute("DROP TABLE IF EXISTS da_agent_task")
    op.execute("DROP TABLE IF EXISTS da_agent_topic")
