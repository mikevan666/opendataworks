# SQL 示例索引

先结论：需要 SQL 参考时，先看本页匹配场景和引擎；示例只用于校准结构，不要直接照抄到最终回答。

## SQL 示例

### 各工作流发布操作类型占比
- 场景：占比分析
- 引擎：`mysql`
- 问题：各工作流发布操作类型占比
- SQL 摘要：`SELECT operation, COUNT(*) AS publish_cnt`
- 注意事项：如果操作类型类别超过 8 个，应回退为条形图或表格。、平台核心表 SQL 也要保留 schema 前缀。、若用户只关心最近一段时间，可追加 created_at 时间过滤。
- 相关术语：工作流发布记录、操作类型
- 来源：`assets/sql_examples.json`

### 各数据层表数量对比
- 场景：对比分析
- 引擎：`mysql`
- 问题：各数据层表数量对比
- SQL 摘要：`SELECT layer, COUNT(*) AS table_cnt`
- 注意事项：若用户强调有效表，可追加 status='active'。、平台核心表 SQL 也要保留 schema 前缀。、layer 是对比维度，默认输出条形图。
- 相关术语：数据层级、数据表数量
- 来源：`assets/sql_examples.json`

### 工作流发布记录明细
- 场景：明细查询
- 引擎：`mysql`
- 问题：最近工作流发布记录
- SQL 摘要：`SELECT workflow_id, version_id, target_engine, operation, status, operator, created_at`
- 注意事项：明细查询必须带 LIMIT。、平台核心表 SQL 也要保留 schema 前缀。、如果用户只关心失败记录，可追加 status='failed' 过滤。
- 相关术语：工作流发布记录、发布记录数
- 来源：`assets/sql_examples.json`

### 按时间范围查询 di 增量明细
- 场景：明细查询
- 引擎：`doris`
- 问题：查询某张 di 增量表在指定时间范围内的明细
- SQL 摘要：`SELECT *`
- 注意事项：Doris `di` 表默认按每日增量表理解，必须带时间范围过滤。、日期字段通常优先使用 `ds`。、真正落地时应结合 metadata 把 `SELECT *` 缩成最小必要字段。
- 相关术语：DI增量表、SQL Schema 限定
- 来源：`assets/sql_examples.json`

### 按最新 ds 查询 df 快照表明细
- 场景：明细查询
- 引擎：`doris`
- 问题：查询某张 df 快照表最新一天的明细
- SQL 摘要：`SELECT *`
- 注意事项：Doris `df` 表默认按每日全量快照理解，常规问数优先只查最新 `ds`。、真正落地时应结合 metadata 把 `SELECT *` 缩成最小必要字段。、如果用户明确要求历史区间，再改成按 `ds` 过滤区间。
- 相关术语：DF快照表、SQL Schema 限定
- 来源：`assets/sql_examples.json`

### 某张表上下游血缘定位
- 场景：诊断
- 引擎：`mysql`
- 问题：查看某张表的上下游血缘
- SQL 摘要：`SELECT dl.lineage_type,`
- 注意事项：把 `your_table` 替换成用户给出的真实表名即可。、平台核心表 SQL 也要保留 schema 前缀。、血缘定位默认输出表格，不强制出图。
- 相关术语：血缘关系、上下游血缘
- 来源：`assets/sql_examples.json`

### 工作流发布次数趋势
- 场景：趋势分析
- 引擎：`mysql`
- 问题：最近 30 天工作流发布次数趋势
- SQL 摘要：`SELECT DATE(created_at) AS stat_day, COUNT(*) AS publish_cnt`
- 注意事项：默认按 created_at 做按天趋势。、平台核心表 SQL 也要保留 schema 前缀。、如果用户要求只看失败发布，需要额外加 status='failed' 过滤。
- 相关术语：工作流发布记录、趋势分析
- 来源：`assets/sql_examples.json`

## Few-shot 提示补充

### 最近 30 天工作流发布次数趋势
- 标签：趋势分析、折线图、工作流发布
- 答案摘要：使用 workflow_publish_record 的 created_at 作为时间字段，按天聚合发布记录数，默认输出折线图，并保留表格结果作为核对依据。
- 来源：`assets/few_shots.json`

### 各数据层表数量对比
- 标签：对比分析、条形图、数据表数量
- 答案摘要：使用 data_table.layer 作为对比维度、COUNT(id) 作为指标，默认过滤 deleted=0；如果用户强调有效表，再补 status='active' 过滤，并输出条形图。
- 来源：`assets/few_shots.json`

### 各工作流发布操作类型占比
- 标签：占比分析、饼图、工作流发布
- 答案摘要：使用 workflow_publish_record.operation 作为分类维度、COUNT(id) 作为指标；类别较少时输出饼图，否则回退为条形图或表格。
- 来源：`assets/few_shots.json`

### 查看某张表的上下游血缘
- 标签：诊断、血缘关系、表格
- 答案摘要：已给出明确表名时，直接在 opendataworks 的 data_lineage 与 data_table 上执行血缘 SQL；若同名表可能存在于多个数据库，再补充 db_name，不要搜索仓库代码或文档实现。
- 来源：`assets/few_shots.json`

### 查询某张 df 快照表最新一天的明细
- 标签：明细查询、Doris、快照表、ds
- 答案摘要：先确认目标表的 `db_name` 和表名；若命中 Doris `df` 快照表，默认用 `<db_name>.<table>` 并按 `MAX(ds)` 过滤最新分区。若用户明确要求历史区间，再改成按 `ds` 查询历史。
- 来源：`assets/few_shots.json`

### 查询某张 di 增量表在指定时间范围内的明细
- 标签：明细查询、Doris、增量表、时间范围
- 答案摘要：若命中 Doris `di` 增量表，必须按时间范围查询，优先使用 `ds BETWEEN 起始日期 AND 结束日期`；如果用户没给时间范围，先追问，不要退化成只查最新 `ds`。
- 来源：`assets/few_shots.json`
