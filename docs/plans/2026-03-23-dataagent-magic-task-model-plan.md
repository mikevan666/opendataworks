# DataAgent Magic Task Model Implementation Plan

> Design: [../design/2026-03-23-dataagent-magic-task-model-design.md](../design/2026-03-23-dataagent-magic-task-model-design.md)

**Goal:** 把智能问数从 `session/run + worker` 迁到 `topic/task + embedded asyncio + Redis lease`，同时把运行态 HTTP 契约重收到 `topic/task/message-queue/message-schedule/admin` 五组资源，并保持事件协议为 Magic 风格生命周期事件与 `ChunkData`。

## Task 1: Replace the durable model and split runtime/admin interfaces

**Files**

- `dataagent/dataagent-backend/alembic/versions/20260323_000004_magic_task_model.py`
- `dataagent/dataagent-backend/core/topic_task_store.py`
- `dataagent/dataagent-backend/models/schemas.py`
- `dataagent/dataagent-backend/api/routes.py`
- `dataagent/dataagent-backend/api/admin_routes.py`
- `dataagent/dataagent-backend/core/task_submission_service.py`

**Steps**

1. 新建 `da_agent_topic/task/message/chunk`
2. 新建 `da_agent_message_queue / da_agent_message_schedule / da_agent_message_schedule_log`
3. 运行态路由切换到 `/topics` `/tasks` `/message-queue` `/message-schedule`
4. settings 从运行态拆到 `/api/v1/nl2sql-admin/settings`
5. 旧 `sessions/runs` 和旧 `/api/v1/nl2sql/settings` 不保留兼容入口

## Task 2: Embed execution and move coordination to Redis

**Files**

- `dataagent/dataagent-backend/core/task_coordinator.py`
- `dataagent/dataagent-backend/main.py`
- `dataagent/dataagent-backend/config.py`
- `dataagent/dataagent-backend/requirements.txt`
- `dataagent/dataagent-backend/worker_main.py`

**Steps**

1. 新增 `TaskCoordinator`
2. 新增 Redis lease / cancel / recovery lock
3. 新增 schedule scan loop，通过 Redis lock 触发 schedule fire
4. FastAPI startup 时启动 coordinator
5. 删除独立 `worker_main.py`

## Task 3: Adapt Claude output to Magic event records

**Files**

- `dataagent/dataagent-backend/core/task_executor.py`
- `dataagent/dataagent-backend/core/task_persistence.py`
- `dataagent/dataagent-backend/core/skill_admin_service.py`
- `dataagent/dataagent-backend/models/schemas.py`
- `frontend/src/views/settings/DataAgentConfig.vue`

**Steps**

1. 新增 `ClaudeToMagicAdapter`
2. 将 Claude SDK 输出改写为：
   - 生命周期事件
   - `ChunkData`
3. 持久化写入 `da_agent_message` 与 `da_agent_chunk`
4. assistant message 作为最终正文快照层持续更新
5. provider 配置增加 `supports_partial_messages`
6. 对 `supports_partial_messages=false` 的 provider 改走 message-level Claude 适配
7. provider 已返回真实错误时，优先写入真实错误，不再退化成 `exit code 1`
8. 用一套共享 reducer 统一 partial stream 与 message-level 的文本分类：
   - tool 前 assistant 纯文本先进 pending
   - 后续出现 `tool_use` 时按 `reasoning` flush
   - 只有 turn 终态才按 `content` commit
   - 每个 tool 边界前主动结束当前 `reasoning` phase，确保前端呈现为 `thinking -> tool -> thinking -> tool -> answer`

## Task 4: Update frontend consumption and client layering

**Files**

- `frontend/src/api/nl2sql.js`
- `frontend/src/api/dataagent.js`
- `frontend/src/views/intelligence/NL2SqlChat.vue`
- `frontend/src/views/intelligence/messageStream.js`

**Steps**

1. 客户端拆成 `topicApi`、`taskApi`、`messageQueueApi`、`scheduleApi`、`adminApi`
2. 聊天页发送入口改成 `/tasks/deliver-message`
3. 历史恢复改成 `getTopic + getTopicMessages`
4. `GET /topics/{topic_id}/messages` 的 assistant message 返回 `blocks + resume_after_seq`
5. SSE 消费改为 `TaskEventRecord`
6. 页面在运行中根据 Magic 事件重建思考、工具和正文块
7. 刷新后优先用历史 `blocks` hydrate，再从 `resume_after_seq` 继续订阅增量
8. settings 页改走 `nl2sql-admin`

## Task 5: Update deploy topology

**Files**

- `deploy/docker-compose.dev.yml`
- `deploy/docker-compose.prod.yml`
- `deploy/.env.example`

**Steps**

1. Compose 加 Redis
2. 移除 `dataagent-worker`
3. `dataagent-backend` 注入 Redis、task runner、schedule runner 配置

## Task 6: Verification

**Target verification**

- Python 语法编译通过
- DataAgent 后端单测至少覆盖：
  - `topics/tasks` 路由契约
  - queue CRUD / consume
  - schedule CRUD / logs
  - `supports_partial_messages=true/false` 两条执行路径
  - tool 前文本 delayed commit / finalize 分类
  - provider 真实错误透传
- 前端测试至少覆盖：
  - Magic 事件流渲染
  - 前端不做 bucket 重判，只按后端 `content_type` 渲染
  - `deliverMessage -> task stream -> topic messages hydrate`
  - `blocks + resume_after_seq` 历史恢复与增量续流
- 管理设置页至少验证：
  - `supports_partial_messages` 能正确读写
- 环境可用时继续补：
  - `backend + MySQL + Redis + frontend` 本地端到端 smoke
  - queue consume smoke
  - schedule trigger / log smoke
  - 租约失效恢复 smoke

## Rollout

1. 先升级 DataAgent schema
2. 再启 Redis
3. 再上线新的 `dataagent-backend`
4. 最后切前端到新的 runtime/admin split API

## Backout

- 这是破坏式切换
- 若需回退，只能回退整套 DataAgent 后端镜像、前端调用和数据库 schema 版本，不支持局部回滚到旧 `sessions/runs`
