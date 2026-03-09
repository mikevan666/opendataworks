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

### 趋势分析
- 同义词：走势、变化趋势
- 规则：未指定时间粒度时默认按天，优先使用 created_at 或业务记录时间字段；时间跨度较长时可建议按周或按月汇总。
- 来源：`assets/business_rules.json`
