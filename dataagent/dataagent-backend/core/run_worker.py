from __future__ import annotations

import inspect
import logging
import os
import socket
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

import anyio

from config import get_settings
from core.nl2sql_agent import AgentRunInput, stream_agent_reply
from core.session_store import SessionStore, get_session_store

logger = logging.getLogger(__name__)

TERMINAL_RUN_STATUSES = {"success", "failed", "cancelled"}
ACTIVE_RUN_STATUSES = {"queued", "running"}


def normalize_execution_mode(raw_mode: str | None, *, stream: bool) -> str:
    mode = str(raw_mode or "").strip().lower()
    if mode in {"interactive", "auto", "background"}:
        return mode
    return "interactive" if stream else "auto"


def resolve_run_timeouts(mode: str) -> dict[str, int]:
    cfg = get_settings()
    normalized = normalize_execution_mode(mode, stream=False)
    is_background = normalized == "background"
    if is_background:
        timeout_seconds = int(cfg.agent_background_timeout_seconds or 1800)
        idle_timeout_seconds = int(cfg.agent_background_idle_timeout_seconds or 300)
        sql_read_timeout_seconds = int(cfg.agent_background_sql_read_timeout_seconds or 900)
    else:
        timeout_seconds = int(cfg.agent_interactive_timeout_seconds or cfg.agent_timeout_seconds or 360)
        idle_timeout_seconds = int(cfg.agent_interactive_idle_timeout_seconds or 90)
        sql_read_timeout_seconds = int(cfg.agent_interactive_sql_read_timeout_seconds or 300)
    return {
        "wait_timeout_seconds": int(cfg.agent_wait_timeout_seconds or 20),
        "timeout_seconds": timeout_seconds,
        "idle_timeout_seconds": idle_timeout_seconds,
        "sql_read_timeout_seconds": sql_read_timeout_seconds,
        "sql_write_timeout_seconds": int(cfg.agent_sql_write_timeout_seconds or 60),
    }


def build_agent_run_input(run: dict[str, Any]) -> AgentRunInput:
    return AgentRunInput(
        run_id=str(run.get("run_id") or ""),
        session_id=str(run.get("session_id") or ""),
        message_id=str(run.get("message_id") or run.get("assistant_message_id") or ""),
        question=str(run.get("question") or ""),
        history=list(run.get("history") or []),
        provider_id=str(run.get("provider_id") or ""),
        model=str(run.get("model") or ""),
        database_hint=str(run.get("database_hint") or "").strip() or None,
        debug=bool(run.get("debug")),
        timeout_seconds=int(run.get("timeout_seconds") or 0),
        sql_read_timeout_seconds=int(run.get("sql_read_timeout_seconds") or 0),
        sql_write_timeout_seconds=int(run.get("sql_write_timeout_seconds") or 0),
        execution_mode=str(run.get("mode") or "interactive"),
    )


def build_worker_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


async def _maybe_call(callback: Callable[[dict[str, Any]], Any] | None, event: dict[str, Any]):
    if callback is None:
        return
    result = callback(event)
    if inspect.isawaitable(result):
        await result


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _terminal_error_payload(code: str, message: str) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
    }


def _build_terminal_event(run: dict[str, Any], *, seq: int, status: str, code: str, message: str) -> dict[str, Any]:
    error = _terminal_error_payload(code, message) if status != "success" else None
    block = {
        "block_id": f"{code}-1",
        "type": "error",
        "status": "failed" if status != "success" else "success",
        "text": message,
        "payload": error or {},
    }
    return {
        "run_id": str(run.get("run_id") or ""),
        "session_id": str(run.get("session_id") or ""),
        "message_id": str(run.get("message_id") or run.get("assistant_message_id") or ""),
        "seq": seq,
        "type": "done",
        "ts": _now_iso(),
        "payload": {
            "status": status,
            "content": message,
            "blocks": [block],
            "error": error,
            "provider_id": str(run.get("provider_id") or ""),
            "model": str(run.get("model") or ""),
        },
    }


