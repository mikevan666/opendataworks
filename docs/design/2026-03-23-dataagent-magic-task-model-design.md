# DataAgent Magic Task Model Design

**Date:** 2026-03-23  
**Goal:** 以 `magic` 的 `topic/task/message/correlation` 身份模型和阶段事件模型重构智能问数运行时，去掉独立 worker，改为 `MySQL durable + Redis ephemeral + asyncio embedded`。  
**Tech Stack:** 前端 `Vue 3` + `Vite 5` + `Element Plus`；DataAgent 后端 `FastAPI` + `Pydantic` + `PyMySQL` + `Alembic` + `AnyIO` + `redis-py`；部署使用 `Docker Compose`。

## Scope

- 覆盖 `dataagent/dataagent-backend` 的身份模型、事件模型、执行协调与 API
- 覆盖前端智能问数页面对 `topic/task` 和 Magic 风格事件的消费
- 覆盖 `deploy/` 中的 Redis 与单服务 DataAgent 部署形态

不在范围内：

- 不引入 MQ
- 不保留旧 `sessions/runs` API 兼容壳
- 不迁移旧 `da_chat_*` 历史数据

## Current Problems

- 旧模型把问数执行表达成 `session/run/attempt`，和 `magic` 的 `topic/task/correlation` 语义不一致
- 独立 `dataagent-worker` 带来额外部署面和调试成本
- MySQL 既承担 durable truth 又承担 lease/claim 轮询，职责过重
- 前端依赖旧 `done/text.delta/thinking.delta/tool.*` 协议，无法直接对齐 `magic`
- 部分 `anthropic_compatible` relay 不支持 Claude SDK 的 `include_partial_messages`，会在连接早期返回 `invalid beta flag`
- 当前运行时把这类 provider 错误压扁成通用 `Command failed with exit code 1`，前端无法看到真实原因

## Target Model

### Identity model

- `topic`
  - 长期对话根对象
  - 字段：`topic_id`、`chat_topic_id`、`chat_conversation_id`、`current_task_id`、`current_task_status`、`title`
- `task`
  - 单次执行单元
  - 字段：`task_id`、`topic_id`、`from_task_id`、`task_status`、`prompt`
- `message`
  - 按 `magic` 的 `TaskMessageEntity / MessagePayload` 组织
  - 核心字段：`message_id`、`topic_id`、`task_id`、`sender_type`、`type`、`status`、`content`、`event`、`steps`、`tool`、`seq_id`、`correlation_id`、`parent_correlation_id`、`content_type`、`usage`

### Event model

- 生命周期事件：
  - `BEFORE_AGENT_THINK`
  - `AFTER_AGENT_THINK`
  - `BEFORE_AGENT_REPLY`
  - `AFTER_AGENT_REPLY`
  - `PENDING_TOOL_CALL`
  - `BEFORE_TOOL_CALL`
  - `AFTER_TOOL_CALL`
  - `AGENT_SUSPENDED`
  - `ERROR`
- 流式块事件：
  - `ChunkData`
  - 字段：`request_id`、`chunk_id`、`content`、`delta.status`、`delta.finish_reason`、`metadata.correlation_id`、`metadata.parent_correlation_id`、`metadata.model_id`、`metadata.content_type`
- `delta.status` 仅使用：
  - `START`
  - `STREAMING`
  - `END`
- `metadata.content_type` 仅使用：
  - `reasoning`
  - `content`

### Claude SDK adapter

- `claude-agent-sdk` 的 partial event 只在运行时适配层存在
- `ClaudeToMagicAdapter` 负责把 SDK 输出转成：
  - 生命周期事件
  - `ChunkData`
- 思考阶段遵循 `magic` 的边界：
  - 首次 reasoning 输出前发 `BEFORE_AGENT_THINK`
  - reasoning 自身按 `BEFORE_AGENT_REPLY(reasoning) -> ChunkData -> AFTER_AGENT_REPLY(reasoning)`
  - 只有在首次 answer 开始前才发 `AFTER_AGENT_THINK`
- 回答阶段遵循：
  - `BEFORE_AGENT_REPLY(content) -> ChunkData -> AFTER_AGENT_REPLY(content)`
- 工具阶段遵循：
  - `PENDING_TOOL_CALL -> BEFORE_TOOL_CALL -> AFTER_TOOL_CALL`

### Provider capability compatibility

- provider 配置增加 `supports_partial_messages`
  - `anthropic`、`openrouter`、`anyrouter` 默认 `true`
  - `anthropic_compatible` 默认 `false`
- 当 `supports_partial_messages=true` 时：
  - 继续使用 Claude SDK partial stream
  - 继续产出当前的细粒度 Magic `ChunkData`
- 当 `supports_partial_messages=false` 时：
  - 仍使用 Claude SDK tool-loop，但改为 message-level 适配
  - `AssistantMessage(TextBlock/ThinkingBlock)` 直接映射为阶段级 `BEFORE_AGENT_REPLY + ChunkData START/END + AFTER_AGENT_REPLY`
  - `AssistantMessage(ToolUseBlock)` / `UserMessage(ToolResultBlock)` 继续映射工具事件
  - 不再保证实时思考增量
- 若 SDK 已返回真实 provider 错误文本：
  - 以 provider 原始错误为准持久化到 task error 和 Magic `ERROR` 事件
  - 不再退化成通用 `exit code 1`

