# NL2SQL Async Background Task Design

**Date:** 2026-03-12
**Goal:** 让智能问数支持 `30-60` 分钟级长任务，将“用户等多久”和“任务能活多久”彻底解耦，同时保持通用 agent 模块与 skill 规则解耦。
**Tech Stack:** 前端使用 `Vue 3`、`Vite 5`、`Vue Router 4`、`Pinia`、`Element Plus`，并允许在新增智能问数界面中增量引入 `Tailwind CSS`；主后端使用 `Java 8`、`Spring Boot 2.7`、`MyBatis-Plus`、`MySQL 8`、`Flyway`；智能问数后端使用 `Python`、`FastAPI`、`Pydantic`、`PyMySQL`、`Alembic`、`AnyIO`；部署层使用 `nginx` 与 `Docker Compose`。

## Scope

- 覆盖 `dataagent/dataagent-backend` 的 run 生命周期、持久化模型、接口、worker、超时与取消策略
- 覆盖前端智能问数页面对后台任务的提交、订阅、恢复与取消交互
- 覆盖智能问数链路中的超时分层与部署约束
- 参考 Cherry Studio、OpenClaw、NanoClaw、Open WebUI 的公开文档，形成适合本仓库的超时与后台任务方案

不在本设计范围内：

- 不实现全仓库通用任务平台
- 不引入 skill wrapper 层
- 不在本期把所有长任务统一抽象成独立基础设施服务

## Current State

- 当前每次提问都会在 `/api/v1/nl2sql/sessions/{session_id}/messages` 中同步创建并执行一次 run，要么直接走 SSE，要么等待非流式结果返回
- `run_id` 已存在，但当前仅作为消息与事件的关联键，并没有独立的 run 持久化模型
- 已有 `da_chat_session`、`da_chat_message`、`da_chat_block`、`da_chat_event`，但没有 `da_chat_run`
- 当前 agent 总超时由 `agent_timeout_seconds=180` 控制，并在 `core/nl2sql_agent.py` 中使用 `fail_after()` 强制终止
- 当前反向代理对 `/api/v1/nl2sql/` 的 `proxy_read_timeout` 和 `proxy_send_timeout` 为 `300s`
- 当前 `run_sql.py` 中数据库 `read_timeout` / `write_timeout` 硬编码为 `60s`
- 当前事件在 `_stream_message_events()` 中先保存在内存，等待 `done` 后才统一持久化

## Problem

- 当前“单次 HTTP 等待窗口”与“任务真实寿命”绑定在一起，任务即使持续有进展，到总超时也会被硬切断
- 浏览器断开、页面刷新或代理链路中断后，任务状态无法独立存在，也无法继续观察
- 没有后台排队、租约、恢复、取消模型，无法可靠支持长任务
- 事件持久化太晚，无法基于已落库事件做断点恢复或重新订阅
- 超时分层不清晰，当前 `180s` agent 超时、`300s` 代理超时、`60s` SQL 超时相互割裂

## Design

### 1. Core run model

- 将 `run_id` 升格为后台任务的唯一标识，不再引入独立 `job_id`
- 新增 `da_chat_run` 表，记录 run 的提交、排队、执行、完成、取消与超时状态
- 一个用户问题对应一个 run；一个 run 绑定一条 user message 和一条 assistant message

### 2. Execution modes

- `interactive`
  - 保留当前“用户发问后立即开始流式输出”的体验
  - run 仍会写入 `da_chat_run`
  - 默认总运行超时 `360s`
  - 默认 idle 超时 `90s`
- `background`
  - API 立即返回 `202 Accepted`
  - 前端通过 `run_id` 单独订阅事件或查询状态
  - 默认总运行超时 `1800s`
  - 默认 idle 超时 `300s`
- `auto`
  - 服务端先等待 `20s`
  - 如果 run 在等待窗口内完成，则按同步结果返回
  - 如果超过等待窗口仍在运行，则返回 `202 Accepted`，run 自动转为后台继续执行

### 3. Worker model

- 引入独立 worker 进程，不把长任务执行绑定在 Web 请求协程里
- Web 进程职责：
  - 创建 run
  - 预创建 assistant message 占位记录
  - 提供状态查询、事件订阅、取消接口
- Worker 进程职责：
  - 从 `da_chat_run` 中领取 `queued` run
  - 通过租约字段避免多 worker 重复消费
  - 执行 agent、写入事件、维护心跳、处理取消与超时
- v1 使用 MySQL 持久化队列，不引入 Celery 或 Redis

### 4. Event and message persistence

- `da_chat_event` 改为真正的 append-only 运行日志
- 事件产生后立即批量落库，不等待 `done`
- `da_chat_message` 与 `da_chat_block` 作为 assistant message 的快照层：
  - 运行中允许多次更新 `status/content/blocks`
  - 完成时写入最终结果
- 前端恢复页面时：
  - 先拉 session/message 快照
  - 再根据 `run_id` 从事件接口补齐运行中增量

### 5. Timeout model

- `wait timeout`
  - 控制当前这次请求愿意等待多久
  - 默认 `20s`
  - 超时仅结束等待，不结束 run
- `run timeout`
  - 控制 run 的最大生命周期
  - `interactive=360s`
  - `background=1800s`
- `idle timeout`
  - 控制长时间无事件且无 worker 心跳的异常 run
  - `interactive=90s`
  - `background=300s`