def _done_payload_to_message(done_payload: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    usage_payload = done_payload.get("usage")
    error_payload = done_payload.get("error")
    blocks_payload = done_payload.get("blocks")
    return {
        "session_id": str(run.get("session_id") or ""),
        "message_id": str(run.get("message_id") or run.get("assistant_message_id") or ""),
        "run_id": str(run.get("run_id") or ""),
        "content": str(done_payload.get("content") or ""),
        "status": str(done_payload.get("status") or "success"),
        "stop_reason": str(done_payload.get("stop_reason") or "").strip() or None,
        "stop_sequence": (
            str(done_payload.get("stop_sequence")) if done_payload.get("stop_sequence") is not None else None
        ),
        "usage": usage_payload if isinstance(usage_payload, dict) else None,
        "blocks": blocks_payload if isinstance(blocks_payload, list) else [],
        "error": error_payload if isinstance(error_payload, dict) else None,
        "provider_id": str(done_payload.get("provider_id") or run.get("provider_id") or ""),
        "model": str(done_payload.get("model") or run.get("model") or ""),
    }


def _load_message_from_session(store: SessionStore, session_id: str, message_id: str) -> dict[str, Any] | None:
    session = store.get_session(session_id)
    if not session:
        return None
    for message in session.get("messages") or []:
        if str(message.get("message_id") or "") == message_id:
            return message
    return None


async def execute_run(
    store: SessionStore,
    run: dict[str, Any],
    *,
    worker_id: str,
    on_event: Callable[[dict[str, Any]], Any] | None = None,
) -> dict[str, Any]:
    cfg = get_settings()
    lease_seconds = max(1, int(cfg.run_worker_lease_seconds or 30))
    heartbeat_seconds = max(1, int(cfg.run_worker_heartbeat_seconds or 5))
    started_run = store.mark_run_running(
        run_id=str(run.get("run_id") or ""),
        lease_owner=worker_id,
        lease_seconds=lease_seconds,
    ) or run
    run = started_run

    if store.is_run_cancel_requested(str(run.get("run_id") or "")):
        cancel_event = _build_terminal_event(
            run,
            seq=max(1, int(run.get("last_event_seq") or 0) + 1),
            status="cancelled",
            code="run_cancelled",
            message="任务已取消",
        )
        store.append_run_event(
            session_id=str(run.get("session_id") or ""),
            message_id=str(run.get("message_id") or ""),
            run_id=str(run.get("run_id") or ""),
            event=cancel_event,
        )
        store.save_assistant_message(**_done_payload_to_message(cancel_event["payload"], run))
        store.finish_run(
            run_id=str(run.get("run_id") or ""),
            status="cancelled",
            error=_terminal_error_payload("run_cancelled", "任务已取消"),
            last_event_seq=int(cancel_event.get("seq") or 0),
        )
        await _maybe_call(on_event, cancel_event)
        return store.get_run(str(run.get("run_id") or "")) or run

    async def heartbeat_loop():
        while True:
            await anyio.sleep(heartbeat_seconds)
            store.heartbeat_run(
                run_id=str(run.get("run_id") or ""),
                lease_owner=worker_id,
                lease_seconds=lease_seconds,
            )

    async def process_stream() -> dict[str, Any]:
        run_input = build_agent_run_input(run)
        done_event: dict[str, Any] | None = None
        last_seq = int(run.get("last_event_seq") or 0)
        async for event in stream_agent_reply(run_input):
            last_seq = max(last_seq, int(event.get("seq") or 0))
            store.append_run_event(
                session_id=str(run.get("session_id") or ""),
                message_id=str(run.get("message_id") or ""),
                run_id=str(run.get("run_id") or ""),
                event=event,
            )
            store.heartbeat_run(
                run_id=str(run.get("run_id") or ""),
                lease_owner=worker_id,
                lease_seconds=lease_seconds,
                last_event_seq=last_seq,
            )
            await _maybe_call(on_event, event)
            if str(event.get("type") or "") == "done":
                done_event = event
                break
            if store.is_run_cancel_requested(str(run.get("run_id") or "")):
                done_event = _build_terminal_event(
                    run,
                    seq=last_seq + 1,
                    status="cancelled",
                    code="run_cancelled",
                    message="任务已取消",
                )
                store.append_run_event(
                    session_id=str(run.get("session_id") or ""),
                    message_id=str(run.get("message_id") or ""),
                    run_id=str(run.get("run_id") or ""),
                    event=done_event,
                )
                await _maybe_call(on_event, done_event)
                break

        if done_event is None:
            done_event = _build_terminal_event(
                run,
                seq=max(1, last_seq + 1),
                status="failed",
                code="done_missing",
                message="模型未返回完成事件",
            )
            store.append_run_event(
                session_id=str(run.get("session_id") or ""),
                message_id=str(run.get("message_id") or ""),
                run_id=str(run.get("run_id") or ""),
                event=done_event,
            )
            await _maybe_call(on_event, done_event)

        done_payload = done_event.get("payload") or {}
        message_payload = _done_payload_to_message(done_payload, run)
        store.save_assistant_message(**message_payload)
        store.finish_run(
            run_id=str(run.get("run_id") or ""),
            status=str(done_payload.get("status") or "success"),
            error=message_payload.get("error"),
            last_event_seq=int(done_event.get("seq") or 0),
        )
        return store.get_run(str(run.get("run_id") or "")) or run

    try:
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(heartbeat_loop)
            finished_run = await process_stream()
            task_group.cancel_scope.cancel()
        return finished_run
    except Exception as exc:
        logger.exception("run execution failed: run_id=%s", run.get("run_id"))
        last_seq = int((store.get_run(str(run.get("run_id") or "")) or {}).get("last_event_seq") or 0)
        done_event = _build_terminal_event(
            run,
            seq=max(1, last_seq + 1),
            status="failed",
            code="run_execution_failed",
            message=str(exc),
        )
        store.append_run_event(
            session_id=str(run.get("session_id") or ""),
            message_id=str(run.get("message_id") or ""),
            run_id=str(run.get("run_id") or ""),
            event=done_event,
        )
        await _maybe_call(on_event, done_event)
        message_payload = _done_payload_to_message(done_event.get("payload") or {}, run)
        store.save_assistant_message(**message_payload)
        store.finish_run(
            run_id=str(run.get("run_id") or ""),
            status="failed",
            error=message_payload.get("error"),
            last_event_seq=int(done_event.get("seq") or 0),
        )
        return store.get_run(str(run.get("run_id") or "")) or run


class RunWorker:
    def __init__(self, *, store: SessionStore | None = None, worker_id: str | None = None):
        self.store = store or get_session_store()
        self.worker_id = worker_id or build_worker_id()

    async def run_forever(self):
        self.store.init_schema()
        cfg = get_settings()
        poll_interval = max(1, int(cfg.run_worker_poll_interval_seconds or 2))
        lease_seconds = max(1, int(cfg.run_worker_lease_seconds or 30))
        logger.info("Run worker started worker_id=%s poll_interval=%s", self.worker_id, poll_interval)
        while True:
            run = self.store.claim_runnable_run(worker_id=self.worker_id, lease_seconds=lease_seconds)
            if not run:
                await anyio.sleep(poll_interval)
                continue
            await execute_run(self.store, run, worker_id=self.worker_id)
