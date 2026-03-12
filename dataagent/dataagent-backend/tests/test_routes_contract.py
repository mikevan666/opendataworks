from __future__ import annotations

import inspect
import json
import sys
import types
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if "pymysql" not in sys.modules:
    sys.modules["pymysql"] = types.SimpleNamespace(
        connect=lambda *args, **kwargs: None,
        cursors=types.SimpleNamespace(DictCursor=object),
        connections=types.SimpleNamespace(Connection=object),
    )

import api.routes as routes
from main import app


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class _FakeStore:
    def __init__(self):
        self.sessions: dict[str, dict] = {}
        self.runs: dict[str, dict] = {}
        self.events: dict[str, list[dict]] = {}

    def init_schema(self):
        return None

    def create_session(self, session_id: str, title: str):
        now = _now()
        session = {
            "session_id": session_id,
            "title": title,
            "messages": [],
            "message_count": 0,
            "last_message_preview": "",
            "created_at": now,
            "updated_at": now,
        }
        self.sessions[session_id] = session
        return session

    def update_session_title(self, session_id: str, title: str):
        self.sessions[session_id]["title"] = title

    def get_session(self, session_id: str):
        return self.sessions.get(session_id)

    def list_sessions(self, include_messages: bool = False):
        rows = []
        for session in self.sessions.values():
            item = dict(session)
            if not include_messages:
                item["messages"] = []
            rows.append(item)
        return rows

    def delete_session(self, session_id: str):
        self.sessions.pop(session_id, None)

    def append_user_message(self, *, session_id: str, message_id: str, content: str):
        session = self.sessions[session_id]
        message = {
            "message_id": message_id,
            "role": "user",
            "content": content,
            "status": "success",
            "created_at": _now(),
        }
        session["messages"].append(message)
        session["message_count"] += 1
        session["last_message_preview"] = content[:120]
        return message

    def update_message_status(self, *, message_id: str, status: str, provider_id: str | None = None, model: str | None = None):
        for session in self.sessions.values():
            for message in session["messages"]:
                if message.get("message_id") != message_id:
                    continue
                message["status"] = status
                if provider_id is not None:
                    message["provider_id"] = provider_id
                if model is not None:
                    message["model"] = model

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
        usage: dict | None,
        blocks: list[dict],
        error: dict | None,
        provider_id: str,
        model: str,
    ):
        session = self.sessions[session_id]
        message = {
            "message_id": message_id,
            "role": "assistant",
            "run_id": run_id,
            "content": content,
            "status": status,
            "stop_reason": stop_reason,
            "stop_sequence": stop_sequence,
            "usage": usage,
            "blocks": blocks,
            "error": error,
            "provider_id": provider_id,
            "model": model,
            "created_at": _now(),
        }
        existing = next((item for item in session["messages"] if item.get("message_id") == message_id), None)
        if existing:
            existing.update(message)
            return existing
        session["messages"].append(message)
        session["message_count"] += 1
        session["last_message_preview"] = content[:120]
        return message

    def append_run_event(self, *, session_id: str, message_id: str, run_id: str, event: dict):
        self.events.setdefault(run_id, []).append(event)
        run = self.runs.get(run_id)
        if run:
            run["last_event_seq"] = max(int(run.get("last_event_seq") or 0), int(event.get("seq") or 0))
            run["updated_at"] = _now()

    def save_run_events(self, *, session_id: str, message_id: str, run_id: str, events: list[dict]):
        for event in events:
            self.append_run_event(session_id=session_id, message_id=message_id, run_id=run_id, event=event)

    def create_run(self, **kwargs):
        now = _now()
        run = {
            "run_id": kwargs["run_id"],
            "session_id": kwargs["session_id"],
            "user_message_id": kwargs["user_message_id"],
            "message_id": kwargs["assistant_message_id"],
            "assistant_message_id": kwargs["assistant_message_id"],
            "mode": kwargs["mode"],
            "status": kwargs["status"],
            "provider_id": kwargs["provider_id"],
            "model": kwargs["model"],
            "question": kwargs["question"],
            "history": list(kwargs.get("history") or []),
            "database_hint": kwargs.get("database_hint"),
            "debug": bool(kwargs.get("debug")),
            "timeout_seconds": int(kwargs.get("timeout_seconds") or 0),
            "idle_timeout_seconds": int(kwargs.get("idle_timeout_seconds") or 0),
            "wait_timeout_seconds": int(kwargs.get("wait_timeout_seconds") or 0),
            "sql_read_timeout_seconds": int(kwargs.get("sql_read_timeout_seconds") or 0),
            "sql_write_timeout_seconds": int(kwargs.get("sql_write_timeout_seconds") or 0),
            "last_event_seq": 0,
            "cancel_requested_at": None,
            "started_at": None,
            "heartbeat_at": None,
            "finished_at": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
        self.runs[run["run_id"]] = run
        return run

    def get_run(self, run_id: str):
        return self.runs.get(run_id)

    def mark_run_running(self, *, run_id: str, lease_owner: str, lease_seconds: int):
        run = self.runs[run_id]
        run["status"] = "running"
        run["started_at"] = run["started_at"] or _now()
        run["heartbeat_at"] = _now()
        self.update_message_status(
            message_id=run["assistant_message_id"],
            status="running",
            provider_id=run["provider_id"],
            model=run["model"],
        )
        return run

    def heartbeat_run(self, *, run_id: str, lease_owner: str, lease_seconds: int, last_event_seq: int | None = None):
        run = self.runs[run_id]
        run["heartbeat_at"] = _now()
        if last_event_seq is not None:
            run["last_event_seq"] = max(int(run.get("last_event_seq") or 0), int(last_event_seq or 0))

    def finish_run(self, *, run_id: str, status: str, error: dict | None = None, last_event_seq: int | None = None):
        run = self.runs[run_id]
        run["status"] = status
        run["error"] = error
        run["finished_at"] = _now()
        run["updated_at"] = _now()
        if last_event_seq is not None:
            run["last_event_seq"] = int(last_event_seq)
        return run

    def claim_runnable_run(self, *, worker_id: str, lease_seconds: int):
        return None

    def request_run_cancel(self, run_id: str):
        run = self.runs.get(run_id)
        if not run:
            return None
        run["cancel_requested_at"] = _now()
        if run["status"] == "queued":
            run["status"] = "cancelled"
            run["finished_at"] = _now()
            self.update_message_status(message_id=run["assistant_message_id"], status="cancelled")
        return run

    def is_run_cancel_requested(self, run_id: str) -> bool:
        run = self.runs.get(run_id)
        return bool(run and run.get("cancel_requested_at"))

    def list_run_events(self, *, run_id: str, after_seq: int = 0, limit: int = 200):
        rows = [event for event in self.events.get(run_id, []) if int(event.get("seq") or 0) > after_seq]
        rows.sort(key=lambda item: int(item.get("seq") or 0))
        page = rows[:limit]
        return {
            "run_id": run_id,
            "after_seq": after_seq,
            "next_after_seq": int(page[-1].get("seq") or after_seq) if page else after_seq,
            "has_more": len(rows) > limit,
            "events": page,
        }


async def _fake_execute_run(store, run, *, worker_id, on_event=None):
    store.mark_run_running(run_id=run["run_id"], lease_owner=worker_id, lease_seconds=30)
    events = [
        {
            "run_id": run["run_id"],
            "session_id": run["session_id"],
            "message_id": run["message_id"],
            "seq": 1,
            "type": "llm_response_created",
            "ts": _now(),
            "payload": {
                "provider_id": run["provider_id"],
                "model": run["model"],
                "database_hint": run["database_hint"],
            },
        },
        {
            "run_id": run["run_id"],
            "session_id": run["session_id"],
            "message_id": run["message_id"],
            "seq": 2,
            "type": "done",
            "ts": _now(),
            "payload": {
                "status": "success",
                "content": "你好",
                "blocks": [
                    {"block_id": "main-text", "type": "main_text", "status": "success", "text": "你好"},
                    {
                        "block_id": "tool-1",
                        "type": "tool_result",
                        "status": "success",
                        "tool_name": "Bash",
                        "tool_id": "tool-1",
                        "output": "{\"kind\":\"python_execution\",\"summary\":\"ok\"}",
                    },
                ],
                "error": None,
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 12, "output_tokens": 6},
                "provider_id": run["provider_id"],
                "model": run["model"],
            },
        },
    ]
    for event in events:
        store.append_run_event(
            session_id=run["session_id"],
            message_id=run["message_id"],
            run_id=run["run_id"],
            event=event,
        )
        if on_event:
            result = on_event(event)
            if inspect.isawaitable(result):
                await result

    done_payload = events[-1]["payload"]
    store.save_assistant_message(
        session_id=run["session_id"],
        message_id=run["message_id"],
        run_id=run["run_id"],
        content=done_payload["content"],
        status=done_payload["status"],
        stop_reason=done_payload["stop_reason"],
        stop_sequence=done_payload["stop_sequence"],
        usage=done_payload["usage"],
        blocks=done_payload["blocks"],
        error=done_payload["error"],
        provider_id=done_payload["provider_id"],
        model=done_payload["model"],
    )
    store.finish_run(run_id=run["run_id"], status="success", last_event_seq=2)
    return store.get_run(run["run_id"])


