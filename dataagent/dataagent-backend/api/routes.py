from __future__ import annotations

"""
DataAgent NL2SQL API（session + run + SSE events）
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator

import anyio
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from config import get_settings
from core.run_worker import (
    ACTIVE_RUN_STATUSES,
    TERMINAL_RUN_STATUSES,
    build_worker_id,
    execute_run,
    normalize_execution_mode,
    resolve_run_timeouts,
)
from core.skill_admin_service import (
    persist_admin_settings,
    resolve_runtime_provider_selection,
    resolved_chat_settings_payload,
)
from core.session_store import SessionStore, get_session_store
from core.stream_events import encode_sse
from models.schemas import (
    AcceptedRunResponse,
    AssistantMessageResponse,
    CancelRunResponse,
    MessageBlock,
    ProviderConfig,
    RunEventPageResponse,
    RunStatusResponse,
    SendMessageRequest,
    SessionDetail,
    SessionMessage,
    SessionSummary,
    SettingsResponse,
    SettingsUpdateRequest,
    StreamEvent,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nl2sql")

MAX_HISTORY_MESSAGES = 24
MAX_HISTORY_CONTENT_CHARS = 1600
SUPPORTED_PROVIDERS = {"anthropic", "openrouter", "anyrouter", "anthropic_compatible"}


@router.get("/health")
async def api_health():
    cfg = get_settings()
    return {
        "status": "ok",
        "provider_id": cfg.llm_provider,
        "model": cfg.claude_model,
        "skills_output_dir": cfg.skills_output_dir,
    }


@router.get("/settings", response_model=SettingsResponse)
async def api_get_settings():
    return _build_settings_response()


@router.put("/settings", response_model=SettingsResponse)
async def api_update_settings(request: SettingsUpdateRequest):
    patch = request.model_dump(exclude_none=True)
    if not patch:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        persisted = persist_admin_settings(patch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if persisted.get("provider_id") and persisted["provider_id"] not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail="provider_id must be one of anthropic/openrouter/anyrouter/anthropic_compatible",
        )
    return _build_settings_response()


@router.post("/sessions", response_model=SessionDetail)
async def api_create_session(title: str = Query(default="新会话")):
    store = _get_store()
    session_id = str(uuid.uuid4())
    session = store.create_session(session_id=session_id, title=title)
    return SessionDetail.model_validate(_normalize_session(session))


@router.get("/sessions", response_model=list[SessionSummary])
async def api_list_sessions():
    store = _get_store()
    sessions = store.list_sessions(include_messages=False)
    return [SessionSummary.model_validate(_normalize_session_summary(item)) for item in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def api_get_session(session_id: str):
    store = _get_store()
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionDetail.model_validate(_normalize_session(session))


@router.delete("/sessions/{session_id}")
async def api_delete_session(session_id: str):
    store = _get_store()
    store.delete_session(session_id)
    return {"status": "ok"}


@router.post("/sessions/{session_id}/messages")
async def api_send_message(session_id: str, request: SendMessageRequest):
    content = str(request.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    store = _get_store()
    run, placeholder = _create_run(store=store, session_id=session_id, request=request, content=content)
    mode = str(run.get("mode") or "interactive")

    if mode == "interactive":
        if request.stream:
            return StreamingResponse(
                _stream_interactive_run(store=store, run=run),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        return await _run_interactive(store=store, run=run)

    if request.stream:
        return StreamingResponse(
            _stream_persisted_run_events(store=store, run_id=str(run.get("run_id") or ""), after_seq=0),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return await _wait_for_run_or_accept(store=store, run=run, placeholder=placeholder)


@router.get("/runs/{run_id}", response_model=RunStatusResponse)
async def api_get_run(run_id: str):
    store = _get_store()
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunStatusResponse.model_validate(_normalize_run(run))


@router.get("/runs/{run_id}/events", response_model=RunEventPageResponse)
async def api_get_run_events(
    run_id: str,
    after_seq: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=1000),
):
    store = _get_store()
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    page = store.list_run_events(run_id=run_id, after_seq=after_seq, limit=limit)
    return RunEventPageResponse.model_validate(
        {
            "run_id": run_id,
            "status": str(run.get("status") or "queued"),
            "after_seq": int(page.get("after_seq") or after_seq),
            "next_after_seq": int(page.get("next_after_seq") or after_seq),
            "has_more": bool(page.get("has_more")),
            "events": [StreamEvent.model_validate(item) for item in page.get("events") or []],
        }
    )


@router.get("/runs/{run_id}/events/stream")
async def api_stream_run_events(run_id: str, after_seq: int = Query(default=0, ge=0)):
    store = _get_store()
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return StreamingResponse(
        _stream_persisted_run_events(store=store, run_id=run_id, after_seq=after_seq),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/runs/{run_id}/cancel", response_model=CancelRunResponse)
async def api_cancel_run(run_id: str):
    store = _get_store()
    run = store.request_run_cancel(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return CancelRunResponse.model_validate(
        {
            "run_id": str(run.get("run_id") or ""),
            "status": str(run.get("status") or ""),
            "cancel_requested_at": run.get("cancel_requested_at"),
        }
    )


def _build_settings_response() -> SettingsResponse:
    payload = resolved_chat_settings_payload()
    providers = [ProviderConfig.model_validate(item) for item in payload.get("providers") or []]
    return SettingsResponse(
        default_provider_id=str(payload.get("default_provider_id") or ""),
        default_model=str(payload.get("default_model") or ""),
        providers=providers,
        skills_output_dir=str(payload.get("skills_output_dir") or ""),
        mysql_host=str(payload.get("mysql_host") or ""),
        mysql_port=int(payload.get("mysql_port") or 3306),
        mysql_database=str(payload.get("mysql_database") or ""),
        doris_host=str(payload.get("doris_host") or ""),
        doris_port=int(payload.get("doris_port") or 9030),
        doris_database=str(payload.get("doris_database") or ""),
    )


def _create_run(
    *,
    store: SessionStore,
    session_id: str,
    request: SendMessageRequest,
    content: str,
) -> tuple[dict[str, Any], AssistantMessageResponse]:
    session = store.get_session(session_id)
    if not session:
        inferred_title = content[:30] + "..." if len(content) > 30 else content
        session = store.create_session(session_id=session_id, title=inferred_title or "新会话")

    user_message_id = f"u_{uuid.uuid4().hex[:24]}"
    store.append_user_message(session_id=session_id, message_id=user_message_id, content=content)

    session_after_user = store.get_session(session_id) or session
    messages = list(session_after_user.get("messages") or [])
    history_messages = [m for m in messages if str(m.get("message_id") or "") != user_message_id]
    history = _build_history_messages(history_messages[-MAX_HISTORY_MESSAGES:])

    try:
        resolved_target = resolve_runtime_provider_selection(request.provider_id, request.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    mode = normalize_execution_mode(request.execution_mode, stream=bool(request.stream))
    timeouts = resolve_run_timeouts(mode)
    if request.wait_timeout_seconds is not None:
        timeouts["wait_timeout_seconds"] = max(0, int(request.wait_timeout_seconds))

    run_id = f"run_{uuid.uuid4().hex[:24]}"
    assistant_message_id = f"a_{uuid.uuid4().hex[:24]}"
    placeholder_status = "running" if mode == "interactive" else "queued"

    store.save_assistant_message(
        session_id=session_id,
        message_id=assistant_message_id,
        run_id=run_id,
        content="",
        status=placeholder_status,
        stop_reason=None,
        stop_sequence=None,
        usage=None,
        blocks=[],
        error=None,
        provider_id=str(resolved_target.get("provider_id") or ""),
        model=str(resolved_target.get("model") or ""),
    )
    run = store.create_run(
        run_id=run_id,
        session_id=session_id,
        user_message_id=user_message_id,
        assistant_message_id=assistant_message_id,
        mode=mode,
        status=placeholder_status,
        provider_id=str(resolved_target.get("provider_id") or ""),
        model=str(resolved_target.get("model") or ""),
        question=content,
        history=history,
        database_hint=str(request.database or "").strip() or None,
        debug=bool(request.debug),
        timeout_seconds=int(timeouts.get("timeout_seconds") or 0),
        idle_timeout_seconds=int(timeouts.get("idle_timeout_seconds") or 0),
        wait_timeout_seconds=int(timeouts.get("wait_timeout_seconds") or 0),
        sql_read_timeout_seconds=int(timeouts.get("sql_read_timeout_seconds") or 0),
        sql_write_timeout_seconds=int(timeouts.get("sql_write_timeout_seconds") or 0),
    )

    placeholder = _load_message_from_session(store, session_id, assistant_message_id) or {
        "message_id": assistant_message_id,
        "run_id": run_id,
        "status": placeholder_status,
        "content": "",
        "provider_id": str(resolved_target.get("provider_id") or ""),
        "model": str(resolved_target.get("model") or ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return run, _to_assistant_message_response(placeholder)


async def _run_interactive(store: SessionStore, run: dict[str, Any]) -> AssistantMessageResponse:
    worker_id = f"api:{build_worker_id()}"
    finished = await execute_run(store, run, worker_id=worker_id)
    saved = _load_message_from_session(store, str(run.get("session_id") or ""), str(run.get("message_id") or ""))
    if not saved:
        raise HTTPException(status_code=500, detail="Run finished without assistant message")
    return _to_assistant_message_response(saved)


async def _stream_interactive_run(store: SessionStore, run: dict[str, Any]) -> AsyncIterator[str]:
    send_stream, receive_stream = anyio.create_memory_object_stream[dict[str, Any]](100)

    async def _produce():
        try:
            await execute_run(store, run, worker_id=f"api:{build_worker_id()}", on_event=send_stream.send)
        finally:
            await send_stream.aclose()

    async with anyio.create_task_group() as task_group:
        task_group.start_soon(_produce)
        async with receive_stream:
            async for event in receive_stream:
                yield encode_sse(event)
        task_group.cancel_scope.cancel()


async def _wait_for_run_or_accept(
    *,
    store: SessionStore,
    run: dict[str, Any],
    placeholder: AssistantMessageResponse,
):
    mode = str(run.get("mode") or "background")
    wait_timeout_seconds = max(0, int(run.get("wait_timeout_seconds") or 0))
    if mode == "background" or wait_timeout_seconds <= 0:
        return _build_run_accepted_response(run, placeholder)

    deadline = anyio.current_time() + wait_timeout_seconds
    while anyio.current_time() < deadline:
        current = store.get_run(str(run.get("run_id") or ""))
        if not current:
            raise HTTPException(status_code=404, detail="Run not found")
        if str(current.get("status") or "") in TERMINAL_RUN_STATUSES:
            saved = _load_message_from_session(
                store,
                str(current.get("session_id") or ""),
                str(current.get("message_id") or ""),
            )
            if saved:
                return _to_assistant_message_response(saved)
            break
        await anyio.sleep(0.5)
    return _build_run_accepted_response(run, placeholder)


def _build_run_accepted_response(run: dict[str, Any], placeholder: AssistantMessageResponse) -> AcceptedRunResponse:
    return AcceptedRunResponse(
        accepted=True,
        session_id=str(run.get("session_id") or ""),
        run_id=str(run.get("run_id") or ""),
        message_id=str(run.get("message_id") or ""),
        status=str(run.get("status") or "queued"),
        mode=str(run.get("mode") or "background"),
        wait_timeout_seconds=int(run.get("wait_timeout_seconds") or 0),
        message=placeholder,
    )


async def _stream_persisted_run_events(
    *,
    store: SessionStore,
    run_id: str,
    after_seq: int = 0,
) -> AsyncIterator[str]:
    cfg = get_settings()
    poll_interval = max(1, int(cfg.run_events_stream_poll_interval_seconds or 1))
    ping_interval = max(5, int(cfg.run_events_stream_ping_seconds or 10))
    next_after = max(0, after_seq)
    last_ping_at = anyio.current_time()

    while True:
        run = store.get_run(run_id)
        if not run:
            error_event = {
                "run_id": run_id,
                "session_id": "",
                "message_id": "",
                "seq": next_after + 1,
                "type": "error",
                "ts": datetime.now(timezone.utc).isoformat(),
                "payload": {"code": "run_not_found", "message": "Run not found"},
            }
            yield encode_sse(error_event)
            break

        page = store.list_run_events(run_id=run_id, after_seq=next_after, limit=200)
        events = list(page.get("events") or [])
        if events:
            for event in events:
                next_after = max(next_after, int(event.get("seq") or 0))
                yield encode_sse(event)
            if str(run.get("status") or "") in TERMINAL_RUN_STATUSES and next_after >= int(run.get("last_event_seq") or 0):
                break
            continue

        if (
            next_after == 0
            and str(run.get("status") or "") in TERMINAL_RUN_STATUSES
            and int(run.get("last_event_seq") or 0) == 0
        ):
            snapshot = _build_snapshot_done_event(store, run)
            if snapshot:
                yield encode_sse(snapshot)
            break

        if anyio.current_time() - last_ping_at >= ping_interval:
            yield encode_sse(
                {
                    "run_id": str(run.get("run_id") or ""),
                    "session_id": str(run.get("session_id") or ""),
                    "message_id": str(run.get("message_id") or ""),
                    "seq": next_after,
                    "type": "ping",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "payload": {"status": str(run.get("status") or "")},
                }
            )
            last_ping_at = anyio.current_time()

        if str(run.get("status") or "") in TERMINAL_RUN_STATUSES and next_after >= int(run.get("last_event_seq") or 0):
            break

        await anyio.sleep(poll_interval)


def _build_snapshot_done_event(store: SessionStore, run: dict[str, Any]) -> dict[str, Any] | None:
    message = _load_message_from_session(store, str(run.get("session_id") or ""), str(run.get("message_id") or ""))
    if not message:
        return None
    return {
        "run_id": str(run.get("run_id") or ""),
        "session_id": str(run.get("session_id") or ""),
        "message_id": str(run.get("message_id") or ""),
        "seq": max(1, int(run.get("last_event_seq") or 0) + 1),
        "type": "done",
        "ts": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "status": str(message.get("status") or "success"),
            "content": str(message.get("content") or ""),
            "blocks": message.get("blocks") if isinstance(message.get("blocks"), list) else [],
            "error": message.get("error") if isinstance(message.get("error"), dict) else None,
            "stop_reason": str(message.get("stop_reason") or "") or None,
            "stop_sequence": str(message.get("stop_sequence") or "") or None,
            "usage": message.get("usage") if isinstance(message.get("usage"), dict) else None,
            "provider_id": str(message.get("provider_id") or run.get("provider_id") or ""),
            "model": str(message.get("model") or run.get("model") or ""),
        },
    }


def _normalize_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": str(run.get("run_id") or ""),
        "session_id": str(run.get("session_id") or ""),
        "user_message_id": str(run.get("user_message_id") or ""),
        "message_id": str(run.get("message_id") or run.get("assistant_message_id") or ""),
        "mode": str(run.get("mode") or "background"),
        "status": str(run.get("status") or "queued"),
        "provider_id": str(run.get("provider_id") or ""),
        "model": str(run.get("model") or ""),
        "database_hint": str(run.get("database_hint") or "") or None,
        "timeout_seconds": int(run.get("timeout_seconds") or 0),
        "idle_timeout_seconds": int(run.get("idle_timeout_seconds") or 0),
        "wait_timeout_seconds": int(run.get("wait_timeout_seconds") or 0),
        "sql_read_timeout_seconds": int(run.get("sql_read_timeout_seconds") or 0),
        "sql_write_timeout_seconds": int(run.get("sql_write_timeout_seconds") or 0),
        "last_event_seq": int(run.get("last_event_seq") or 0),
        "cancel_requested_at": run.get("cancel_requested_at"),
        "started_at": run.get("started_at"),
        "heartbeat_at": run.get("heartbeat_at"),
        "finished_at": run.get("finished_at"),
        "error": run.get("error") if isinstance(run.get("error"), dict) else None,
        "created_at": str(run.get("created_at") or ""),
        "updated_at": str(run.get("updated_at") or ""),
    }


def _load_message_from_session(store: SessionStore, session_id: str, message_id: str) -> dict[str, Any] | None:
    session = store.get_session(session_id)
    if not session:
        return None
    for message in session.get("messages") or []:
        if str(message.get("message_id") or "") == message_id:
            return message
    return None


def _to_assistant_message_response(message: dict[str, Any]) -> AssistantMessageResponse:
    blocks: list[MessageBlock] = []
    for block in message.get("blocks") or []:
        if isinstance(block, dict):
            blocks.append(MessageBlock.model_validate(block))

    return AssistantMessageResponse(
        role="assistant",
        message_id=str(message.get("message_id") or ""),
        run_id=str(message.get("run_id") or ""),
        status=str(message.get("status") or "success"),
        content=str(message.get("content") or ""),
        stop_reason=str(message.get("stop_reason") or "") or None,
        stop_sequence=str(message.get("stop_sequence") or "") or None,
        usage=message.get("usage") if isinstance(message.get("usage"), dict) else None,
        blocks=blocks,
        error=message.get("error") if isinstance(message.get("error"), dict) else None,
        provider_id=str(message.get("provider_id") or ""),
        model=str(message.get("model") or ""),
        created_at=str(message.get("created_at") or ""),
    )


def _normalize_session_summary(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": str(session.get("session_id") or ""),
        "title": str(session.get("title") or "新会话"),
        "message_count": int(session.get("message_count") or 0),
        "last_message_preview": str(session.get("last_message_preview") or ""),
        "created_at": str(session.get("created_at") or ""),
        "updated_at": str(session.get("updated_at") or ""),
    }


def _normalize_session(session: dict[str, Any]) -> dict[str, Any]:
    messages = []
    for message in session.get("messages") or []:
        if not isinstance(message, dict):
            continue
        payload = {
            "message_id": str(message.get("message_id") or ""),
            "role": str(message.get("role") or "assistant"),
            "content": str(message.get("content") or ""),
            "status": str(message.get("status") or "success"),
            "stop_reason": str(message.get("stop_reason") or "") or None,
            "stop_sequence": str(message.get("stop_sequence") or "") or None,
            "usage": message.get("usage") if isinstance(message.get("usage"), dict) else None,
            "run_id": str(message.get("run_id") or "") or None,
            "blocks": message.get("blocks") if isinstance(message.get("blocks"), list) else [],
            "error": message.get("error") if isinstance(message.get("error"), dict) else None,
            "provider_id": str(message.get("provider_id") or "") or None,
            "model": str(message.get("model") or "") or None,
            "created_at": str(message.get("created_at") or ""),
        }
        messages.append(SessionMessage.model_validate(payload).model_dump())

    return {
        "session_id": str(session.get("session_id") or ""),
        "title": str(session.get("title") or "新会话"),
        "messages": messages,
        "created_at": str(session.get("created_at") or ""),
        "updated_at": str(session.get("updated_at") or ""),
    }


def _build_history_messages(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    for item in messages:
        role = str(item.get("role") or "")
        if role not in {"user", "assistant"}:
            continue
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        if len(content) > MAX_HISTORY_CONTENT_CHARS:
            content = content[:MAX_HISTORY_CONTENT_CHARS] + "..."
        history.append({"role": role, "content": content})
    return history


def _get_store() -> SessionStore:
    store = get_session_store()
    try:
        store.init_schema()
    except Exception as exc:
        logger.exception("session store init failed")
        raise HTTPException(status_code=500, detail=f"Session store unavailable: {exc}") from exc
    return store