## Runtime Model

### Durable vs ephemeral

- MySQL 保存 durable truth：
  - `da_agent_topic`
  - `da_agent_task`
  - `da_agent_message`
  - `da_agent_chunk`
- Redis 仅保存短状态：
  - `da:task:lease:{task_id}`
  - `da:task:cancel:{task_id}`
  - `da:task:recovery:lock`
- `asyncio` 负责本进程内队列、并发上限和 task 执行

### Embedded coordinator

- `dataagent-backend` 启动时拉起 `TaskCoordinator`
- 新 task 创建后：
  - 当前实例先尝试拿 Redis lease
  - 成功后入本地 `asyncio.Queue`
  - 执行中持续续租和写 MySQL heartbeat
- recovery loop 周期扫描：
  - `waiting` task
  - `running` 但 lease 已失效的 task
- lease 失效后：
  - 不复用旧 task
  - 新建 child task，`from_task_id = 旧 task_id`
  - `topic.current_task_id` 切到新 task
  - 新 task 从头重跑

## Public Interfaces

- 运行态保留统一前缀 `/api/v1/nl2sql`，按 `magic` 风格拆成 4 组：
  - `topic`
    - `POST /topics`
    - `GET /topics`
    - `GET /topics/{topic_id}`
    - `PUT /topics/{topic_id}`
    - `DELETE /topics/{topic_id}`
    - `GET /topics/{topic_id}/messages?page=1&page_size=200&order=asc|desc`
  - `task`
    - `POST /tasks/deliver-message`
    - `POST /tasks`
    - `GET /tasks/{task_id}`
    - `GET /tasks/{task_id}/events`
    - `GET /tasks/{task_id}/events/stream`
    - `POST /tasks/{task_id}/cancel`
  - `message queue`
    - `POST /message-queue/queries`
    - `POST /message-queue`
    - `PUT /message-queue/{queue_id}`
    - `DELETE /message-queue/{queue_id}`
    - `POST /message-queue/{queue_id}/consume`
  - `message schedule`
    - `POST /message-schedule/queries`
    - `POST /message-schedule`
    - `PUT /message-schedule/{schedule_id}`
    - `DELETE /message-schedule/{schedule_id}`
    - `GET /message-schedule/{schedule_id}`
    - `POST /message-schedule/{schedule_id}/logs`
- 管理态 settings 从运行态剥离到 `/api/v1/nl2sql-admin/settings`
- 删除旧接口：
  - `/api/v1/nl2sql/settings`
  - `POST /api/v1/nl2sql/topics/{topic_id}/messages`
- `deliver-message` 是交互式发送主入口，只返回 ids 和 task 状态：
  - `accepted`
  - `topic_id`
  - `task_id`
  - `task_status`
  - `user_message_id`
  - `assistant_message_id`
- provider 设置响应在 `ProviderConfig` 中增加 `supports_partial_messages`
- `da_agent_settings.raw_json` 持久化 `provider_settings.<provider_id>.supports_partial_messages`
- queue / schedule 为本次新增 durable 入口，因此需要 Alembic

## Persistence Changes

- 新建：
  - `da_agent_topic`
  - `da_agent_task`
  - `da_agent_message`
  - `da_agent_chunk`
  - `da_agent_message_queue`
  - `da_agent_message_schedule`
  - `da_agent_message_schedule_log`
- 废弃：
  - `da_chat_session`
  - `da_chat_message`
  - `da_chat_block`
  - `da_chat_event`
  - `da_chat_run`
- 采用破坏式切换，不做历史迁移

## Frontend Strategy

- 页面结构保持当前智能问数视图，不重新设计交互壳
- 前端 API client 拆成 `topicApi`、`taskApi`、`messageQueueApi`、`scheduleApi`、`adminApi`
- 本地状态和事件订阅命名统一切到 `topic/task`
- 渲染逻辑改为消费：
  - 生命周期事件
  - `ChunkData`
- 聊天页发送路径固定为 `POST /tasks/deliver-message -> GET /tasks/{task_id}/events/stream`
- 历史 assistant message 通过 `GET /topics/{topic_id}` + `GET /topics/{topic_id}/messages` 两步恢复
- settings 页只走 `/api/v1/nl2sql-admin/settings`

## Deployment Changes

- `dataagent-worker` 从 Compose 中移除
- `dataagent-backend` 单服务同时承担：
  - API
  - embedded async execution
- `deploy/` 新增 Redis 依赖与相关环境变量
- `deploy/` 补充 queue / schedule runner 的扫描配置：
  - `DATAAGENT_SCHEDULE_SCAN_INTERVAL_SECONDS`
  - `DATAAGENT_SCHEDULE_SCAN_BATCH_SIZE`
  - `DATAAGENT_SCHEDULE_LOCK_TTL_SECONDS`

## Risks

- 这是破坏式 API 和 schema 切换，旧前端或旧脚本若仍调用 `sessions/runs` 会直接失效
- Redis lease 目前为轻量实现，后续若要继续贴近 `magic` 的成熟度，需要进一步强化原子续租与观测
- 历史 `blocks` 兼容层被收缩，旧消息不再从旧 `blocks` 快照恢复完整过程轨迹
