from __future__ import annotations

from typing import Any

from core.topic_task_store import TopicTaskStore


class TaskPersistenceWriter:
    def __init__(self, *, store: TopicTaskStore, topic_id: str, task_id: str):
        self.store = store
        self.topic_id = topic_id
        self.task_id = task_id
        self.usage: dict[str, Any] | None = None
        self.error: dict[str, Any] | None = None
        self._content_by_correlation: dict[str, str] = {}
        self._content_order: list[str] = []

    def _assistant_content(self) -> str:
        return "".join(self._content_by_correlation.get(correlation_id, "") for correlation_id in self._content_order)

    async def persist(self, record: dict[str, Any]) -> None:
        if str(record.get("record_type") or "") == "event":
            data = dict(record.get("data") or {})
            usage = data.get("token_usage")
            if isinstance(usage, dict):
                self.usage = {**(self.usage or {}), **usage}
            error = data.get("error")
            if isinstance(error, dict):
                self.error = error

            self.store.append_lifecycle_event(
                topic_id=self.topic_id,
                task_id=self.task_id,
                event_type=str(record.get("event_type") or ""),
                content_type=str(record.get("content_type") or "") or None,
                correlation_id=str(record.get("correlation_id") or "") or None,
                parent_correlation_id=str(record.get("parent_correlation_id") or "") or None,
                data=data,
            )
            return

        if str(record.get("record_type") or "") != "chunk":
            return

        delta = dict(record.get("delta") or {})
        metadata = dict(record.get("metadata") or {})
        correlation_id = str(metadata.get("correlation_id") or "")
        content_type = str(metadata.get("content_type") or "")
        content = record.get("content")

        self.store.append_chunk(
            topic_id=self.topic_id,
            task_id=self.task_id,
            request_id=str(record.get("request_id") or ""),
            chunk_id=int(record.get("chunk_id") or 0),
            content=str(content) if content is not None else None,
            delta=delta,
            metadata=metadata,
        )

        if content_type != "content" or not correlation_id:
            return

        if correlation_id not in self._content_order:
            self._content_order.append(correlation_id)

        status = str(delta.get("status") or "")
        text = str(content or "")
        current = self._content_by_correlation.get(correlation_id, "")
        if status == "END":
            self._content_by_correlation[correlation_id] = text
        else:
            self._content_by_correlation[correlation_id] = f"{current}{text}"

        self.store.update_assistant_message(
            topic_id=self.topic_id,
            task_id=self.task_id,
            status="running",
            content=self._assistant_content(),
            usage=self.usage,
            error=self.error,
        )

    def finalize(self, *, task_status: str, content: str, usage: dict[str, Any] | None, error: dict[str, Any] | None) -> None:
        self.usage = usage or self.usage
        self.error = error or self.error
        self.store.update_assistant_message(
            topic_id=self.topic_id,
            task_id=self.task_id,
            status=task_status,
            content=content or self._assistant_content(),
            usage=self.usage,
            error=self.error,
        )
