# NL2SQL Backend CLI Design

## Background

智能问数当前静态业务知识已经沉到 skill 资产，但动态 metadata、lineage、datasource 解析仍然由 skill 脚本直接访问 `opendataworks` MySQL。这样会把平台元数据结构、权限边界和 DataAgent 运行时耦合在一起，也不符合本次“DataAgent 保留 session/run/worker，只把元数据侧能力后移”的改造目标。

## Scope

本次只覆盖三类动态能力：

- metadata inspect
- lineage inspect/export
- datasource resolve

不在本次范围内：

- DataAgent 会话、run、worker 架构
- 静态业务知识资产
- SQL 执行主链路后移到 backend

## Solution

### Backend Agent API Module

- 新增顶层 Maven 模块 `backend-agent-api/`
- 模块内只放 agent 专用 controller、DTO、SPI、service-token 鉴权配置
- 现有 `backend/` 模块依赖该 jar，并在同一 Spring Boot 进程内提供 SPI 实现

### Runtime Path

运行时链路调整为：

1. skill 继续调用 `inspect_metadata.py` / `resolve_datasource.py` / `query_opendataworks_metadata.py`
2. 这些脚本内部固定优先调用 skill 自带 `bin/odw-cli`
3. `odw-cli` 通过 `curl` 请求 backend `/api/v1/ai/metadata/*`
4. backend 复用现有 metadata / lineage / doris cluster 数据，返回与原脚本兼容的 JSON 结构

为保证 skill 可移植到其他智能体平台，运行时只认固定路径 `${DATAAGENT_SKILL_ROOT}/bin/odw-cli`。执行 metadata 相关脚本前必须先检查该路径；如果缺失，直接停止并提示用户先自行安装到这个路径。

### API Contract

- `GET /api/v1/ai/metadata/inspect`
- `GET /api/v1/ai/metadata/lineage`
- `GET /api/v1/ai/metadata/datasource/resolve`
- `GET /api/v1/ai/metadata/export`

返回 JSON 维持现有脚本的 snake_case 输出字段，避免 skill 提示词和下游工具结果契约抖动。

### Auth Boundary

- agent API 不复用用户态 `@RequireAuth`
- 新增 `X-Agent-Service-Token`
- 默认要求私网来源
- DataAgent 与 backend 通过同一 Compose 内网访问

## Tradeoffs

- 采用 shell CLI 而不是 JVM CLI，能避免把额外 Java 运行时带进 DataAgent 镜像，但 CLI 只适合作为 HTTP 封装层，真正的权限和数据边界仍然在 backend
- 固定只认 skill 内 CLI 路径，规则更简单，但要求迁移 skill 时必须保证该固定路径事先安装完成
- 不再保留旧的直查库兼容路径，运行时只有一条 metadata 获取链路：skill CLI -> backend agent API
- `run_sql.py` 仍本地执行，意味着 DataAgent 还需要访问真实查询目标库；本次只解决 metadata 直查库问题
