# OpenDataWorks 与 Opendataagent 并行共存设计

## Summary

本轮设计目标不是退役现有智能问数，而是在同一仓库内维持两条独立、可长期并行的智能体产品线：

- 主前端中的现有智能问数模块继续保留，维持生产可用状态
- `opendataagent/` 作为独立的 Go SDK 路线 agent 平台继续演进

两者不互相替换，不通过主前端增加互跳入口，也不把任何一方硬塞进另一方的运行链路。

同时，OpenDataWorks 平台能力为 `opendataagent` 新增一套共享 skill 源码与 CLI 接入方式：

- 根目录 `skills/` 作为唯一共享 skill 源码目录
- 平台类 skill 统一通过 `odw-cli` 调 Java agent API
- `opendataagent` 保留通用 MCP 产品能力，但 OpenDataWorks 平台 skill 不依赖 MCP

## Current State

- 主前端仍有现成的智能问数页面与配置管理页，背后是 `dataagent/dataagent-backend`
- 该链路当前处于生产可用状态，不能按“冻结待删”的思路处理
- `opendataagent/` 已是独立的 Go + Vue agent 平台，具备会话、Skill、MCP、模型配置与运行时
- OpenDataWorks 平台能力目前分散在 Java `backend-agent-api`、旧 DataAgent skill、`portal-mcp` 等多条路径
- 仓库内缺少一个统一的“共享平台 skill 源码目录 + CLI 入口”来服务 `opendataagent`

## Problem

当前真正需要解决的问题是：

1. 让 `opendataagent` 拥有一套稳定、可复用的 OpenDataWorks 平台 skill 能力来源
2. 在不影响现有智能问数生产链路的前提下，引入新的 Go SDK 路线
3. 明确两条产品线的边界，避免出现“门户要不要切换到 opendataagent”的反复
4. 把平台检索能力与 SQL 执行能力在 skill 层完成清晰拆分

## Goals

- 主前端继续保留原智能问数入口、路由、菜单、配置页和 skill 管理页
- `opendataagent` 保持独立项目定位，不通过主前端菜单跳转
- 根目录新增 `skills/`，作为共享 skill 源码目录
- OpenDataWorks 平台能力统一通过 `odw-cli` 提供给 `opendataagent`
- 平台 skill 和 SQL skill 拆开
- `workflow-context` 不进入这轮平台能力范围

## Non-Goals

- 不退役 `dataagent/dataagent-backend`
- 不下线主前端智能问数入口
- 不要求主前端和 `opendataagent` 互相跳转
- 不把 OpenDataWorks 平台能力迁移到 MCP 主链
- 不把业务分析逻辑塞进平台 skill

## Product Boundary

### 现有智能问数

- 产品位置：主前端内嵌模块
- 技术路线：现有 Python DataAgent / Claude Agent SDK
- 目标：继续承载当前生产智能问数能力
- 生命周期：长期并行存在，不按短期退役处理

### Opendataagent

- 产品位置：独立项目 `opendataagent/`
- 技术路线：Go runtime / `agentsdk-go`
- 目标：通用 agent 平台，支持 Skill、MCP、Python 分析、图表等能力
- 生命周期：独立演进，不要求替代现有智能问数

## Shared Skill Architecture

根目录 `skills/` 作为唯一共享 skill 源码目录，固定为：

- `skills/platform/opendataworks-platform/`
- `skills/platform/opendataworks-readonly-sql/`
- `skills/generic/python-analysis/`
- `skills/generic/chart-visualization/`

其中：

- `OpenDataWorks Platform Skill`
  - metadata inspect
  - lineage
  - datasource resolve
  - DDL lookup
  - 不包含 `workflow-context`
  - 不执行 SQL
- `OpenDataWorks Readonly SQL Skill`
  - 单独承载只读 SQL
  - 底层统一走 `odw-cli read-query`
- `Python Analysis Skill`
  - 提供 Python 数据分析能力
- `Chart Visualization Skill`
  - 提供图表能力
  - 计划基于 AntV chart-visualization skill 体系整理接入

## CLI Boundary

`odw-cli` 是 OpenDataWorks 平台能力给 `opendataagent` 的唯一脚本入口，覆盖：

- `inspect`
- `lineage`
- `resolve-datasource`
- `export`
- `ddl`
- `read-query`

本轮明确不提供：

- `workflow-context`

也不增加对应 Java agent API。

## SQL Boundary

`OpenDataWorks Readonly SQL Skill` 的边界由 CLI/API 保证：

- 允许查询 `opendataworks` 平台库
- 允许查询通过 metadata resolve 映射到的业务库
- 默认结果上限 `200`
- 默认超时 `30s`
- 只读校验、库范围、错误语义统一收敛在 `odw-cli + backend-agent-api`

## Opendataagent Loading Model

- `opendataagent` 在构建或启动时把根 `skills/` 镜像到自己的 bundled skills 目录
- shared skills 视为只读源码来源
- `opendataagent` 的 managed skills 继续存在，但只用于额外安装和覆盖
- 共享平台 skill 不回写主前端旧 DataAgent 的 skill 目录

## MCP Boundary

- `opendataagent` 继续保留通用 MCP 管理与挂载能力
- OpenDataWorks 平台 skill 不依赖 MCP
- `portal-mcp` 可以继续存在，但不作为这轮共享 skill 主链

## Tradeoffs

- 保留主前端智能问数会增加长期维护成本，但这是生产稳定性的必要代价
- `opendataagent` 与现有智能问数并行，会出现两套 agent 产品，但边界清晰后比“强行统一”风险更低
- 共享 `skills/` 能提高平台能力复用率，但要求 skill 设计严格区分“共享平台能力”和“旧 DataAgent 专用能力”
- 不引入 `workflow-context` 会少一个专用平台接口，但也避免为了未确认需求扩出长期维护面

## Affected Areas

- `frontend/`
- `dataagent/`
- `opendataagent/`
- `backend-agent-api/`
- `skills/`
- `deploy/`
