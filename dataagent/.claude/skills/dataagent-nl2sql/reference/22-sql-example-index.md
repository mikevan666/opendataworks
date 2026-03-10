# SQL 示例索引

先结论：需要 SQL 参考时，先看本页匹配场景和引擎；示例只用于校准结构，不要直接照抄到最终回答。

## SQL 示例

### 各工作流发布操作类型占比
- 场景：占比分析
- 引擎：`mysql`
- 问题：各工作流发布操作类型占比
- SQL 摘要：`SELECT operation, COUNT(*) AS publish_cnt`
- 注意事项：如果操作类型类别超过 8 个，应回退为条形图或表格。、若用户只关心最近一段时间，可追加 created_at 时间过滤。
- 相关术语：工作流发布记录、操作类型
- 来源：`assets/sql_examples.json`

### 各数据层表数量对比
- 场景：对比分析
- 引擎：`mysql`
- 问题：各数据层表数量对比
- SQL 摘要：`SELECT layer, COUNT(*) AS table_cnt`
- 注意事项：若用户强调有效表，可追加 status='active'。、layer 是对比维度，默认输出条形图。
- 相关术语：数据层级、数据表数量
- 来源：`assets/sql_examples.json`

### 工作流发布记录明细
- 场景：明细查询
- 引擎：`mysql`
- 问题：最近工作流发布记录
- SQL 摘要：`SELECT workflow_id, version_id, target_engine, operation, status, operator, created_at`
- 注意事项：明细查询必须带 LIMIT。、如果用户只关心失败记录，可追加 status='failed' 过滤。
- 相关术语：工作流发布记录、发布记录数
- 来源：`assets/sql_examples.json`

### dwd_tech_dev_inspection_rule_cnt_di 上下游血缘定位
- 场景：诊断
- 引擎：`mysql`
- 问题：查看 dwd_tech_dev_inspection_rule_cnt_di 的上下游血缘
- SQL 摘要：`SELECT dl.lineage_type,`
- 注意事项：如果用户换成其他表名，按同样模板替换表名即可。、血缘定位默认输出表格，不强制出图。
- 相关术语：血缘关系、上下游血缘
- 来源：`assets/sql_examples.json`

### 工作流发布次数趋势
- 场景：趋势分析
- 引擎：`mysql`
- 问题：最近 30 天工作流发布次数趋势
- SQL 摘要：`SELECT DATE(created_at) AS stat_day, COUNT(*) AS publish_cnt`
- 注意事项：默认按 created_at 做按天趋势。、如果用户要求只看失败发布，需要额外加 status='failed' 过滤。
- 相关术语：工作流发布记录、趋势分析
- 来源：`assets/sql_examples.json`

## Few-shot 提示补充

### 最近 30 天工作流发布次数趋势
- 标签：趋势分析、折线图、工作流发布
- 答案摘要：先按趋势分析处理。确认使用 workflow_publish_record 的 created_at 作为时间字段，按天聚合发布记录数，默认输出折线图，并保留表格结果作为核对依据。
- 来源：`assets/few_shots.json`

### 各数据层表数量对比
- 标签：对比分析、条形图、数据表数量
- 答案摘要：先按对比分析处理。使用 data_table.layer 作为对比维度、COUNT(id) 作为指标，默认过滤 deleted=0；如果用户强调有效表，再补 status='active' 过滤，并输出条形图。
- 来源：`assets/few_shots.json`

### 各工作流发布操作类型占比
- 标签：占比分析、饼图、工作流发布
- 答案摘要：先按占比分析处理。使用 workflow_publish_record.operation 作为分类维度、COUNT(id) 作为指标；类别较少时输出饼图，否则回退为条形图或表格。
- 来源：`assets/few_shots.json`

### 查看 dwd_tech_dev_inspection_rule_cnt_di 的上下游血缘
- 标签：诊断、血缘关系、表格
- 答案摘要：先按诊断处理。已给出明确表名，直接在 opendataworks 的 data_lineage 与 data_table 上执行血缘 SQL，不要搜索仓库代码或文档实现，默认输出表格和简短诊断结论。
- 来源：`assets/few_shots.json`
