from __future__ import annotations

"""
NL2SQL 会话与运行存储（MySQL 持久化）
- 新表前缀: da_*
- 旧 aq_* 表保留但不再写入
"""

import json
import logging
import threading
from datetime import datetime
from typing import Any

import pymysql

from config import get_settings

logger = logging.getLogger(__name__)


def _to_iso(value) -> str:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    return str(value) if value is not None else ""


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    return str(value)


def _safe_json_load(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


class SessionStore:
    def __init__(self):
        self._ready = False
        self._ready_lock = threading.Lock()

    def _connect(self, database: str | None):
        cfg = get_settings()
        return pymysql.connect(
            host=cfg.mysql_host,
            port=cfg.mysql_port,
            user=cfg.mysql_user,
            password=cfg.mysql_password,
            database=database,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )

    def _schema_name(self) -> str:
        cfg = get_settings()
        return cfg.session_mysql_database

    def init_schema(self):
        if self._ready:
            return
        with self._ready_lock:
            if self._ready:
                return
            self._ready = True
            logger.info("Session store is ready; schema is expected to be managed by Alembic")

    def _ensure_ready(self):
        if not self._ready:
            self.init_schema()

    def create_session(self, session_id: str, title: str) -> dict[str, Any]:
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO da_chat_session (session_id, title)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE title = VALUES(title), updated_at = CURRENT_TIMESTAMP
                    """,
                    (session_id, title),
                )
            conn.commit()
        finally:
            conn.close()
        return self.get_session(session_id) or {}

    def update_session_title(self, session_id: str, title: str):
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE da_chat_session SET title = %s, updated_at = CURRENT_TIMESTAMP WHERE session_id = %s",
                    (title, session_id),
                )
            conn.commit()
        finally:
            conn.close()

    def append_user_message(self, *, session_id: str, message_id: str, content: str) -> dict[str, Any]:
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO da_chat_message (
                        message_id, session_id, role, status, content
                    ) VALUES (%s, %s, 'user', 'success', %s)
                    """,
                    (message_id, session_id, content or ""),
                )
                cur.execute(
                    "UPDATE da_chat_session SET updated_at = CURRENT_TIMESTAMP WHERE session_id = %s",
                    (session_id,),
                )
            conn.commit()
        finally:
            conn.close()
        return {
            "message_id": message_id,
            "role": "user",
            "content": content or "",
            "status": "success",
        }

    def update_message_status(
        self,
        *,
        message_id: str,
        status: str,
        provider_id: str | None = None,
        model: str | None = None,
    ):
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE da_chat_message
                    SET status = %s,
                        provider_id = COALESCE(%s, provider_id),
                        model_name = COALESCE(%s, model_name),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE message_id = %s
                    """,
                    (status, provider_id, model, message_id),
                )
            conn.commit()
        finally:
            conn.close()

    def save_assistant_message(
        self,
        *,
        session_id: str,
        message_id: str,
        run_id: str,
        content: str,
        status: str,
        stop_reason: str | None,
        stop_sequence: str | None,
        usage: dict[str, Any] | None,
        blocks: list[dict[str, Any]],
        error: dict[str, Any] | None,
        provider_id: str,
        model: str,
    ) -> dict[str, Any]:
        self._ensure_ready()
        error_json = json.dumps(error, ensure_ascii=False, default=_json_default) if error else None
        usage_json = json.dumps(usage, ensure_ascii=False, default=_json_default) if usage else None

        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO da_chat_message (
                        message_id, session_id, role, status, stop_reason, stop_sequence, run_id, content,
                        usage_json, error_json, provider_id, model_name
                    ) VALUES (%s, %s, 'assistant', %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        status = VALUES(status),
                        stop_reason = VALUES(stop_reason),
                        stop_sequence = VALUES(stop_sequence),
                        run_id = VALUES(run_id),
                        content = VALUES(content),
                        usage_json = VALUES(usage_json),
                        error_json = VALUES(error_json),
                        provider_id = VALUES(provider_id),
                        model_name = VALUES(model_name),
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        message_id,
                        session_id,
                        status,
                        stop_reason,
                        stop_sequence,
                        run_id,
                        content or "",
                        usage_json,
                        error_json,
                        provider_id,
                        model,
                    ),
                )

                cur.execute("DELETE FROM da_chat_block WHERE message_id = %s", (message_id,))
                for idx, block in enumerate(blocks):
                    block_id = str(block.get("block_id") or f"b_{idx}")
                    block_type = str(block.get("type") or "unknown")
                    block_status = str(block.get("status") or "success")
                    content_json = json.dumps(block, ensure_ascii=False, default=_json_default)
                    cur.execute(
                        """
                        INSERT INTO da_chat_block (message_id, block_id, block_type, status, content_json, seq)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (message_id, block_id, block_type, block_status, content_json, idx),
                    )

                cur.execute(
                    "UPDATE da_chat_session SET updated_at = CURRENT_TIMESTAMP WHERE session_id = %s",
                    (session_id,),
                )
            conn.commit()
        finally:
            conn.close()

        return {
            "message_id": message_id,
            "role": "assistant",
            "run_id": run_id,
            "status": status,
            "content": content or "",
            "stop_reason": stop_reason,
            "stop_sequence": stop_sequence,
            "usage": usage,
            "blocks": blocks,
            "error": error,
            "provider_id": provider_id,
            "model": model,
        }

    def append_run_event(
        self,
        *,
        session_id: str,
        message_id: str,
        run_id: str,
        event: dict[str, Any],
    ):
        self._ensure_ready()
        seq = int(event.get("seq") or 0)
        event_type = str(event.get("type") or "")
        payload = event.get("payload") or {}
        payload_json = json.dumps(payload, ensure_ascii=False, default=_json_default)

        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO da_chat_event (run_id, session_id, message_id, seq, event_type, payload_json)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (run_id, session_id, message_id, seq, event_type, payload_json),
                )
                cur.execute(
                    """
                    UPDATE da_chat_run
                    SET last_event_seq = GREATEST(last_event_seq, %s),
                        heartbeat_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE run_id = %s
                    """,
                    (seq, run_id),
                )
            conn.commit()
        finally:
            conn.close()

    def save_run_events(
        self,
        *,
        session_id: str,
        message_id: str,
        run_id: str,
        events: list[dict[str, Any]],
    ):
        if not events:
            return
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                last_seq = 0
                for event in events:
                    seq = int(event.get("seq") or 0)
                    last_seq = max(last_seq, seq)
                    event_type = str(event.get("type") or "")
                    payload = event.get("payload") or {}
                    payload_json = json.dumps(payload, ensure_ascii=False, default=_json_default)
                    cur.execute(
                        """
                        INSERT INTO da_chat_event (run_id, session_id, message_id, seq, event_type, payload_json)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (run_id, session_id, message_id, seq, event_type, payload_json),
                    )
                cur.execute(
                    """
                    UPDATE da_chat_run
                    SET last_event_seq = GREATEST(last_event_seq, %s),
                        heartbeat_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE run_id = %s
                    """,
                    (last_seq, run_id),
                )
            conn.commit()
        finally:
            conn.close()

    def create_run(
        self,
        *,
        run_id: str,
        session_id: str,
        user_message_id: str,
        assistant_message_id: str,
        mode: str,
        status: str,
        provider_id: str,
        model: str,
        question: str,
        history: list[dict[str, Any]],
        database_hint: str | None,
        debug: bool,
        timeout_seconds: int,
        idle_timeout_seconds: int,
        wait_timeout_seconds: int,
        sql_read_timeout_seconds: int,
        sql_write_timeout_seconds: int,
    ) -> dict[str, Any]:
        self._ensure_ready()
        history_json = json.dumps(history or [], ensure_ascii=False, default=_json_default)
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO da_chat_run (
                        run_id, session_id, user_message_id, assistant_message_id, mode, status,
                        provider_id, model_name, question, history_json, database_hint, debug_enabled,
                        timeout_seconds, idle_timeout_seconds, wait_timeout_seconds,
                        sql_read_timeout_seconds, sql_write_timeout_seconds
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id,
                        session_id,
                        user_message_id,
                        assistant_message_id,
                        mode,
                        status,
                        provider_id,
                        model,
                        question,
                        history_json,
                        database_hint,
                        1 if debug else 0,
                        timeout_seconds,
                        idle_timeout_seconds,
                        wait_timeout_seconds,
                        sql_read_timeout_seconds,
                        sql_write_timeout_seconds,
                    ),
                )
            conn.commit()
        finally:
            conn.close()
        return self.get_run(run_id) or {}

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT run_id, session_id, user_message_id, assistant_message_id, mode, status,
                           provider_id, model_name, question, history_json, database_hint, debug_enabled,
                           timeout_seconds, idle_timeout_seconds, wait_timeout_seconds,
                           sql_read_timeout_seconds, sql_write_timeout_seconds, last_event_seq,
                           error_json, started_at, heartbeat_at, finished_at, cancel_requested_at,
                           lease_owner, lease_expires_at, created_at, updated_at
                    FROM da_chat_run
                    WHERE run_id = %s
                    LIMIT 1
                    """,
                    (run_id,),
                )
                row = cur.fetchone()
        finally:
            conn.close()
        return self._normalize_run_row(row)

    def mark_run_running(self, *, run_id: str, lease_owner: str, lease_seconds: int) -> dict[str, Any] | None:
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE da_chat_run
                    SET status = 'running',
                        started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
                        heartbeat_at = CURRENT_TIMESTAMP,
                        lease_owner = %s,
                        lease_expires_at = DATE_ADD(CURRENT_TIMESTAMP, INTERVAL %s SECOND),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE run_id = %s
                    """,
                    (lease_owner, max(1, lease_seconds), run_id),
                )
                cur.execute(
                    "SELECT assistant_message_id, provider_id, model_name FROM da_chat_run WHERE run_id = %s LIMIT 1",
                    (run_id,),
                )
                row = cur.fetchone()
                if row:
                    cur.execute(
                        """
                        UPDATE da_chat_message
                        SET status = 'running',
                            provider_id = COALESCE(%s, provider_id),
                            model_name = COALESCE(%s, model_name),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE message_id = %s
                        """,
                        (
                            row.get("provider_id"),
                            row.get("model_name"),
                            row.get("assistant_message_id"),
                        ),
                    )
            conn.commit()
        finally:
            conn.close()
        return self.get_run(run_id)

    def heartbeat_run(
        self,
        *,
        run_id: str,
        lease_owner: str,
        lease_seconds: int,
        last_event_seq: int | None = None,
    ):
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                if last_event_seq is None:
                    cur.execute(
                        """
                        UPDATE da_chat_run
                        SET heartbeat_at = CURRENT_TIMESTAMP,
                            lease_owner = %s,
                            lease_expires_at = DATE_ADD(CURRENT_TIMESTAMP, INTERVAL %s SECOND),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE run_id = %s
                        """,
                        (lease_owner, max(1, lease_seconds), run_id),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE da_chat_run
                        SET last_event_seq = GREATEST(last_event_seq, %s),
                            heartbeat_at = CURRENT_TIMESTAMP,
                            lease_owner = %s,
                            lease_expires_at = DATE_ADD(CURRENT_TIMESTAMP, INTERVAL %s SECOND),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE run_id = %s
                        """,
                        (last_event_seq, lease_owner, max(1, lease_seconds), run_id),
                    )
            conn.commit()
        finally:
            conn.close()

    def finish_run(
        self,
        *,
        run_id: str,
        status: str,
        error: dict[str, Any] | None = None,
        last_event_seq: int | None = None,
    ) -> dict[str, Any] | None:
        self._ensure_ready()
        error_json = json.dumps(error, ensure_ascii=False, default=_json_default) if error else None
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                if last_event_seq is None:
                    cur.execute(
                        """
                        UPDATE da_chat_run
                        SET status = %s,
                            error_json = %s,
                            finished_at = CURRENT_TIMESTAMP,
                            heartbeat_at = CURRENT_TIMESTAMP,
                            lease_owner = NULL,
                            lease_expires_at = NULL,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE run_id = %s
                        """,
                        (status, error_json, run_id),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE da_chat_run
                        SET status = %s,
                            error_json = %s,
                            last_event_seq = GREATEST(last_event_seq, %s),
                            finished_at = CURRENT_TIMESTAMP,
                            heartbeat_at = CURRENT_TIMESTAMP,
                            lease_owner = NULL,
                            lease_expires_at = NULL,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE run_id = %s
                        """,
                        (status, error_json, last_event_seq, run_id),
                    )
            conn.commit()
        finally:
            conn.close()
        return self.get_run(run_id)

    def claim_runnable_run(self, *, worker_id: str, lease_seconds: int) -> dict[str, Any] | None:
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT run_id
                    FROM da_chat_run
                    WHERE status IN ('queued', 'running')
                      AND finished_at IS NULL
                      AND (
                        status = 'queued'
                        OR lease_expires_at IS NULL
                        OR lease_expires_at < CURRENT_TIMESTAMP
                      )
                    ORDER BY created_at ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                    """
                )
                row = cur.fetchone()
                if not row:
                    conn.rollback()
                    return None

                run_id = str(row.get("run_id") or "")
                cur.execute(
                    """
                    UPDATE da_chat_run
                    SET status = 'running',
                        started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
                        heartbeat_at = CURRENT_TIMESTAMP,
                        lease_owner = %s,
                        lease_expires_at = DATE_ADD(CURRENT_TIMESTAMP, INTERVAL %s SECOND),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE run_id = %s
                    """,
                    (worker_id, max(1, lease_seconds), run_id),
                )
                cur.execute(
                    """
                    SELECT assistant_message_id, provider_id, model_name
                    FROM da_chat_run
                    WHERE run_id = %s
                    LIMIT 1
                    """,
                    (run_id,),
                )
                message_row = cur.fetchone()
                if message_row:
                    cur.execute(
                        """
                        UPDATE da_chat_message
                        SET status = 'running',
                            provider_id = COALESCE(%s, provider_id),
                            model_name = COALESCE(%s, model_name),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE message_id = %s
                        """,
                        (
                            message_row.get("provider_id"),
                            message_row.get("model_name"),
                            message_row.get("assistant_message_id"),
                        ),
                    )
            conn.commit()
        finally:
            conn.close()
        return self.get_run(run_id)

    def request_run_cancel(self, run_id: str) -> dict[str, Any] | None:
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE da_chat_run
                    SET cancel_requested_at = COALESCE(cancel_requested_at, CURRENT_TIMESTAMP),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE run_id = %s
                    """,
                    (run_id,),
                )
                cur.execute(
                    "SELECT status, assistant_message_id FROM da_chat_run WHERE run_id = %s LIMIT 1",
                    (run_id,),
                )
                row = cur.fetchone()
                if row and str(row.get("status") or "") == "queued":
                    cur.execute(
                        """
                        UPDATE da_chat_message
                        SET status = 'cancelled',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE message_id = %s
                        """,
                        (row.get("assistant_message_id"),),
                    )
                    cur.execute(
                        """
                        UPDATE da_chat_run
                        SET status = 'cancelled',
                            finished_at = CURRENT_TIMESTAMP,
                            lease_owner = NULL,
                            lease_expires_at = NULL,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE run_id = %s
                          AND status = 'queued'
                        """,
                        (run_id,),
                    )
            conn.commit()
        finally:
            conn.close()
        return self.get_run(run_id)

    def is_run_cancel_requested(self, run_id: str) -> bool:
        run = self.get_run(run_id)
        if not run:
            return False
        return bool(run.get("cancel_requested_at")) and str(run.get("status") or "") not in {
            "success",
            "failed",
            "cancelled",
        }

    def list_run_events(self, *, run_id: str, after_seq: int = 0, limit: int = 200) -> dict[str, Any]:
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT run_id, session_id, message_id, seq, event_type, payload_json, created_at
                    FROM da_chat_event
                    WHERE run_id = %s AND seq > %s
                    ORDER BY seq ASC
                    LIMIT %s
                    """,
                    (run_id, max(0, after_seq), max(1, limit) + 1),
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        has_more = len(rows) > max(1, limit)
        event_rows = rows[: max(1, limit)]
        events = []
        for row in event_rows:
            payload = _safe_json_load(row.get("payload_json"))
            events.append(
                {
                    "run_id": str(row.get("run_id") or ""),
                    "session_id": str(row.get("session_id") or ""),
                    "message_id": str(row.get("message_id") or ""),
                    "seq": int(row.get("seq") or 0),
                    "type": str(row.get("event_type") or ""),
                    "ts": _to_iso(row.get("created_at")),
                    "payload": payload if isinstance(payload, dict) else {},
                }
            )
        next_after_seq = int(events[-1]["seq"]) if events else max(0, after_seq)
        return {
            "run_id": run_id,
            "after_seq": max(0, after_seq),
            "next_after_seq": next_after_seq,
            "has_more": has_more,
            "events": events,
        }

    def delete_session(self, session_id: str):
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM da_chat_session WHERE session_id = %s", (session_id,))
            conn.commit()
        finally:
            conn.close()

    def _normalize_run_row(self, row: dict[str, Any] | None) -> dict[str, Any] | None:
        if not row:
            return None
        history = _safe_json_load(row.get("history_json"))
        error = _safe_json_load(row.get("error_json"))
        return {
            "run_id": str(row.get("run_id") or ""),
            "session_id": str(row.get("session_id") or ""),
            "user_message_id": str(row.get("user_message_id") or ""),
            "message_id": str(row.get("assistant_message_id") or ""),
            "assistant_message_id": str(row.get("assistant_message_id") or ""),
            "mode": str(row.get("mode") or "interactive"),
            "status": str(row.get("status") or "queued"),
            "provider_id": str(row.get("provider_id") or ""),
            "model": str(row.get("model_name") or ""),
            "question": str(row.get("question") or ""),
            "history": history if isinstance(history, list) else [],
            "database_hint": str(row.get("database_hint") or "") or None,
            "debug": bool(row.get("debug_enabled")),
            "timeout_seconds": int(row.get("timeout_seconds") or 0),
            "idle_timeout_seconds": int(row.get("idle_timeout_seconds") or 0),
            "wait_timeout_seconds": int(row.get("wait_timeout_seconds") or 0),
            "sql_read_timeout_seconds": int(row.get("sql_read_timeout_seconds") or 0),
            "sql_write_timeout_seconds": int(row.get("sql_write_timeout_seconds") or 0),
            "last_event_seq": int(row.get("last_event_seq") or 0),
            "error": error if isinstance(error, dict) else None,
            "cancel_requested_at": _to_iso(row.get("cancel_requested_at")) or None,
            "started_at": _to_iso(row.get("started_at")) or None,
            "heartbeat_at": _to_iso(row.get("heartbeat_at")) or None,
            "finished_at": _to_iso(row.get("finished_at")) or None,
            "lease_owner": str(row.get("lease_owner") or "") or None,
            "lease_expires_at": _to_iso(row.get("lease_expires_at")) or None,
            "created_at": _to_iso(row.get("created_at")),
            "updated_at": _to_iso(row.get("updated_at")),
        }

    def _load_blocks_map(self, message_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        if not message_ids:
            return {}

        conn = self._connect(database=self._schema_name())
        try:
            placeholders = ",".join(["%s"] * len(message_ids))
            with conn.cursor() as cur:
                cur.execute(
                    (
                        "SELECT message_id, content_json FROM da_chat_block "
                        f"WHERE message_id IN ({placeholders}) ORDER BY message_id ASC, seq ASC"
                    ),
                    message_ids,
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        blocks_map: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            msg_id = str(row.get("message_id") or "")
            block = _safe_json_load(row.get("content_json"))
            if not isinstance(block, dict):
                continue
            blocks_map.setdefault(msg_id, []).append(block)
        return blocks_map

    def _load_messages(self, session_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        if not session_ids:
            return {}

        conn = self._connect(database=self._schema_name())
        try:
            placeholders = ",".join(["%s"] * len(session_ids))
            with conn.cursor() as cur:
                cur.execute(
                    (
                        "SELECT message_id, session_id, role, status, stop_reason, stop_sequence, run_id, content, usage_json, error_json, "
                        "provider_id, model_name, created_at "
                        "FROM da_chat_message "
                        f"WHERE session_id IN ({placeholders}) "
                        "ORDER BY created_at ASC, message_id ASC"
                    ),
                    session_ids,
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        message_ids = [str(row.get("message_id") or "") for row in rows]
        blocks_map = self._load_blocks_map(message_ids)

        result: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            msg_id = str(row.get("message_id") or "")
            error = _safe_json_load(row.get("error_json"))
            usage = _safe_json_load(row.get("usage_json"))
            message = {
                "message_id": msg_id,
                "role": row.get("role"),
                "status": row.get("status") or "success",
                "stop_reason": row.get("stop_reason") or None,
                "stop_sequence": row.get("stop_sequence") or None,
                "run_id": row.get("run_id"),
                "content": row.get("content") or "",
                "usage": usage if isinstance(usage, dict) else None,
                "blocks": blocks_map.get(msg_id, []),
                "error": error if isinstance(error, dict) else None,
                "provider_id": row.get("provider_id"),
                "model": row.get("model_name"),
                "created_at": _to_iso(row.get("created_at")),
            }
            sid = str(row.get("session_id") or "")
            result.setdefault(sid, []).append(message)

        return result

    def _load_message_stats(self, session_ids: list[str]) -> dict[str, dict[str, Any]]:
        if not session_ids:
            return {}

        conn = self._connect(database=self._schema_name())
        try:
            placeholders = ",".join(["%s"] * len(session_ids))
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT session_id, COUNT(*) AS message_count, MAX(created_at) AS latest_time
                    FROM da_chat_message
                    WHERE session_id IN ({placeholders})
                    GROUP BY session_id
                    """,
                    session_ids,
                )
                stat_rows = cur.fetchall()

                cur.execute(
                    (
                        "SELECT m.session_id, m.content FROM da_chat_message m "
                        "INNER JOIN ("
                        f"  SELECT session_id, MAX(created_at) AS latest_time FROM da_chat_message WHERE session_id IN ({placeholders}) GROUP BY session_id"
                        ") t ON m.session_id = t.session_id AND m.created_at = t.latest_time"
                    ),
                    session_ids,
                )
                preview_rows = cur.fetchall()
        finally:
            conn.close()

        preview_map: dict[str, str] = {}
        for row in preview_rows:
            sid = str(row.get("session_id") or "")
            content = str(row.get("content") or "").strip()
            preview_map[sid] = content[:120] + ("..." if len(content) > 120 else "")

        result: dict[str, dict[str, Any]] = {}
        for row in stat_rows:
            sid = str(row.get("session_id") or "")
            result[sid] = {
                "message_count": int(row.get("message_count") or 0),
                "last_message_preview": preview_map.get(sid, ""),
            }
        return result

    def list_sessions(self, include_messages: bool = False) -> list[dict[str, Any]]:
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT session_id, title, created_at, updated_at
                    FROM da_chat_session
                    ORDER BY updated_at DESC
                    """
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        session_ids = [str(row.get("session_id") or "") for row in rows]
        messages_map = self._load_messages(session_ids) if include_messages else {}
        stats_map = self._load_message_stats(session_ids)

        result = []
        for row in rows:
            sid = str(row.get("session_id") or "")
            stats = stats_map.get(sid, {})
            result.append(
                {
                    "session_id": sid,
                    "title": row.get("title") or "新会话",
                    "messages": messages_map.get(sid, []),
                    "message_count": int(stats.get("message_count") or 0),
                    "last_message_preview": stats.get("last_message_preview") or "",
                    "created_at": _to_iso(row.get("created_at")),
                    "updated_at": _to_iso(row.get("updated_at")),
                }
            )
        return result

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        self._ensure_ready()
        conn = self._connect(database=self._schema_name())
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT session_id, title, created_at, updated_at
                    FROM da_chat_session
                    WHERE session_id = %s
                    LIMIT 1
                    """,
                    (session_id,),
                )
                row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            return None

        messages = self._load_messages([session_id]).get(session_id, [])
        return {
            "session_id": str(row.get("session_id") or ""),
            "title": row.get("title") or "新会话",
            "messages": messages,
            "created_at": _to_iso(row.get("created_at")),
            "updated_at": _to_iso(row.get("updated_at")),
        }


_session_store = SessionStore()


def get_session_store() -> SessionStore:
    return _session_store
