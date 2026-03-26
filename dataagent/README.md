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
- `inspect_metadata.py` / `resolve_datasource.py` / `query_opendataworks_metadata.py` 会优先通过 skill 自带的 `dataagent/.claude/skills/dataagent-nl2sql/bin/odw-cli` 调用 backend 的 `/api/v1/ai/metadata/*` 只读接口，而不是直接访问平台元数据库。
- 如果把 `dataagent-nl2sql` skill 复制到其他智能体平台，运行前应先检查 `dataagent/.claude/skills/dataagent-nl2sql/bin/odw-cli` 是否存在；若不存在，需由用户先自行安装到该固定路径。
- `dataagent-backend` 的表结构现在由 Alembic 管理；启动前需对 `SESSION_MYSQL_DATABASE` 执行 `alembic upgrade head`。
