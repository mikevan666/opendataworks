# Opendataagent Platform Design

## Summary

`opendataagent/` 是独立于主门户和 Python DataAgent 的新平台工程，拆分为：

- `opendataagent/web`：Vue 3 + Vite 控制台
- `opendataagent/server`：Go 服务，承载会话、Skill、MCP、设置与本地 Skill 市场

运行时底座已经接入 `agentsdk-go`。本轮设计的目标不是再造一层模型 runtime，也不是扩展 SDK，而是把模型选择收敛成 OpenOcta 风格的应用层 `ModelFactory` 分层，并把每个 provider 的 `Base URL / API Token` 纳入平台 settings 持久化。同时，少数非标准供应商继续隔离为应用层 compat driver。前端控制台则收敛到统一的企业工作台设计系统：顶层产品导航、全页面一致的工作台壳层、Tailwind 令牌、`lucide-vue-next` 图标以及基于 ECharts 的轻量分析卡。

## Current State

- 聊天、Skill、MCP、设置、本地 Skill 市场和 SSE 任务流已经在 `opendataagent/server` 内可运行。
- `agentsdk-go` 已作为正式 runtime 底座使用，负责 agent loop、stream、tool calling、skills、MCP bridge。
- 模型 provider 的连接配置已经进入 `settings.providers[*]`：
  - `provider_type`
  - `base_url`
  - `api_token`
  - `enabled`
- runtime 在构造 `ModelFactory` 时直接读取 settings 中的 provider 配置，不再依赖 `ANTHROPIC_*` 或 `OPENAI_*` 这类模型环境变量。
- 模型设置页不再只是编辑内置 provider，而是要支持：
  - 新增 provider 实例
  - 给当前 provider 增减模型
  - 删除用户新增的 provider
- `opendataagent/web` 已从原始侧栏卡片布局收敛为：
  - 顶部产品导航
  - 统一 `ProductPageShell`
  - `styles.css` 提供的企业级设计令牌
  - `MetricTrendChart.vue` 提供的 ECharts 统计卡
  - Skill 市场 / Skill 管理 / MCP / 设置 / 聊天五页统一的 hero、指标卡、侧栏和主工作区结构
- 项目内前端设计约束改为通过仓库本地 skill `.claude/skills/opendata-frontend-skill/` 维护，用于约束后续页面继续沿着企业级、商务风、可维护的前端设计方向演进；当前固定技术栈为 `Vue 3 + Tailwind CSS + ECharts + lucide-vue-next`。
- 供应商 `wzw.pp.ua` 同时暴露 Anthropic-compatible 与 OpenAI-compatible 接口，但两条协议的 tool calling 语义都不完全标准：
  - Anthropic 口首轮可能返回 `"<tool_call>...</tool_call>"`、`runtime_context()` 或裸工具名
  - OpenAI 口首轮可能返回 `call_runtime_context([])` 这类文本式函数调用，二轮原生 tool-result 协议不稳定
- 该差异不是 SDK 问题，而是供应商协议语义与标准 Anthropic 不一致。

## Problem

当前实现聚焦解决 3 个结构性问题：

1. 模型工厂必须集中在应用层，runtime 不再残留 provider/model 分支。
2. 模型连接配置不能依赖服务进程环境变量，而要能在平台 settings 中查看、编辑和持久化。
3. 特定供应商的非标准 tool-calling 语义需要被隔离，否则会污染标准 provider 主链。

同时，产品层还存在一个缺口：

4. 页面只能编辑“已有 provider 的连接配置”，不能新增供应商实例或补充模型列表，导致真正的多供应商接入仍然要改代码。

前端在本轮收口前也存在 2 个产品层问题：

1. 顶部或侧栏导航与页面信息架构没有收敛，非聊天页像若干散落的表单和表格。
2. 非聊天页缺少统一工作区壳层，导致“能用但不像控制台”，并且导航点击体验不稳定。

## Target Architecture

目标结构固定为：

`App / Settings -> ModelFactory -> agentsdk-go Provider -> Runtime`

其中：

- `app` 层负责读取设置、解析 provider/model、选择 `ModelFactory`
- `runtime` 层只接收已经构造好的 `sdkapi.ModelFactory`
- `agentsdk-go` 继续提供实际 agent 执行能力
- `web` 层采用 OpenOcta 风格信息架构：
  - 顶层导航负责产品路由切换
  - 聊天页保持对话工作区，但视觉上与控制台其他页面统一
  - 所有页面统一使用工作台壳层承载页面头、指标卡、侧栏、图表卡与主内容

## Key Decisions

- 默认工厂回到 Anthropic，默认模型为 `claude-sonnet-4-5-20250929`。
- `mock` 只保留为显式测试或本地调试 provider，不再作为默认 provider。
- 应用层新增 OpenOcta 风格模型工厂模块，职责固定为：
  - 维护 provider catalog
  - 归一化 settings
  - 解析 provider/model 选择
  - 构造 `AnthropicProvider` 或 `OpenAIProvider`
  - 从 `settings.providers[*]` 提供 `Base URL / API Token`
  - 为测试 provider 注入 mock factory
- `settings.providers[*]` 拆成两层含义：
  - `provider_id`：实例 ID，用于页面选择、默认值和任务记录
  - `provider_type`：运行时类型，用于决定实际走 `anthropic` / `openai` / `anthropic_compat` / `mock`
- `AgentSettings` 中每个 provider 的 `base_url / api_token` 由平台持久化并通过模型设置页维护。
- 内置 provider 不再等于“唯一可用 provider”。页面允许基于内置类型新增用户自定义 provider 实例。
- 自定义 provider 的模型列表完全由 settings 持久化；模型项从字符串升级为对象结构：
  - `name`
  - `enabled`
- 模型设置页右侧直接展示当前 provider 的模型列表，并用两列开关维护：
  - `是否启用`
  - `是否默认`
- runtime / model factory 不再读取 `ANTHROPIC_API_KEY`、`ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_BASE_URL`、`OPENAI_API_KEY`、`OPENAI_BASE_URL` 作为主链配置来源。
- runtime 主链不再自己解析 `provider_id / model_name`。
- 前端导航不再依赖原始 `RouterLink` 卡片列表，而是显式按钮式路由切换，减少初始重定向阶段的点击竞争。
- 新增统一页面壳组件 `ProductPageShell.vue`，给 Skill 市场、Skill 管理、MCP 管理和设置页复用，并与聊天页保持同一视觉基线。
- 新增全局样式入口 `web/src/styles.css`，把卡片、按钮、输入框、排版和状态收敛到企业级设计令牌。
- 新增 `web/src/components/MetricTrendChart.vue`，统一用 ECharts 承载页面级业务统计与趋势摘要。
- Skill 市场参考 OpenOcta `skill-library` 的 catalog 结构，拆成：
  - 页面 hero + stats
  - 来源侧栏
  - 已安装区 / 可安装区
- Skill 管理参考 OpenOcta `skills` 的 source grouping 思路，把文档列表改成 source 分组卡片而不是纯表格。
- MCP 管理、设置页和聊天页也收敛成工作台布局，保留原 API 逻辑但统一到目录/卡片/主编辑区模式。
- 本轮明确不扩展 `agentsdk-go`，不新增自有 fork。
- 对 `wzw.pp.ua` 这类“Claude-compatible 但 tool-calling 非标准”的网关，增加应用层 compat provider，而不是修改 SDK。
- compat provider 只在命中已知 allowlist base URL 时暴露，当前 allowlist 为 `wzw.pp.ua`。
- compat provider 内部采用 hybrid 策略：
  - 首选 OpenAI wire protocol
  - OpenAI 首轮失败时回退到 Anthropic wire protocol 拿到第一次 tool call
  - 二轮不依赖供应商原生 tool-result 协议，而是优先回放首轮缓存的 final text；没有缓存时，改成“基于 tool output 的文本总结请求”

## Supported Provider Model

正式支持面固定为：

- `anthropic` 类型
  - `claude-sonnet-4-5-20250929`
  - `claude-opus-4-1`
- `anthropic_compat` 类型
  - `GLM-4.7`
  - `z-ai/glm4.7`
- `openai` 类型
  - `gpt-5.4-mini`
  - `gpt-5.4`
  - `gpt-4.1`
- `mock` 类型
  - `mock-agent-1`
  - `mock-agent-verbose`

