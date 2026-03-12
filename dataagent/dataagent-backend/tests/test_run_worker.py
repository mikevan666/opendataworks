from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core import run_worker


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class _Store:
    def __init__(self):
        self.run = {
            "run_id": "run-1",
            "session_id": "session-1",
            "user_message_id": "u-1",
            "message_id": "a-1",
            "assistant_message_id": "a-1",
            "mode": "background",
            "status": "queued",
            "provider_id": "openrouter",
            "model": "anthropic/claude-sonnet-4.5",
            "question": "最近 30 天工作流发布次数趋势",
            "history": [],
            "database_hint": None,
            "debug": False,
            "timeout_seconds": 1800,
            "idle_timeout_seconds": 300,
            "wait_timeout_seconds": 20,
            "sql_read_timeout_seconds": 900,
            "sql_write_timeout_seconds": 60,
            "last_event_seq": 0,
            "cancel_requested_at": None,
            "started_at": None,
            "heartbeat_at": None,
            "finished_at": None,
            "error": None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.session = {
            "session_id": "session-1",
            "title": "新会话",
            "messages": [
                {
                    "message_id": "a-1",
                    "role": "assistant",
                    "run_id": "run-1",
                    "content": "",
                    "status": "queued",
                    "blocks": [],
                    "created_at": _now(),
                    "provider_id": "openrouter",
                    "model": "anthropic/claude-sonnet-4.5",
                }
            ],
        }
        self.events: list[dict] = []

    def mark_run_running(self, *, run_id: str, lease_owner: str, lease_seconds: int):
        self.run["status"] = "running"
        self.run["started_at"] = self.run["started_at"] or _now()
        self.run["heartbeat_at"] = _now()
        self.session["messages"][0]["status"] = "running"
        return self.run

    def is_run_cancel_requested(self, run_id: str) -> bool:
        return False

    def heartbeat_run(self, *, run_id: str, lease_owner: str, lease_seconds: int, last_event_seq: int | None = None):
        self.run["heartbeat_at"] = _now()
        if last_event_seq is not None:
            self.run["last_event_seq"] = int(last_event_seq)

    def append_run_event(self, *, session_id: str, message_id: str, run_id: str, event: dict):
        self.events.append(event)
        self.run["last_event_seq"] = max(self.run["last_event_seq"], int(event.get("seq") or 0))

    def save_assistant_message(self, **kwargs):
        self.session["messages"][0].update(
            {
                "message_id": kwargs["message_id"],
                "run_id": kwargs["run_id"],
                "content": kwargs["content"],
                "status": kwargs["status"],
                "stop_reason": kwargs["stop_reason"],
                "stop_sequence": kwargs["stop_sequence"],
                "usage": kwargs["usage"],
                "blocks": kwargs["blocks"],
                "error": kwargs["error"],
                "provider_id": kwargs["provider_id"],
                "model": kwargs["model"],
            }
        )
        return self.session["messages"][0]

    def finish_run(self, *, run_id: str, status: str, error: dict | None = None, last_event_seq: int | None = None):
        self.run["status"] = status
        self.run["error"] = error
        self.run["finished_at"] = _now()
        if last_event_seq is not None:
            self.run["last_event_seq"] = int(last_event_seq)
        return self.run

    def get_run(self, run_id: str):
        return self.run

    def get_session(self, session_id: str):
        return self.session


async def _fake_stream_agent_reply(run_input):
    yield {
        "run_id": run_input.run_id,
        "session_id": run_input.session_id,
        "message_id": run_input.message_id,
        "seq": 1,
        "type": "llm_response_created",
        "ts": _now(),
        "payload": {
            "provider_id": run_input.provider_id,
            "model": run_input.model,
            "database_hint": run_input.database_hint,
        },
    }
    yield {
        "run_id": run_input.run_id,
        "session_id": run_input.session_id,
        "message_id": run_input.message_id,
        "seq": 2,
        "type": "done",
        "ts": _now(),
        "payload": {
            "status": "success",
            "content": "分析完成",
            "blocks": [{"block_id": "main-text", "type": "main_text", "status": "success", "text": "分析完成"}],
            "error": None,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 6},
            "provider_id": run_input.provider_id,
            "model": run_input.model,
        },
    }


def test_execute_run_persists_events_and_terminal_message(monkeypatch):
    store = _Store()
    monkeypatch.setattr(run_worker, "stream_agent_reply", _fake_stream_agent_reply)

    asyncio.run(run_worker.execute_run(store, store.run, worker_id="worker:test"))

    assert [event["type"] for event in store.events] == ["llm_response_created", "done"]
    assert store.run["status"] == "success"
    assert store.run["last_event_seq"] == 2
    assert store.run["finished_at"]
    assert store.session["messages"][0]["status"] == "success"
    assert store.session["messages"][0]["content"] == "分析完成"


class _QueueStore:
    def __init__(self, runs: list[dict]):
        self.runs = list(runs)

    def init_schema(self):
        return None

    def claim_runnable_run(self, *, worker_id: str, lease_seconds: int):
        if not self.runs:
            return None
        return self.runs.pop(0)


def test_run_worker_claims_multiple_runs_up_to_max_concurrency(monkeypatch):
    claimed_runs = [
        {"run_id": "run-1"},
        {"run_id": "run-2"},
    ]
    store = _QueueStore(claimed_runs)
    active_run_ids: set[str] = set()
    max_parallel = {"value": 0}

    async def _fake_execute_run(store_arg, run, *, worker_id):
        run_id = str(run.get("run_id") or "")
        active_run_ids.add(run_id)
        max_parallel["value"] = max(max_parallel["value"], len(active_run_ids))
        await run_worker.anyio.sleep(0.05)
        active_run_ids.discard(run_id)
        return run

    monkeypatch.setattr(run_worker, "execute_run", _fake_execute_run)
    monkeypatch.setattr(
        run_worker,
        "get_settings",
        lambda: type(
            "_Cfg",
            (),
            {
                "run_worker_poll_interval_seconds": 2,
                "run_worker_lease_seconds": 30,
                "run_worker_max_concurrency": 2,
            },
        )(),
    )

    async def _exercise():
        worker = run_worker.RunWorker(store=store, worker_id="worker:test", max_concurrency=2)
        with run_worker.anyio.move_on_after(0.2):
            await worker.run_forever()

    asyncio.run(_exercise())

    assert max_parallel["value"] == 2
