# 运行时元数据与数据源说明

先结论：只有在 `SKILL.md + 00 + 10 + 11 + 20/21/22` 仍然不能消除具体疑问时，才需要阅读本页或执行脚本。

## 何时需要本页

- 需要确认平台核心表的关键字段
- 需要确认上下游血缘或任务关系
- 需要确认目标数据库落在 MySQL 还是 Doris
- 需要解释为什么平台核心表可直接走 MySQL，而托管业务表必须先 metadata 再 datasource 再 SQL

## 推荐脚本入口

- [`scripts/inspect_metadata.py`](../scripts/inspect_metadata.py)
- [`scripts/resolve_datasource.py`](../scripts/resolve_datasource.py)
- [`scripts/query_opendataworks_metadata.py`](../scripts/query_opendataworks_metadata.py)

## 使用原则

- 数据源账号密码只在脚本内部使用，不要回写到最终回答。
- 实际执行时只使用 `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/<name>.py" ...`，不要自己拼 `/app/scripts/...` 或 `scripts/<name>.py`。
- 默认运行时下，`inspect_metadata.py`、`resolve_datasource.py`、`query_opendataworks_metadata.py` 会优先通过 skill 自带 `${DATAAGENT_SKILL_ROOT}/bin/odw-cli` 调 backend agent API 获取动态 metadata。
- 执行 metadata 相关脚本前，先检查 `${DATAAGENT_SKILL_ROOT}/bin/odw-cli` 是否存在。
- 部署时如果 bind mount 丢了执行位，运行时会自动退回 `sh "${DATAAGENT_SKILL_ROOT}/bin/odw-cli" ...`；但宿主机仍建议保留 `+x`。
- 如果该固定路径缺少 CLI，必须先由用户自行安装到 `${DATAAGENT_SKILL_ROOT}/bin/odw-cli`，然后再执行 metadata 相关脚本。
- `inspect_metadata.py` 只返回托管业务表命中的客观候选，不负责判断“哪张表最好”。
- 平台核心表结构已在本页给出，字段明确时可直接写 SQL。
- `resolve_datasource.py` 只负责确认引擎与数据源元信息。
- `run_sql.py` 会在执行前再次解析数据源，因此不要把 datasource 结果当成最终凭证输出。
- 一旦数据库明确，SQL 必须写 `<schema>.<table>`；平台核心表固定用 `opendataworks.<table>`。

## 平台核心表速查

### 数据表与字段

- `data_table`
  - `id`, `db_name`, `table_name`, `table_comment`, `layer`, `status`, `owner`, `created_at`
- `data_field`
  - `table_id`, `field_name`, `field_type`, `field_comment`, `is_partition`, `is_primary`, `field_order`

### 血缘与任务关系

- `data_lineage`
  - `task_id`, `upstream_table_id`, `downstream_table_id`, `lineage_type`, `created_at`
- `table_task_relation`
  - `task_id`, `table_id`, `relation_type`, `created_at`
- `data_task`
  - `task_name`, `task_code`, `task_type`, `engine`, `status`, `owner`, `datasource_name`, `datasource_type`, `created_at`

### 工作流治理

- `data_workflow`
  - `workflow_code`, `workflow_name`, `status`, `publish_status`, `current_version_id`, `last_published_version_id`, `created_at`
- `workflow_task_relation`
  - `workflow_id`, `task_id`, `upstream_task_count`, `downstream_task_count`, `version_id`, `created_at`
- `workflow_version`
  - `workflow_id`, `version_no`, `change_summary`, `trigger_source`, `created_at`
- `workflow_publish_record`
  - `workflow_id`, `version_id`, `target_engine`, `operation`, `status`, `engine_workflow_code`, `operator`, `created_at`

### Doris 数据源

- `doris_cluster`
  - `cluster_name`, `fe_host`, `fe_port`, `username`, `is_default`, `status`
- `doris_database_users`
  - `cluster_id`, `database_name`, `readonly_username`, `readwrite_username`, `created_at`

## Backend CLI 环境变量

- `ODW_BACKEND_BASE_URL=http://backend:8080/api/v1/ai/metadata`
- `ODW_AGENT_SERVICE_TOKEN=<shared-token>`
- `ODW_BACKEND_TIMEOUT_SECONDS=30`

## 原始查询示例

### 各数据层表数量对比

```sql
SELECT layer, COUNT(*) AS table_cnt
FROM opendataworks.data_table
WHERE deleted = 0
GROUP BY layer
ORDER BY table_cnt DESC
LIMIT 20;
```

### 最近 30 天工作流发布次数趋势

```sql
SELECT DATE(created_at) AS stat_day, COUNT(*) AS publish_cnt
FROM opendataworks.workflow_publish_record
WHERE created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 29 DAY)
GROUP BY DATE(created_at)
ORDER BY stat_day
LIMIT 100;
```

### 某张表的上下游血缘

```sql
SELECT dl.lineage_type,
       ut.db_name AS upstream_db,
       ut.table_name AS upstream_table,
       dt.db_name AS downstream_db,
       dt.table_name AS downstream_table
FROM opendataworks.data_lineage dl
LEFT JOIN opendataworks.data_table ut ON ut.id = dl.upstream_table_id AND ut.deleted = 0
LEFT JOIN opendataworks.data_table dt ON dt.id = dl.downstream_table_id AND dt.deleted = 0
WHERE (ut.table_name = 'your_table' OR dt.table_name = 'your_table')
ORDER BY dl.id DESC
LIMIT 100;
```

诊断类硬规则：

- 用户已经给出明确表名时，直接执行这条 SQL 模板或等价脚本，不要搜索仓库里的 lineage/血缘代码实现。
- 如果是 `dwd_order` 这类具体表名，优先直接把表名填入 SQL，再执行 `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/run_sql.py" --database opendataworks --engine mysql --sql "<SQL>"`。
- 只要第一次血缘 SQL 已返回非空结果，就直接总结；即使 `downstream_table` 或 `upstream_table` 有空值，也不要因为补空列再继续追加第二条 SQL。
- 只有同名表不唯一或用户没给出表名时，才退回 metadata 检索和追问。

### 某个业务数据库对应的 Doris 只读账号

```sql
SELECT du.database_name,
       du.readonly_username,
       dc.cluster_name,
       dc.fe_host,
       dc.fe_port
FROM opendataworks.doris_database_users du
INNER JOIN opendataworks.doris_cluster dc ON dc.id = du.cluster_id
WHERE du.database_name = 'your_database'
LIMIT 20;
```