def _extract_sse_events(raw_text: str) -> list[dict]:
    events = []
    chunks = [item for item in raw_text.split("\n\n") if item.strip()]
    for chunk in chunks:
        data_lines = [line[5:].strip() for line in chunk.split("\n") if line.startswith("data:")]
        if not data_lines:
            continue
        payload = json.loads("\n".join(data_lines))
        events.append(payload)
    return events


def test_session_message_stream_and_non_stream_contract(monkeypatch):
    fake_store = _FakeStore()
    fake_store.create_session("s1", "新会话")

    monkeypatch.setattr(routes, "get_session_store", lambda: fake_store)
    monkeypatch.setattr(routes, "execute_run", _fake_execute_run)
    monkeypatch.setattr(
        routes,
        "resolve_runtime_provider_selection",
        lambda provider_id, model: {
            "provider_id": provider_id or "openrouter",
            "model": model or "anthropic/claude-sonnet-4.5",
            "api_key": "",
            "auth_token": "token",
            "base_url": "https://openrouter.ai/api",
        },
    )

    client = TestClient(app)

    non_stream = client.post(
        "/api/v1/nl2sql/sessions/s1/messages",
        json={
            "content": "你好",
            "provider_id": "openrouter",
            "model": "anthropic/claude-sonnet-4.5",
            "stream": False,
            "execution_mode": "interactive",
        },
    )
    assert non_stream.status_code == 200
    non_stream_data = non_stream.json()

    stream = client.post(
        "/api/v1/nl2sql/sessions/s1/messages",
        json={
            "content": "你好",
            "provider_id": "openrouter",
            "model": "anthropic/claude-sonnet-4.5",
            "stream": True,
            "execution_mode": "interactive",
        },
    )
    assert stream.status_code == 200
    stream_events = _extract_sse_events(stream.text)
    assert stream_events
    assert stream_events[-1]["type"] == "done"
    stream_done = stream_events[-1]["payload"]

    expected_keys = {
        "role",
        "message_id",
        "run_id",
        "status",
        "content",
        "stop_reason",
        "stop_sequence",
        "usage",
        "blocks",
        "error",
        "provider_id",
        "model",
        "created_at",
    }
    assert expected_keys.issubset(set(non_stream_data.keys()))
    assert non_stream_data["content"] == stream_done["content"]
    assert non_stream_data["status"] == stream_done["status"]
    assert non_stream_data["stop_reason"] == stream_done["stop_reason"]
    assert non_stream_data["usage"] == stream_done["usage"]
    assert non_stream_data["provider_id"] == stream_done["provider_id"]
    assert non_stream_data["model"] == stream_done["model"]


