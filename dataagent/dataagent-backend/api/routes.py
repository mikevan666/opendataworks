from __future__ import annotations

import logging
from typing import AsyncIterator

import anyio
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from config import get_settings
from core.magic_events import TERMINAL_TASK_STATUSES, encode_sse
from core.task_coordinator import get_task_coordinator
from core.task_submission_service import compute_next_run_at, current_utc_naive, submit_message_task
from core.topic_task_store import get_topic_task_store
from models.schemas import (
    CancelTaskResponse,
    CreateTaskRequest,
    CreateTopicRequest,
    DeliverMessageRequest,
    MessageQueuePageResponse,
    MessageQueueQueryRequest,
    MessageQueueRecord,
    MessageQueueUpsertRequest,
    MessageScheduleLogPageResponse,
    MessageScheduleLogsQueryRequest,
    MessageSchedulePageResponse,
    MessageScheduleQueryRequest,
    MessageScheduleRecord,
    MessageScheduleUpsertRequest,
    TaskEventPageResponse,
    TaskEventRecord,
    TaskStatusResponse,
    TaskSubmissionResponse,
    TopicDetail,
    TopicMessagePageResponse,
    TopicSummary,
    UpdateTopicRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/nl2sql")
topic_router = APIRouter(prefix="/topics")
task_router = APIRouter(prefix="/tasks")
queue_router = APIRouter(prefix="/message-queue")
schedule_router = APIRouter(prefix="/message-schedule")


@router.get("/health")
async def api_health():
    cfg = get_settings()
    return {
        "status": "ok",
        "provider_id": cfg.llm_provider,
        "model": cfg.claude_model,
        "skills_output_dir": cfg.skills_output_dir,
        "redis_host": cfg.redis_host,
        "redis_port": cfg.redis_port,
    }


@topic_router.post("", response_model=TopicDetail)
async def api_create_topic(request: CreateTopicRequest | None = None):
    store = _get_store()
    payload = request or CreateTopicRequest()
    topic = store.create_topic(title=str(payload.title or "").strip() or "新话题")
    return TopicDetail.model_validate(topic)


@topic_router.get("", response_model=list[TopicSummary])
async def api_list_topics():
    store = _get_store()
    topics = store.list_topics(include_messages=False)
    return [TopicSummary.model_validate(item) for item in topics]


@topic_router.get("/{topic_id}", response_model=TopicDetail)
async def api_get_topic(topic_id: str):
    topic = _require_topic(topic_id)
    return TopicDetail.model_validate(topic)


@topic_router.put("/{topic_id}", response_model=TopicDetail)
async def api_update_topic(topic_id: str, request: UpdateTopicRequest):
    title = str(request.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    _require_topic(topic_id)
    topic = _get_store().update_topic(topic_id, title=title)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return TopicDetail.model_validate(topic)


@topic_router.delete("/{topic_id}")
async def api_delete_topic(topic_id: str):
    store = _get_store()
    store.delete_topic(topic_id)
    return JSONResponse({"status": "ok"})


@topic_router.get("/{topic_id}/messages", response_model=TopicMessagePageResponse)
async def api_list_topic_messages(
    topic_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=200, ge=1, le=500),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
):
    _require_topic(topic_id)
    payload = _get_store().list_topic_messages_page(topic_id=topic_id, page=page, page_size=page_size, order=order)
    return TopicMessagePageResponse.model_validate(payload)


@task_router.post("/deliver-message", response_model=TaskSubmissionResponse)
async def api_deliver_message(request: DeliverMessageRequest):
    topic_id = str(request.topic_id or "").strip()
    content = str(request.content or "").strip()
    if not topic_id:
        raise HTTPException(status_code=400, detail="topic_id is required")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    _require_topic(topic_id)
    try:
        submitted = await submit_message_task(
            topic_id=topic_id,
            message_type="text",
            message_content=content,
            provider_id=request.provider_id,
            model=request.model,
            database_hint=request.database,
            debug=bool(request.debug),
            execution_mode=request.execution_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskSubmissionResponse.model_validate(submitted)


@task_router.post("", response_model=TaskSubmissionResponse)
async def api_create_task(request: CreateTaskRequest):
    topic_id = str(request.topic_id or "").strip()
    if not topic_id:
        raise HTTPException(status_code=400, detail="topic_id is required")
    _require_topic(topic_id)
    try:
        submitted = await submit_message_task(
            topic_id=topic_id,
            message_type=request.message_type,
            message_content=request.message_content,
            provider_id=request.provider_id,
            model=request.model,
            database_hint=request.database,
            debug=bool(request.debug),
            execution_mode=request.execution_mode,
            source_queue_id=request.source_queue_id,
            source_schedule_id=request.source_schedule_id,
            source_schedule_log_id=request.source_schedule_log_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskSubmissionResponse.model_validate(submitted)


@task_router.get("/{task_id}", response_model=TaskStatusResponse)
async def api_get_task(task_id: str):
    store = _get_store()
    task = store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse.model_validate(task)


@task_router.get("/{task_id}/events", response_model=TaskEventPageResponse)
async def api_get_task_events(
    task_id: str,
    after_seq: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=1000),
):
    store = _get_store()
    task = store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    page = store.list_task_events(task_id=task_id, after_seq=after_seq, limit=limit)
    return TaskEventPageResponse.model_validate(
        {
            "task_id": task_id,
            "task_status": str(page.get("task_status") or task.get("task_status") or "waiting"),
            "after_seq": int(page.get("after_seq") or after_seq),
            "next_after_seq": int(page.get("next_after_seq") or after_seq),
            "has_more": bool(page.get("has_more")),
            "events": [TaskEventRecord.model_validate(item) for item in page.get("events") or []],
        }
    )


@task_router.get("/{task_id}/events/stream")
async def api_stream_task_events(task_id: str, after_seq: int = Query(default=0, ge=0)):
    store = _get_store()
    task = store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return StreamingResponse(
        _stream_task_events(task_id=task_id, after_seq=after_seq),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@task_router.post("/{task_id}/cancel", response_model=CancelTaskResponse)
async def api_cancel_task(task_id: str):
    store = _get_store()
    task = store.request_task_cancel(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await get_task_coordinator().request_cancel(task_id)
    task = store.get_task(task_id) or task
    return CancelTaskResponse.model_validate(task)


@queue_router.post("/queries", response_model=MessageQueuePageResponse)
async def api_query_message_queues(request: MessageQueueQueryRequest):
    page = _get_store().query_message_queues(topic_id=request.topic_id, page=request.page, page_size=request.page_size)
    return MessageQueuePageResponse.model_validate(
        {
            "page": int(page.get("page") or request.page),
            "page_size": int(page.get("page_size") or request.page_size),
            "total": int(page.get("total") or 0),
            "list": [MessageQueueRecord.model_validate(item) for item in page.get("items") or []],
        }
    )


@queue_router.post("", response_model=MessageQueueRecord)
async def api_create_message_queue(request: MessageQueueUpsertRequest):
    topic_id = str(request.topic_id or "").strip()
    if not topic_id:
        raise HTTPException(status_code=400, detail="topic_id is required")
    _require_topic(topic_id)
    created = _get_store().create_message_queue(
        topic_id=topic_id,
        message_type=str(request.message_type or "").strip() or "text",
        message_content=request.message_content,
    )
    return MessageQueueRecord.model_validate(created)


@queue_router.put("/{queue_id}", response_model=MessageQueueRecord)
async def api_update_message_queue(queue_id: str, request: MessageQueueUpsertRequest):
    _require_topic(str(request.topic_id or "").strip())
    updated = _get_store().update_message_queue(
        queue_id=queue_id,
        topic_id=str(request.topic_id or "").strip(),
        message_type=str(request.message_type or "").strip() or "text",
        message_content=request.message_content,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Queue message not found")
    return MessageQueueRecord.model_validate(updated)


@queue_router.delete("/{queue_id}")
async def api_delete_message_queue(queue_id: str):
    deleted = _get_store().delete_message_queue(queue_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Queue message not found")
    return JSONResponse({"status": "ok"})


@queue_router.post("/{queue_id}/consume", response_model=TaskSubmissionResponse)
async def api_consume_message_queue(queue_id: str):
    store = _get_store()
    queue = store.get_message_queue(queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue message not found")
    if str(queue.get("status") or "") == "running":
        raise HTTPException(status_code=409, detail="Queue message is already running")
    try:
        submitted = await submit_message_task(
            topic_id=str(queue.get("topic_id") or ""),
            message_type=str(queue.get("message_type") or "text"),
            message_content=queue.get("message_content"),
            execution_mode="background",
            source_queue_id=str(queue.get("queue_id") or ""),
            source_schedule_id=str(queue.get("source_schedule_id") or "") or None,
            source_schedule_log_id=str(queue.get("source_schedule_log_id") or "") or None,
        )
    except ValueError as exc:
        store.mark_message_queue_failed(queue_id=queue_id, error_message=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TaskSubmissionResponse.model_validate(submitted)


@schedule_router.post("/queries", response_model=MessageSchedulePageResponse)
async def api_query_message_schedules(request: MessageScheduleQueryRequest):
    page = _get_store().query_message_schedules(topic_id=request.topic_id, page=request.page, page_size=request.page_size)
    return MessageSchedulePageResponse.model_validate(
        {
            "page": int(page.get("page") or request.page),
            "page_size": int(page.get("page_size") or request.page_size),
            "total": int(page.get("total") or 0),
            "list": [MessageScheduleRecord.model_validate(item) for item in page.get("items") or []],
        }
    )


@schedule_router.post("", response_model=MessageScheduleRecord)
async def api_create_message_schedule(request: MessageScheduleUpsertRequest):
    topic_id = str(request.topic_id or "").strip()
    if not topic_id:
        raise HTTPException(status_code=400, detail="topic_id is required")
    _require_topic(topic_id)
    try:
        next_run_at = compute_next_run_at(request.cron_expr, request.timezone) if request.enabled else None
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid cron_expr or timezone: {exc}") from exc
    created = _get_store().create_message_schedule(
        topic_id=topic_id,
        name=str(request.name or "").strip(),
        message_type=str(request.message_type or "").strip() or "text",
        message_content=request.message_content,
        cron_expr=str(request.cron_expr or "").strip(),
        enabled=bool(request.enabled),
        timezone=str(request.timezone or "").strip() or "Asia/Shanghai",
        next_run_at=next_run_at,
    )
    return MessageScheduleRecord.model_validate(created)


@schedule_router.put("/{schedule_id}", response_model=MessageScheduleRecord)
async def api_update_message_schedule(schedule_id: str, request: MessageScheduleUpsertRequest):
    topic_id = str(request.topic_id or "").strip()
    _require_topic(topic_id)
    try:
        next_run_at = compute_next_run_at(request.cron_expr, request.timezone) if request.enabled else None
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid cron_expr or timezone: {exc}") from exc
    updated = _get_store().update_message_schedule(
        schedule_id=schedule_id,
        topic_id=topic_id,
        name=str(request.name or "").strip(),
        message_type=str(request.message_type or "").strip() or "text",
        message_content=request.message_content,
        cron_expr=str(request.cron_expr or "").strip(),
        enabled=bool(request.enabled),
        timezone=str(request.timezone or "").strip() or "Asia/Shanghai",
        next_run_at=next_run_at,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Message schedule not found")
    return MessageScheduleRecord.model_validate(updated)


@schedule_router.delete("/{schedule_id}")
async def api_delete_message_schedule(schedule_id: str):
    deleted = _get_store().delete_message_schedule(schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Message schedule not found")
    return JSONResponse({"status": "ok"})


@schedule_router.get("/{schedule_id}", response_model=MessageScheduleRecord)
async def api_get_message_schedule(schedule_id: str):
    schedule = _get_store().get_message_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Message schedule not found")
    return MessageScheduleRecord.model_validate(schedule)


@schedule_router.post("/{schedule_id}/logs", response_model=MessageScheduleLogPageResponse)
async def api_list_message_schedule_logs(schedule_id: str, request: MessageScheduleLogsQueryRequest):
    schedule = _get_store().get_message_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Message schedule not found")
    payload = _get_store().list_message_schedule_logs(
        schedule_id=schedule_id,
        page=request.page,
        page_size=request.page_size,
    )
    return MessageScheduleLogPageResponse.model_validate(
        {
            "schedule_id": schedule_id,
            "page": int(payload.get("page") or request.page),
            "page_size": int(payload.get("page_size") or request.page_size),
            "total": int(payload.get("total") or 0),
            "list": payload.get("items") or [],
        }
    )


router.include_router(topic_router)
router.include_router(task_router)
router.include_router(queue_router)
router.include_router(schedule_router)


async def _stream_task_events(task_id: str, after_seq: int) -> AsyncIterator[str]:
    cfg = get_settings()
    poll_interval = max(1, int(cfg.run_events_stream_poll_interval_seconds or 1))
    ping_seconds = max(5, int(cfg.run_events_stream_ping_seconds or 10))
    next_after_seq = max(0, after_seq)
    since_ping = 0
    store = _get_store()

    while True:
        page = store.list_task_events(task_id=task_id, after_seq=next_after_seq, limit=200)
        events = list(page.get("events") or [])
        for event in events:
            next_after_seq = max(next_after_seq, int(event.get("seq_id") or 0))
            yield encode_sse(event)
        if events:
            since_ping = 0
        else:
            since_ping += poll_interval
            if since_ping >= ping_seconds:
                yield ": ping\n\n"
                since_ping = 0

        task = store.get_task(task_id)
        if not task:
            break
        if str(task.get("task_status") or "") in TERMINAL_TASK_STATUSES and not page.get("has_more") and not events:
            break
        await anyio.sleep(poll_interval)


def _get_store():
    store = get_topic_task_store()
    store.init_schema()
    return store


def _require_topic(topic_id: str) -> dict:
    store = _get_store()
    topic = store.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic
