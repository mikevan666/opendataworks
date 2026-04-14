# Opendataagent Platform Plan

## Goal

把 `opendataagent` 的模型接入层收敛到 OpenOcta 风格，并在应用层增加窄范围 compat driver：

- 应用层负责 `ModelFactory`
- runtime 只消费 `ModelFactory`
- 默认 provider 改为 Anthropic
- provider 的 `Base URL / API Token` 持久化到 settings
- runtime 直接读页面配置，不再依赖模型环境变量
- 页面可新增供应商实例、增减模型
- 标准 provider 主链保持干净
- `wzw.pp.ua` 这类 Claude-compatible 但 tool-calling 非标准的网关，通过应用层 compat provider 支持
- 前端控制台按 `opendata-frontend-skill` 收口到统一企业工作台设计系统

## Scope

本轮仅覆盖以下内容：

- 回写现有 design / plan 文档
- 新增应用层模型工厂模块
- 收敛 runtime 输入边界
- 扩展 settings 数据模型和模型设置页，让每个 provider 可编辑 `Base URL / API Token`
- 扩展 settings 数据模型和模型设置页，让 provider catalog 可在页面中维护
- 增加应用层 compat provider
- 回正默认状态文件和 provider catalog
- 补最小后端单测和编译回归
- 收敛前端产品导航、图表卡、聊天工作区和非聊天页工作台壳层

不在本轮内：

- 修改 `agentsdk-go`
- 新增自有 SDK fork
- 改写后端或运行时接口契约

## Execution Steps

### Phase 1: 文档回归

- 更新 `docs/design/2026-03-27-opendataagent-platform-design.md`
- 更新 `docs/plans/2026-03-27-opendataagent-platform-plan.md`
- 删除过期描述：
  - stub runtime
  - Go 1.19 阻塞
  - 后续再接 `agentsdk-go`
  - 自有 fork 计划

### Phase 2: 应用层 ModelFactory

- 新增 `opendataagent/server/internal/agent/model_factory.go`
- 提供以下能力：
  - `DefaultModelFactory()`
  - `CreateModelFactoryFromSettings(...)`
  - `CreateModelFactoryForModelRef(...)`
  - `ResolveSelection(...)`
  - canonical provider catalog
- `ProviderConfig.provider_type`
- `ProviderConfig.base_url` / `ProviderConfig.api_token`
- 默认 provider 设为 `anthropic`
- 默认模型设为 `claude-sonnet-4-5-20250929`

### Phase 3: Settings 持久化与模型页

- 扩展 `opendataagent/server/internal/models/types.go`
- `GET / PUT /api/v1/settings/agent` 返回并保存 provider 级连接配置
- settings 中的 provider 列表支持：
  - 内置 provider 模板归一化
  - 用户新增 provider 实例
  - 每个 provider 独立模型列表
  - 每个模型持久化 `name / enabled`
- 模型页右侧 provider 详情区新增：
  - `Base URL`
  - `API Token`
  - 继续保留 provider 启停
  - 模型列表直接展示在右侧主工作区，支持 `是否启用 / 是否默认` 两列开关
- 模型页左侧新增：
  - `新增供应商`
  - `新增模型`
  - 删除用户新增 provider
  - 删除当前 provider 下的模型
- `mock` provider 不显示 URL / Token 字段

### Phase 4: Runtime 收敛

- 调整 `opendataagent/server/internal/runtime/runtime.go`
- `RunInput` 不再携带 provider/model 构造信息
- runtime 仅接收 `sdkapi.ModelFactory`
- mock runtime 通过显式 `NewMockModelFactory(...)` 注入

### Phase 5: App Wiring 与默认值修正

- 调整 `opendataagent/server/internal/app/app.go`
- 在投递消息时先解析 provider/model selection
- 在任务执行前先构造 `ModelFactory`，再传给 runtime
- 设置读取、更新和默认状态统一经过 settings normalization
- 重写 `opendataagent/server/data/state.json` 为 Anthropic-first 干净初始状态

### Phase 6: Compat Provider

- 新增 `opendataagent/server/internal/agent/compat/`
- 对 `wzw.pp.ua` 暴露 `anthropic_compat` provider
- 兼容逻辑固定为：
  - 首选 OpenAI wire protocol，必要时首轮回退到 Anthropic wire protocol
  - 响应中把 `"<tool_call>...</tool_call>"`、`runtime_context()`、裸工具名、`call_<tool>(...)` 文本翻成结构化 `ToolCall`
  - 二轮优先回放首轮缓存的 final text；没有缓存时退化成“基于 tool output 的文本总结请求”
  - SDK 不做任何修改
  - provider 的 `base_url / api_token` 仍然从 settings 获取，而不是从环境变量获取

### Phase 7: 回归验证

