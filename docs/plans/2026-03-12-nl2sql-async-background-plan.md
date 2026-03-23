# NL2SQL Async Background Task Implementation Plan

> Superseded on 2026-03-23 by [2026-03-23-dataagent-magic-task-model-plan.md](./2026-03-23-dataagent-magic-task-model-plan.md). The old `session/run + worker` execution plan is retained only for history.

> Design: [../design/2026-03-12-nl2sql-async-background-design.md](../design/2026-03-12-nl2sql-async-background-design.md)

**Goal:** 为智能问数引入后台任务 run 模型、独立 worker、可恢复事件流和分层超时，使长任务不再绑定单次 HTTP 请求寿命。
**Tech Stack:** `Vue 3`、`Vite 5`、`Vue Router 4`、`Pinia`、`Element Plus`，以及可按需增量引入的 `Tailwind CSS`；`Java 8`、`Spring Boot 2.7`、`MyBatis-Plus`、`MySQL 8`；`Python`、`FastAPI`、`Pydantic`、`PyMySQL`、`Alembic`、`AnyIO`；`nginx` 与 `Docker Compose`。

## Architecture Summary

- 保留 `session/message/block/event` 作为会话与消息视图层
- 新增 `run` 层作为后台任务生命周期模型，直接复用 `run_id`
- Web 进程负责提交 run、暴露状态与事件接口
- Worker 进程负责消费 run、执行 agent、写心跳、处理取消与超时
- 前端从“发消息后一直等一个请求”改为“发消息拿 run_id，再按 run 订阅或查询”

## Task 1: Add run persistence and storage contracts

**Files:**

- `dataagent/dataagent-backend/alembic/versions/<new_revision>_add_chat_run_table.py`
- `dataagent/dataagent-backend/core/session_store.py`
- `dataagent/dataagent-backend/models/schemas.py`

**Steps:**

1. 新增 Alembic migration，创建 `da_chat_run`，不修改已有初始化 migration。
2. 在 `session_store.py` 中新增 run 相关方法：
   - create run
   - claim queued runs with lease
   - heartbeat
   - append run events
   - update run status
   - request cancel
   - query run by `run_id`
3. 在 `models/schemas.py` 中新增 run 请求与响应模型，并扩展 assistant message `status` 枚举语义。

**Expected Result:**

- 运行层有独立持久化模型
- 现有 session/message/event 数据结构保持兼容
- Web 与 worker 都能通过统一 store 访问 run 状态

## Task 2: Submit runs through the API instead of executing directly in-request

**Files:**

- `dataagent/dataagent-backend/api/routes.py`
- `dataagent/dataagent-backend/models/schemas.py`

**Steps:**

1. 扩展 `SendMessageRequest`：
   - `execution_mode`
   - `wait_timeout_seconds`
2. 调整 `/sessions/{session_id}/messages`：
   - 继续创建 user message
   - 预创建 assistant message 占位记录
   - 创建 `da_chat_run`
   - 按 `interactive/background/auto` 决定是短等待还是立即返回 accepted
3. 新增 run 相关接口：
   - `GET /runs/{run_id}`
   - `GET /runs/{run_id}/events`
   - `POST /runs/{run_id}/cancel`

**Expected Result:**

- 每次提问先形成持久化 run
- 背景模式下 API 能立即返回 `run_id`
- Web 接口不再承担长任务的完整执行寿命

## Task 3: Introduce a dedicated worker and move run execution out of the request path

**Files:**

- `dataagent/dataagent-backend/core/run_worker.py`（新建）
- `dataagent/dataagent-backend/main.py`
- `dataagent/dataagent-backend/config.py`
- `dataagent/dataagent-backend/Dockerfile`
- `deploy/docker-compose.dev.yml`
- `deploy/docker-compose.prod.yml`

**Steps:**

1. 新建 `core/run_worker.py`，实现：
   - 轮询或阻塞领取 `queued` runs
   - 续租与心跳
   - 取消与超时检查
   - 运行结束后的状态落盘
2. 为 worker 增加配置开关与并发上限，例如：
   - `DATAAGENT_RUN_WORKER_ENABLED`
   - `DATAAGENT_RUN_WORKER_CONCURRENCY`
3. 在部署配置中新增 worker 进程，默认与 Web 进程分离部署。
4. `main.py` 仅负责 Web 应用启动，不把长任务 worker 隐式挂在请求进程里。

**Expected Result:**

- 长任务生命周期与 Web 请求解耦
- worker 可独立扩容和重启
- run 可在无前端连接的情况下继续执行

## Task 4: Persist events incrementally and support reconnectable streams

**Files:**

