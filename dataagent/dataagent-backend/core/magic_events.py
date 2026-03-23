from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


TERMINAL_TASK_STATUSES = {"finished", "error", "suspended"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TaskEventSequencer:
    topic_id: str
    task_id: str
    seq: int = 0

    def next_seq(self) -> int:
        self.seq += 1
        return self.seq

    def event(
        self,
        event_type: str,
        *,
        content_type: str | None = None,
        correlation_id: str | None = None,
        parent_correlation_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "record_type": "event",
            "seq_id": self.next_seq(),
            "created_at": utc_now_iso(),
            "event_type": event_type,
            "correlation_id": correlation_id,
            "parent_correlation_id": parent_correlation_id,
            "content_type": content_type,
            "data": data or {},
        }

    def chunk(
        self,
        *,
        request_id: str,
        chunk_id: int,
        content: str | None,
        delta: dict[str, Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "record_type": "chunk",
            "seq_id": self.next_seq(),
            "created_at": utc_now_iso(),
            "request_id": request_id,
            "chunk_id": int(chunk_id),
            "content": content,
            "delta": delta,
            "metadata": metadata,
        }


def encode_sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False, separators=(',', ':'))}\n\n"
