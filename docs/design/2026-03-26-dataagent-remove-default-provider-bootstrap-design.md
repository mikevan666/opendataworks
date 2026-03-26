# DataAgent Remove Default Provider Bootstrap Design

**Date:** 2026-03-26  
**Goal:** 去掉 DataAgent 在未显式配置时自动回填 `openrouter + anthropic/claude-sonnet-4.5` 的行为，确保大模型供应商与模型选择只来自管理页已保存配置或显式运行时注入，而不是 `deploy` / 启动默认值。  
**Tech Stack:** 前端 `Vue 3` + `Vite 5` + `Element Plus`；DataAgent 后端 `FastAPI` + `Pydantic` + `PyMySQL`。

## Scope

- 覆盖 `dataagent/dataagent-backend` 的配置默认值、启动回填链路、provider 选择逻辑
- 覆盖智能问数聊天页和 DataAgent 设置页的前端初始默认值
- 覆盖针对该行为的后端与前端回归测试

不在范围内：

- 不改动 provider catalog 中的候选供应商列表和模型列表
- 不移除设置页中作为提示的默认 Base URL 占位语义
- 不在本次变更中调整 `da_agent_settings` 表结构默认值

## Current Problems

- `deploy/.env.example` 与 Compose 中的 provider/model 默认值已经清掉，但 `config.py` 仍默认 `llm_provider=openrouter`、`claude_model=anthropic/claude-sonnet-4.5`
- `main.py` 启动时会执行 `bootstrap_admin_settings()`，把运行时默认值合并并持久化到 `da_agent_settings`
- `skill_admin_store.py` 在读写 settings 记录时也会把空值补成 `openrouter + anthropic/claude-sonnet-4.5`
- 前端聊天页和设置页仍以内置默认值初始化，导致未配置时 UI 看起来像“已有默认供应商”

结果是：

- 从部署层看，系统仍然会在第一次启动时自动形成一套默认 provider/model
- 管理页没有完成显式配置时，界面状态和真实可执行状态容易不一致
- 用户很难判断“系统未配置”与“系统已配置但未校验通过”的区别

## Target State

- 未显式配置 provider/model 时：
  - 后端运行时 `llm_provider`、`claude_model` 为空字符串
  - `bootstrap_admin_settings()` 不再把 `openrouter` 或默认模型写入 `da_agent_settings`
  - 管理接口返回的顶层 `provider_id`、`model` 为空
  - 智能问数聊天页不再预选 `openrouter`
  - 发送请求前必须来自已启用 provider 的显式选择
- 已显式保存 provider/model 时：
  - 继续按当前管理页配置执行
  - provider 校验、enabled models、Base URL 推导和运行时注入逻辑保持不变

## Design

### 1. Runtime defaults become empty

- `config.py`
  - `llm_provider` 默认值改为空字符串
  - `claude_model` 默认值改为空字符串
- 健康检查与启动日志继续返回这两个字段，但允许为空

### 2. Bootstrap no longer invents provider/model

- `skill_admin_service.py`
  - 区分“空 provider”与“非法 provider”
  - 仅当 payload 中已有合法 provider，或 provider settings 中已有启用供应商时，才产生顶层 `provider_id`
  - `model` 仅从显式值或启用模型列表中解析，不再从 provider definition 默认模型兜底
  - `resolve_runtime_provider_selection()` 在没有任何可执行 provider 时直接报错，而不是隐式回退到 `openrouter`

### 3. Settings store keeps blank values blank

- `skill_admin_store.py`
  - settings payload / row 归一化时不再把空 `provider_id`、`model` 填成 `openrouter` 或 `anthropic/claude-sonnet-4.5`

### 4. Frontend defaults reflect “not configured”

- `frontend/src/views/intelligence/NL2SqlChat.vue`
  - 本地初始 `default_provider_id`、`default_model` 改为空
  - 加载管理设置后，只选择已启用 provider
- `frontend/src/views/settings/DataAgentConfig.vue`
  - 保存时不再把空 provider 回退成 `openrouter`

## Interfaces Affected

- `GET /api/v1/nl2sql/health`
  - `provider_id`、`model` 可能为空
- `GET /api/v1/nl2sql-admin/settings`
  - 顶层 `provider_id`、`model` 可能为空
- `POST /api/v1/nl2sql/tasks` / `POST /api/v1/nl2sql/tasks/deliver-message`
  - 在系统没有任何已启用 provider 时，会更早返回明确配置错误

## Risks

- 旧测试可能依赖 `openrouter` 作为默认 provider
- 若某些脚本默认读取健康检查中的 provider/model 非空，需要同步收敛预期
- 老数据如果已经保存了顶层 provider/model，不会自动清空；本次只保证“新启动/新保存时不再发明默认值”

## Verification

- 后端单测覆盖：
  - bootstrap 空运行时不落默认 provider/model
  - runtime selection 在无启用 provider 时失败
  - 已保存 provider settings 仍能解析正确 provider/model
- 前端单测覆盖：
  - 聊天页加载未配置 settings 时不再默认选中 `openrouter`
- 环境可用时补充本地 smoke：
  - 启动 DataAgent 后直接访问设置接口，确认 `provider_id/model` 为空
  - 在管理页完成 provider 配置后，再验证聊天页可以正常选择并发送
