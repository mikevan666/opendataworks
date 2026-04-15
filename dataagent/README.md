# dataagent

统一后的 DataAgent 目录：

- `dataagent-backend`：Python/FastAPI 服务（原 `nl2sql-service`）
- `.claude/`：DataAgent 运行时配置与 Skills 目录

说明：

- 主应用 `frontend` 已统一承载智能问数页面，入口为 `/intelligent-query`。
- 原 Java `dataagent-backend` 模块已删除。
- `dataagent/.claude/skills/dataagent-nl2sql` 是当前运行时使用的内置通用问数 skill，同时承载方法论文档、静态语义资产，以及 skill-local `scripts/` / `bin/` 运行时入口。
- 该内置 skill 只应保留 OpenDataWorks 平台术语、平台表、数据中台通用问数规则；租户或业务域知识应拆到仓库外或未提交的扩展 skill 中。
- 表元数据、血缘、数据源的动态查询入口放在 skill 的 `references/` 和 `scripts/` 中，不再同步成大块 JSON 快照。
- OpenDataWorks 内部部署下，DataAgent runtime 默认 MCP-first：若当前 run 已注入 `portal-mcp`，模型会优先直接调用 `portal_search_tables` / `portal_get_lineage` / `portal_resolve_datasource` / `portal_export_metadata` / `portal_get_table_ddl` / `portal_query_readonly`。
- `inspect_metadata.py` / `resolve_datasource.py` / `query_opendataworks_metadata.py` / `run_sql.py` 仍保留为非 MCP 智能体或 MCP 未注入场景下的 fallback，它们会通过 skill 自带的 `dataagent/.claude/skills/dataagent-nl2sql/bin/odw-cli` 调用 backend 的 `/api/v1/ai/*` 只读接口，而不是由 skill/runtime 直接访问平台元数据库或业务数据库。
- metadata 检索默认先做全局搜索；只有用户明确给出 database 时才加 database 过滤。
- `resolve_datasource.py` 与 datasource export 只返回 datasource 摘要，不再向 skill/runtime 暴露 host、port、user、password、readonly_* 等连接信息。
- 如果把 `dataagent-nl2sql` skill 复制到其他智能体平台，支持远程 MCP 时优先挂 `portal-mcp`；不支持 MCP 时，再检查 `dataagent/.claude/skills/dataagent-nl2sql/bin/odw-cli` 是否存在并走 fallback。
- `dataagent-backend` 的表结构现在由 Alembic 管理；启动前需对 `SESSION_MYSQL_DATABASE` 执行 `alembic upgrade head`。