页面上允许出现多个同类型 provider 实例，例如：

- `anthropic`
- `anthropic-cn`
- `openai-proxy`

只要它们的 `provider_id` 唯一且 `provider_type` 受支持。

以下边界固定不变：

- 标准 `anthropic` provider 不为 `wzw.pp.ua` 之类网关做语义兼容
- compat 逻辑只存在于应用层，不进入 `agentsdk-go`
- 任何新的兼容供应商都需要显式 allowlist 和独立适配器
- `anthropic`、`openai`、`anthropic_compat` 的连接参数都来自 settings，而不是模型环境变量

## Skill / MCP Boundaries

- Skill 继续按 OpenOcta 的三层模型拆分：
  - 市场：catalog / install
  - 加载：bundled / managed 扫描与覆盖
  - 管理：文档、版本、启停、删除
- MCP 仍由平台管理配置和生命周期，运行时只消费已启用 MCP 配置并注入 `agentsdk-go`。
- 模型工厂调整不改变 Skill 市场、Skill 管理和 MCP 管理的 API 形状。
- compat provider 对运行时仍然只暴露标准 `model.Model`；Skill / MCP / tool executor 不感知供应商差异。
- 文本式工具调用兼容范围固定包括：
  - `"<tool_call>...</tool_call>"`
  - `runtime_context()`
  - `runtime_context`
  - `call_runtime_context([])` 及同类 `call_<tool>(...)`

## Interfaces

对外接口维持现状：

- `GET/POST/PUT/DELETE /api/v1/agent/topics*`
- `POST /api/v1/agent/tasks/deliver-message`
- `GET /api/v1/agent/tasks/{id}/events`
- `GET /api/v1/agent/tasks/{id}/events/stream`
- `GET/PUT /api/v1/settings/agent`
- `GET/PUT /api/v1/skills/documents*`
- `POST /api/v1/skills/runtime/sync`
- `GET /api/v1/skill-market/items`
- `POST /api/v1/skill-market/install`
- `GET/POST/PUT/DELETE /api/v1/mcps/servers*`

内部接口调整为：

- `DefaultModelFactory()`
- `CreateModelFactoryFromSettings(...)`
- `CreateModelFactoryForModelRef(...)`
- `ResolveSelection(...)`
- `anthropic_compat` provider factory
- `ProviderConfig.provider_type`
- `ProviderConfig.base_url`
- `ProviderConfig.api_token`
- `ProviderConfig.models[*].name`
- `ProviderConfig.models[*].enabled`

前端内部壳层接口增加：

- `ProductPageShell.vue`
- `MetricTrendChart.vue`
- `styles.css`
- 顶层按钮式 product nav
- 全页面统一 hero / stats / sidebar / insight / main 布局约定

## Non-Goals

- 不修改 `agentsdk-go` 源码
- 不增加新的 SDK fork
- 不改变当前 Skill / MCP / 会话 API 契约
- 不把 OpenOcta 的 Lit UI 直接搬进当前 Vue 项目；只复用其信息架构和交互组织
- 不支持在页面上新增一种全新的 runtime 协议类型；页面只能新增受支持类型的 provider 实例

## Tradeoffs

- 采用 Anthropic-first 默认值，会让正式平台默认行为更接近 OpenOcta，也能把 `mock` 收敛回测试角色。
- 通过应用层 `ModelFactory` 集中 provider 选择，可以保留对标准 `OpenAIProvider` 的支持，同时避免把供应商细节散落到 runtime。
- 通过 `provider_type + provider_id` 的双层设计，页面可以新增 provider 实例而不用改 runtime 分支；代价是 settings 归一化逻辑会比纯内置 catalog 更复杂。
- 针对 `wzw.pp.ua` 的 compat 方案会引入应用层维护成本，但这个成本被严格限制在单独 provider/adapter 内，不会扩散到 SDK 或标准主链。
- 兼容逻辑里存在少量供应商定制回退策略，但这些策略都被封装在 `internal/agent/compat/` 内，不进入标准 `anthropic` / `openai` provider。
- 统一前端页面壳层会增加一些组件层抽象，但收益是导航、页面头、指标卡和工作区布局不再在四个页面里重复演化，后续扩页面时也更稳定。