- `SQL timeout`
  - 从脚本硬编码改为环境变量驱动
  - `interactive read timeout=300s`
  - `background read timeout=1200s`
  - `write timeout=60s`
- `proxy timeout`
  - 只需要覆盖单次事件订阅或同步等待窗口
  - 不再承担整个后台任务寿命

### 6. Cancellation

- 取消是显式 API 行为，不以浏览器断链作为取消信号
- `POST /runs/{run_id}/cancel` 会写入 `cancel_requested_at`
- Worker 在安全检查点检测取消请求并尽快终止执行
- run 结束状态新增 `cancelled`

### 7. Frontend behavior

- 发送消息后优先拿到 `assistant_message_id` 和 `run_id`
- `interactive` 与 `auto` 在前 `20s` 内仍可直接消费实时流
- 一旦进入 `background`：
  - UI 显示“后台执行中”
  - 支持刷新后恢复
  - 支持手动取消
  - 支持重新订阅事件流

### 8. Compatibility

- 保留现有会话与消息模型，不推翻 `session/message/block/event` 体系
- 新增 `run` 层，不把 skill 规则写回通用 agent 模块
- 智能问数脚本调用继续坚持：
  - `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/<name>.py" ...`
- 不重新引入 wrapper，不接受 `/app/scripts/...` 这类部署猜测路径

## Interfaces / Data Model

### API changes

- `SendMessageRequest`
  - 新增 `execution_mode: "interactive" | "background" | "auto"`
  - 新增 `wait_timeout_seconds: int | null`
- 新增 `GET /api/v1/nl2sql/runs/{run_id}`
- 新增 `GET /api/v1/nl2sql/runs/{run_id}/events?after_seq=<n>`
- 新增 `POST /api/v1/nl2sql/runs/{run_id}/cancel`

### Response model

- assistant message `status` 扩展为：
  - `queued`
  - `running`
  - `success`
  - `failed`
  - `cancelled`
  - `timeout`
- run 状态响应至少包含：
  - `run_id`
  - `session_id`
  - `assistant_message_id`
  - `status`
  - `mode`
  - `last_event_seq`
  - `started_at`
  - `finished_at`
  - `error`

### `da_chat_run`

建议字段：

- `run_id` 主键
- `session_id`
- `user_message_id`
- `assistant_message_id`
- `mode`
- `status`
- `provider_id`
- `model_name`
- `wait_timeout_seconds`
- `run_timeout_seconds`
- `idle_timeout_seconds`
- `last_event_seq`
- `heartbeat_at`
- `started_at`
- `finished_at`
- `cancel_requested_at`
- `lease_owner`
- `lease_expires_at`
- `error_json`
- `created_at`
- `updated_at`

## Risks / Alternatives

### MySQL queue vs Redis/Celery

- 选型：v1 使用 MySQL 队列
- 原因：
  - 当前 DataAgent 已经依赖 MySQL 持久化 session/message/event
  - 引入 Redis/Celery 会增加部署面与运维复杂度
  - 当前目标是先把 run 生命周期独立出来，而不是建设通用分布式任务平台

### `run_id` vs `job_id`

- 选型：直接复用 `run_id`
- 原因：
  - 当前消息和事件都已经围绕 `run_id`
  - 新引入 `job_id` 只会增加映射与前端理解成本

### 仅拉长同步 SSE 超时

- 选型：不采用
- 原因：
  - 单次同步请求挂到 `30-60` 分钟会放大浏览器、代理、worker 长连接风险
  - 无法解决断线恢复、重新订阅与显式取消问题

### 参考系统结论

- OpenClaw：明确区分等待超时和任务寿命，等待超时不等于任务终止，最接近本设计目标
  - [Agent Loop](https://docs.openclaw.ai/agent-loop)
  - [Session Tool](https://docs.openclaw.ai/session-tool)
  - [Configuration Reference](https://docs.openclaw.ai/gateway/configuration-reference)
  - [Background Process](https://docs.openclaw.ai/background-process)
- Open WebUI：主要提供请求级 timeout 配置，适合控制 API 调用等待时长，但不是后台任务模型
  - [Environment Variable Configuration](https://docs.openwebui.com/reference/env-configuration/)
  - [Server Connectivity Issues](https://docs.openwebui.com/troubleshooting/connection-error/)
- Cherry Studio：公开文档更多聚焦客户端或提供商请求超时与 MCP 安装问题，没有像 OpenClaw 那样公开的后台 run 生命周期模型
  - [FAQ](https://docs.cherry-ai.com/question-contact/questions)
  - [MCP Installation](https://docs.cherry-ai.com/docs/en-us/advanced-basic/mcp/install)
- NanoClaw：公开资料强调调度、队列与并发控制，可参考其“持久化队列 + scheduler”思路，但未看到清晰的“等待超时 vs 任务寿命”分层
  - [Official Site](https://nanoclaw.net/)
  - [SPEC](https://github.com/gavrielc/nanoclaw/blob/main/docs/SPEC.md)

## Verification

- Alembic migration 能新增 `da_chat_run` 且不破坏现有 chat 表
- worker 能领取、续租、完成、失败和回收过期租约
- `auto` 模式在等待窗口后能转为后台执行，run 继续完成
- 页面刷新或 SSE 断开后，前端能基于 `run_id` 恢复订阅
- cancel 请求能把运行中的 run 切为 `cancelled`
- 超时分层可验证：
  - 等待超时只结束请求，不结束 run
  - run 超时结束后台任务
  - SQL timeout 不再被硬编码 `60s` 提前打断
