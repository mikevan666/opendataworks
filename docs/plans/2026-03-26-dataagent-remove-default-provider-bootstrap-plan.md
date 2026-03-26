# DataAgent Remove Default Provider Bootstrap Implementation Plan

> Design: [../design/2026-03-26-dataagent-remove-default-provider-bootstrap-design.md](../design/2026-03-26-dataagent-remove-default-provider-bootstrap-design.md)

**Goal:** 让 DataAgent 在未显式配置大模型供应商前保持“未配置”状态，而不是在启动或保存时自动回填 `openrouter + anthropic/claude-sonnet-4.5`。

## Task 1: Stop backend runtime and store defaults from inventing provider/model

**Files**

- `dataagent/dataagent-backend/config.py`
- `dataagent/dataagent-backend/core/skill_admin_service.py`
- `dataagent/dataagent-backend/core/skill_admin_store.py`

**Steps**

1. 将运行时默认 `llm_provider`、`claude_model` 改为空字符串
2. 调整 settings merge 逻辑，允许顶层 `provider_id`、`model` 为空
3. 调整 runtime provider selection，在没有可执行 provider 时返回明确错误
4. 保留 provider catalog 和 provider-specific base URL/supported models 展示逻辑

## Task 2: Remove frontend implicit selections

**Files**

- `frontend/src/views/intelligence/NL2SqlChat.vue`
- `frontend/src/views/settings/DataAgentConfig.vue`

**Steps**

1. 聊天页本地初始 provider/model 改为空
2. 设置加载后仅自动选择已启用 provider
3. 设置页保存时不再把空 provider 回退成 `openrouter`

## Task 3: Update regression coverage

**Files**

- `dataagent/dataagent-backend/tests/test_skill_admin_service.py`
- `dataagent/dataagent-backend/tests/test_skill_admin_store.py`
- `frontend/src/views/intelligence/__tests__/NL2SqlChat.spec.js`

**Steps**

1. 增加空启动 settings 不生成默认 provider/model 的测试
2. 增加无启用 provider 时 runtime selection 报错的测试
3. 调整聊天页 settings 加载测试，验证未配置时不再自动选中 `openrouter`

## Verification

- 后端：
  - `pytest dataagent/dataagent-backend/tests/test_skill_admin_service.py dataagent/dataagent-backend/tests/test_skill_admin_store.py`
- 前端：
  - 先执行 `nvm use`
  - 再跑最小相关测试
- 若本地 DataAgent 环境可直接启动，再补 `GET /api/v1/nl2sql-admin/settings` smoke，确认顶层 `provider_id/model` 为空

## Rollout

1. 合入后先观察空配置环境的启动日志与 settings 接口返回
2. 再让管理页完成显式 provider 配置
3. 最后验证聊天页发送路径

## Backout

- 若需要回退，恢复 `config.py`、`skill_admin_service.py`、`skill_admin_store.py`、前端初始选择逻辑即可
- 本次不涉及数据迁移，回退不需要回滚 schema