def test_background_run_contract_and_cancel(monkeypatch):
    fake_store = _FakeStore()
    fake_store.create_session("s1", "新会话")

    monkeypatch.setattr(routes, "get_session_store", lambda: fake_store)
    monkeypatch.setattr(
        routes,
        "resolve_runtime_provider_selection",
        lambda provider_id, model: {
            "provider_id": provider_id or "openrouter",
            "model": model or "anthropic/claude-sonnet-4.5",
            "api_key": "",
            "auth_token": "token",
            "base_url": "https://openrouter.ai/api",
        },
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/nl2sql/sessions/s1/messages",
        json={
            "content": "最近 30 天工作流发布次数趋势",
            "provider_id": "openrouter",
            "model": "anthropic/claude-sonnet-4.5",
            "stream": False,
            "execution_mode": "background",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["mode"] == "background"
    assert payload["status"] == "queued"
    assert payload["message"]["status"] == "queued"

    run_id = payload["run_id"]
    status = client.get(f"/api/v1/nl2sql/runs/{run_id}")
    assert status.status_code == 200
    status_payload = status.json()
    assert status_payload["mode"] == "background"
    assert status_payload["status"] == "queued"
    assert status_payload["message_id"] == payload["message_id"]

    events = client.get(f"/api/v1/nl2sql/runs/{run_id}/events", params={"after_seq": 0})
    assert events.status_code == 200
    events_payload = events.json()
    assert events_payload["run_id"] == run_id
    assert events_payload["events"] == []

    cancelled = client.post(f"/api/v1/nl2sql/runs/{run_id}/cancel")
    assert cancelled.status_code == 200
    cancel_payload = cancelled.json()
    assert cancel_payload["run_id"] == run_id
    assert cancel_payload["status"] == "cancelled"


def test_auto_run_uses_background_timeout_profile(monkeypatch):
    fake_store = _FakeStore()
    fake_store.create_session("s1", "新会话")

    monkeypatch.setattr(routes, "get_session_store", lambda: fake_store)
    monkeypatch.setattr(
        routes,
        "resolve_runtime_provider_selection",
        lambda provider_id, model: {
            "provider_id": provider_id or "openrouter",
            "model": model or "anthropic/claude-sonnet-4.5",
            "api_key": "",
            "auth_token": "token",
            "base_url": "https://openrouter.ai/api",
        },
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/nl2sql/sessions/s1/messages",
        json={
            "content": "最近 30 天工作流发布次数趋势",
            "provider_id": "openrouter",
            "model": "anthropic/claude-sonnet-4.5",
            "stream": False,
            "execution_mode": "auto",
            "wait_timeout_seconds": 0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["mode"] == "auto"

    run = fake_store.get_run(payload["run_id"])
    assert run is not None
    assert run["timeout_seconds"] == 1800
    assert run["idle_timeout_seconds"] == 300
    assert run["sql_read_timeout_seconds"] == 900
    assert run["wait_timeout_seconds"] == 0


def test_ask_endpoint_removed():
    client = TestClient(app)
    response = client.post("/api/v1/nl2sql/ask", json={"question": "hello"})
    assert response.status_code == 404