- `dataagent/dataagent-backend/api/routes.py`
- `dataagent/dataagent-backend/core/session_store.py`
- `dataagent/dataagent-backend/core/nl2sql_agent.py`

**Steps:**

1. 将当前“先缓存全部事件、结束后一次性保存”的逻辑改为增量落库。
2. 运行中定期刷新 assistant message 快照与 blocks，状态使用 `queued/running/success/failed/cancelled/timeout`。
3. `/runs/{run_id}/events` 支持从 `after_seq` 开始追增量事件。
4. `interactive` 模式下的 SSE 也改为从 run 事件流读取，保证与后台模式使用同一事件源。

**Expected Result:**

- 页面刷新后可按 `run_id` 恢复事件流
- 后台任务执行中途产生的事件不会因请求中断丢失
- 交互式流与后台流共享同一事实来源

## Task 5: Add mode-aware timeout, SQL timeout, and cancellation controls

**Files:**

- `dataagent/dataagent-backend/config.py`
- `dataagent/dataagent-backend/core/nl2sql_agent.py`
- `dataagent/.claude/skills/dataagent-nl2sql/scripts/run_sql.py`
- `frontend/nginx.conf`
- `deploy/docker-compose.dev.yml`
- `deploy/docker-compose.prod.yml`

**Steps:**

1. 将 timeout 配置拆分为：
   - `wait timeout` 默认 `20s`
   - `interactive run timeout` 默认 `360s`
   - `background run timeout` 默认 `1800s`
   - `interactive idle timeout` 默认 `90s`
   - `background idle timeout` 默认 `300s`
2. `run_sql.py` 改为从环境变量读取 SQL `read_timeout` 和 `write_timeout`，去掉硬编码 `60s`。
3. nginx 仅为单次流式连接提供足够窗口，不再假设需要覆盖全部后台运行时长。
4. `cancel` 逻辑通过 `cancel_requested_at` 驱动，worker 在安全检查点尽快中止。

**Expected Result:**

- 等待超时不再等同于任务终止
- 后台 run 有独立寿命与 idle 保护
- SQL 层 timeout 与 run 模式保持一致

## Task 6: Update frontend chat flow to be run-driven

**Files:**

- `frontend/src/api/nl2sql.js`
- `frontend/src/views/intelligence/NL2SqlChat.vue`

**Steps:**

1. 发送消息后统一接收 `assistant_message_id` 和 `run_id`。
2. 在 `interactive` 与 `auto` 模式下先消费短等待窗口内的流式结果。
3. 如果 run 进入后台：
   - 展示“后台执行中”
   - 支持重新连接 `/runs/{run_id}/events`
   - 页面刷新后自动恢复订阅
   - 提供取消入口
4. 错误提示区分：
   - 请求等待超时
   - run 执行失败
   - 网络中断

**Expected Result:**

- 前端不再依赖一次 `fetch` 挂到底
- 用户可观察、恢复和取消长任务
- UI 能正确区分等待超时与任务失败

## Task 7: Validate behavior and prepare rollout

**Files:**

- `dataagent/dataagent-backend/tests/test_session_store.py`
- `dataagent/dataagent-backend/tests/test_routes_contract.py`
- `dataagent/dataagent-backend/tests/test_nl2sql_agent.py`
- `docs/reports/` 下新增或更新验证记录（按需要）

**Steps:**

1. 为 run schema、API 合约、增量事件、取消、timeout 分层补充测试。
2. 补一条端到端验证路径：
   - 提交问题
   - 进入后台
   - 刷新恢复
   - 完成或取消
3. 灰度发布时先启 worker，再放开 `background` 或 `auto` 模式入口。
4. 保留 `interactive` 作为回退路径，出现异常时可先关闭 `background/auto`。

**Expected Result:**

- 新 run 模型有最小回归覆盖
- 具备灰度启用与快速回退路径
- 验证记录可追溯

## Verification

- `alembic upgrade head` 可顺利创建新 run 表
- 重点测试至少覆盖：
  - run 创建与状态流转
  - worker 领取、续租、回收
  - `interactive/background/auto` 三种模式
  - 事件增量落库与 `after_seq` 恢复
  - cancel 语义
  - mode-aware timeout
- 前端需验证：
  - 发送消息后出现后台执行状态
  - 刷新页面后恢复 run
  - 取消按钮生效
  - 错误文案区分等待超时与执行失败

## Rollout / Backout

- Rollout:
  - 先上线 schema 与 store
  - 再上线 worker 服务
  - 最后前端放开 `background` 或 `auto` 入口
- Backout:
  - 关闭 `background` 与 `auto`，只保留 `interactive`
  - 停 worker，但保留已写入的 run 表与事件表数据
  - 如需回退代码，run 相关表结构可保留，不要求立即删除