- 后端：
  - `go test ./...`
- 前端：
  - `nvm use && npm --prefix opendataagent/web run build`
- 检查 provider catalog 已切到 Anthropic-first，且 provider 详情页可编辑 `Base URL / API Token`
- 检查页面可新增 provider 实例和模型，并能持久化后重新加载
- 检查 compat provider 仍受 allowlist base URL 约束，但读取来源为 settings
- 用 `wzw.pp.ua + GLM-4.7` 跑一轮真实 tool-calling smoke

### Phase 8: Frontend Design System 收口

- 调整 `opendataagent/web/src/App.vue`
  - 用顶层 product nav 取代旧侧栏卡片导航
  - 显式按钮式路由切换，修复非聊天页点击切换体验
- 新增 `opendataagent/web/src/styles.css`
  - 统一 Tailwind 设计令牌、按钮、输入框和卡片风格
- 新增 `opendataagent/web/src/components/ProductPageShell.vue`
  - 统一 hero / stats / sidebar / insight / main 工作区壳层
- 新增 `opendataagent/web/src/components/MetricTrendChart.vue`
  - 用 ECharts 提供页面级业务分析卡
- 重构以下页面但保持既有 API 逻辑不变：
  - `src/views/chat/AgentChatView.vue`
  - `src/views/market/SkillMarketView.vue`
  - `src/views/skills/SkillAdminView.vue`
  - `src/views/mcps/McpManagerView.vue`
  - `src/views/settings/AgentSettingsView.vue`
- 增加浏览器级 smoke：
  - `/chat -> /skill-market -> /skills -> /mcps -> /settings -> /chat`
  - 验证详情抽屉、编辑区、MCP 新增弹窗、设置页 provider 操作、聊天输入区均可点击

## Touched Files

- `docs/design/2026-03-27-opendataagent-platform-design.md`
- `docs/plans/2026-03-27-opendataagent-platform-plan.md`
- `opendataagent/server/internal/agent/model_factory.go`
- `opendataagent/server/internal/agent/compat/anthropic_text_toolcall.go`
- `opendataagent/server/internal/agent/compat/openai_gateway_toolcall.go`
- `opendataagent/server/internal/agent/compat/anthropic_text_toolcall_test.go`
- `opendataagent/server/internal/agent/model_factory_test.go`
- `opendataagent/server/internal/app/app.go`
- `opendataagent/server/internal/runtime/runtime.go`
- `opendataagent/server/internal/models/types.go`
- `opendataagent/server/data/state.json`
- `opendataagent/web/src/App.vue`
- `opendataagent/web/src/main.js`
- `opendataagent/web/src/styles.css`
- `opendataagent/web/src/components/ProductPageShell.vue`
- `opendataagent/web/src/components/MetricTrendChart.vue`
- `opendataagent/web/src/views/chat/AgentChatView.vue`
- `opendataagent/web/src/views/market/SkillMarketView.vue`
- `opendataagent/web/src/views/skills/SkillAdminView.vue`
- `opendataagent/web/src/views/mcps/McpManagerView.vue`
- `opendataagent/web/src/views/settings/AgentSettingsView.vue`
- `opendataagent/web/vite.config.js`
- `opendataagent/web/package.json`
- `opendataagent/web/index.html`
- `opendataagent/web/public/favicon.svg`
- `opendataagent/server/skills/bundled/opendata-frontend-skill/SKILL.md`

## Acceptance Criteria

- 默认 provider 为 `anthropic`
- 默认模型为 `claude-sonnet-4-5-20250929`
- 应用层可以从 settings 构造标准 `AnthropicProvider` / `OpenAIProvider`
- provider 级 `Base URL / API Token` 可通过模型设置页编辑并持久化到 settings
- 页面可新增受支持类型的 provider 实例
- 页面可给当前 provider 新增和删除模型
- 页面可为当前 provider 直接切换模型启用状态和默认模型
- runtime 构造模型时不再依赖 `ANTHROPIC_*` / `OPENAI_*` 模型环境变量
- `mock` provider 仍可显式选择，但不再是默认值
- `wzw.pp.ua` 在应用层 compat provider 下可以跑通 `GLM-4.7` tool-calling
- 浏览器级 `/chat` E2E 可见 tool 卡片和最终 `smoke-ok`
- `agentsdk-go` 仍保持未修改
- 文档与当前实现边界一致
- 前端技术栈收敛到 `Vue 3 + Tailwind CSS + ECharts + lucide-vue-next`
- `/chat` 与 Skill 市场 / Skill 管理 / MCP / 设置页都进入统一的企业工作台视觉语言
- 顶层导航稳定切换，且导入弹窗、版本区域、MCP 新增弹窗、设置页 provider 操作、聊天输入区都能正常工作
