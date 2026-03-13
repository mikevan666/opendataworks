# 指标索引

先结论：遇到统计、对比、趋势分析，先用本页确认指标公式、默认时间字段和关键口径约束。

## 全局约束

- 最大行数保护：1000
- 时区：Asia/Shanghai
- 禁止操作：drop、truncate、delete、alter、create、insert、update
- 来源：`assets/constraints.json`

## 指标清单

### 任务数量
- Metric Key：`task_cnt`
- 公式：`COUNT(data_task.id)`
- 默认时间字段：`created_at`
- 来源：`assets/metrics.json`

### 发布记录数
- Metric Key：`publish_record_cnt`
- 公式：`COUNT(workflow_publish_record.id)`
- 默认时间字段：`created_at`
- 来源：`assets/metrics.json`

### 失败发布次数
- Metric Key：`failed_publish_cnt`
- 公式：`SUM(CASE WHEN workflow_publish_record.status = 'failed' THEN 1 ELSE 0 END)`
- 默认时间字段：`created_at`
- 来源：`assets/metrics.json`

### 工作流数量
- Metric Key：`workflow_cnt`
- 公式：`COUNT(data_workflow.id)`
- 默认时间字段：`created_at`
- 来源：`assets/metrics.json`

### 数据表数量
- Metric Key：`table_cnt`
- 公式：`COUNT(data_table.id)`
- 默认时间字段：`created_at`
- 来源：`assets/metrics.json`

### 血缘关系数
- Metric Key：`lineage_edge_cnt`
- 公式：`COUNT(data_lineage.id)`
- 默认时间字段：`created_at`
- 来源：`assets/metrics.json`

## 业务规则补充

### Doris 增量表
- 同义词：di表、增量表、每日增量
- 规则：Doris 数仓表若命名体现 `di` 增量含义，默认按每日增量表理解；日期字段通常为 `ds`，这类表必须按时间范围查询，若用户未给范围应先追问。
- 来源：`assets/business_rules.json`

### Doris 快照表
- 同义词：df表、快照表、每日全量快照
- 规则：Doris 数仓表若命名体现 `df` 快照含义，默认按每日全量快照理解；日期字段通常为 `ds`，除非用户明确要求历史回溯、趋势或归因分析，否则默认只查最新 `ds`。
- 来源：`assets/business_rules.json`

### SQL Schema 限定
- 同义词：schema、库名前缀、database 前缀
- 规则：目标数据库一旦明确，SQL 中必须写成 `<schema>.<table>`；平台核心表固定使用 `opendataworks.<table>`，不要省略 schema，也不要把 `mysql` / `doris` 误当成 schema。
- 来源：`assets/business_rules.json`

### 上下游血缘
- 同义词：血缘关系、上游下游
- 规则：查询血缘时必须明确目标表名；若同名表可能存在于多个数据库，必须先补充 db_name 再执行。
- 来源：`assets/business_rules.json`

### 对比分析
- 同义词：横向对比、分组对比
- 规则：默认要求所有分组使用相同时间范围、相同过滤条件和相同统计口径。
- 来源：`assets/business_rules.json`

### 工作流发布状态
- 同义词：发布结果、发布状态
- 规则：历史发布结果以 workflow_publish_record.status 为准；平台当前态以 data_workflow.publish_status 为准，两者不能混用。
- 来源：`assets/business_rules.json`

### 数据层级
- 同义词：层级、表层级、ODS/DWD/DIM/DWS/ADS
- 规则：涉及层级分布或层级对比时，默认使用 data_table.layer，并排除 deleted=1 的记录；若用户强调“有效表”，再额外过滤 status='active'。
- 来源：`assets/business_rules.json`

### 环境名称
- 同义词：环境、业务环境、env
- 规则：业务语境中的“环境名称”默认优先映射字段 `env_name`，常见值为大写 `PROD` / `SIM`；必须与数据中心名称（如 `tz`、`simcx`）和 CFC 环境名称（如 `prod`、`sim`、`oasj`）区分。
- 来源：`assets/business_rules.json`

### 趋势分析
- 同义词：走势、变化趋势
- 规则：未指定时间粒度时默认按天，优先使用 created_at 或业务记录时间字段；时间跨度较长时可建议按周或按月汇总。
- 来源：`assets/business_rules.json`
