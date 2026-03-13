# 术语索引

先结论：遇到业务术语、别名、口径不清的问题，先看本页；仍不明确时，再下钻到对应资产或追问用户。

## 术语解释资产

### CFC环境名称
- 别名：配置中心环境、cfc env、cfc环境
- 解释：CFC 环境名称指组件依赖的配置中心环境，常见值如 `prod`、`sim`、`oasj`，通常为小写。它与业务环境 `env_name` 以及数据中心名称都不同。
- 易混术语：环境名称、数据中心名称
- 推荐追问：请确认你要过滤的是 CFC 环境，还是业务 `env_name`，还是数据中心名称。
- 相关指标：无
- 相关表：无
- 来源：`assets/term_explanations.json`

### DF快照表
- 别名：df表、快照表、每日全量快照表
- 解释：数仓中若表名体现 `df`，通常表示按 `ds` 存储的每日全量快照表。默认优先查最新 `ds`，只有归因分析、历史回溯或用户明确要求历史区间时才扩大时间范围。
- 易混术语：增量表、趋势分析
- 推荐追问：请确认你要看最新快照，还是要按 `ds` 回看历史区间；如果只是常规问数，默认只查最新 `ds`。
- 相关指标：无
- 相关表：data_table、data_field
- 来源：`assets/term_explanations.json`

### DI增量表
- 别名：di表、增量表、每日增量表
- 解释：数仓中若表名体现 `di`，通常表示按 `ds` 存储的每日增量表。此类表默认需要按时间范围查询，不能直接退化成只查最新 `ds`，也不应无条件扫描全历史。
- 易混术语：DF快照表、趋势分析
- 推荐追问：请提供要查询的时间范围，优先明确 `ds` 的起止日期；如果没有时间范围，先不要直接执行 SQL。
- 相关指标：无
- 相关表：data_table、data_field
- 来源：`assets/term_explanations.json`

### Doris 只读账号
- 别名：只读账号、数据库只读用户
- 解释：doris_database_users 按 cluster_id + database_name 保存数据库级只读账号和读写账号，供查询脚本在运行时路由使用。
- 易混术语：Doris 集群、数据库路由
- 推荐追问：请提供明确的 database_name；若同一数据库在多个集群出现，需要进一步确认 cluster_id。
- 相关指标：发布记录数
- 相关表：doris_cluster、doris_database_users
- 来源：`assets/term_explanations.json`

### Doris 引擎
- 别名：doris、Doris 数据源、Doris 查询引擎
- 解释：Doris 在技能里表示查询引擎类型，不是 SQL 的 schema 名。真正写 SQL 时，应使用 metadata 返回的 `db_name` / schema 作为库名前缀，例如 `<db_name>.<table_name>`。
- 易混术语：database_name、db_name、schema
- 推荐追问：请确认你给的是引擎类型，还是实际数据库 / schema 名；执行 SQL 时两者不能混用。
- 相关指标：无
- 相关表：doris_cluster、doris_database_users、data_table
- 来源：`assets/term_explanations.json`

### 任务依赖
- 别名：上下游任务、任务上下游
- 解释：任务依赖通常结合 workflow_task_relation 的上下游计数，以及 table_task_relation / data_lineage 推导出的读写关系来理解。
- 易混术语：血缘关系、工作流关系
- 推荐追问：请确认你要看的是任务所在工作流、上下游任务数量，还是任务读写了哪些表。
- 相关指标：任务数量、工作流任务数
- 相关表：data_task、workflow_task_relation、table_task_relation
- 来源：`assets/term_explanations.json`

### 工作流发布记录
- 别名：发布记录、工作流发布流水
- 解释：workflow_publish_record 记录平台将某个 workflow 版本发布到目标引擎的动作、状态、操作人和时间。
- 易混术语：工作流状态、发布状态
- 推荐追问：请确认你想看的是历史发布记录，还是 data_workflow 上的当前 publish_status。
- 相关指标：发布记录数、失败发布次数
- 相关表：workflow_publish_record、data_workflow
- 来源：`assets/term_explanations.json`

### 接口名称
- 别名：API名称、服务接口、接口
- 解释：接口名称通常是组件或微服务中的接口。只给接口名时容易重名，最好同时给出组件名称和环境条件。
- 易混术语：组件名称、方法名
- 推荐追问：请确认接口属于哪个组件或微服务，以及所在环境；否则同名接口可能不唯一。
- 相关指标：无
- 相关表：无
- 来源：`assets/term_explanations.json`

### 数据中心名称
- 别名：机房、DC、data center
- 解释：数据中心名称表示部署或所属机房维度，常见值如 `tz`、`simcx`。它不是业务 `env_name`，也不是 CFC 环境名称。
- 易混术语：环境名称、CFC环境名称
- 推荐追问：请确认你要按数据中心过滤，还是按业务环境 `env_name` / CFC 环境过滤。
- 相关指标：无
- 相关表：无
- 来源：`assets/term_explanations.json`

### 数据层级
- 别名：表层级、层级、ODS/DWD/DIM/DWS/ADS
- 解释：数据层级描述表在数仓中的分层位置。OpenDataWorks 当前使用 ODS、DWD、DIM、DWS、ADS 五类层级保存到 data_table.layer。
- 易混术语：业务域、数据域
- 推荐追问：请确认你想看的是 layer 分布，还是 business_domain / data_domain 维度。
- 相关指标：数据表数量
- 相关表：data_table
- 来源：`assets/term_explanations.json`

### 环境名称
- 别名：业务环境、env_name、环境
- 解释：业务语境中的环境名称通常指字段 `env_name`，常见值为大写 `PROD` / `SIM`。这和数据中心名称、CFC 环境名称不是一回事。
- 易混术语：数据中心名称、CFC环境名称
- 推荐追问：请确认你说的环境是业务 `env_name`，还是数据中心名称，还是 CFC 环境名称。
- 相关指标：无
- 相关表：无
- 来源：`assets/term_explanations.json`

### 组件名称
- 别名：服务名称、组件
- 解释：组件名称通常在同一环境中唯一。定位组件时，优先同时给出组件名称和环境，避免跨环境同名误判。
- 易混术语：接口名称、应用名称
- 推荐追问：请提供组件名称，以及它所在的业务环境 / 数据中心 / CFC 环境中的哪一种限定。
- 相关指标：无
- 相关表：无
- 来源：`assets/term_explanations.json`

### 血缘关系
- 别名：上下游血缘、lineage
- 解释：血缘关系描述数据表之间的输入输出依赖，平台表 data_lineage 记录 upstream_table_id 和 downstream_table_id。
- 易混术语：任务依赖、工作流依赖
- 推荐追问：请提供明确的表名；如果同名表可能存在于多个数据库，请一并提供 db_name。
- 相关指标：血缘关系数
- 相关表：data_lineage、data_table
- 来源：`assets/term_explanations.json`

## 业务概念补充

### 任务数量
- 说明：当前平台中满足过滤条件的任务数量。
- 默认映射：`data_task / id / count`
- 来源：`assets/business_concepts.json`

### 发布记录数
- 说明：工作流发布记录总数。
- 默认映射：`workflow_publish_record / id / count`
- 来源：`assets/business_concepts.json`

### 工作流任务数
- 说明：某个工作流下已绑定的任务数量。
- 默认映射：`workflow_task_relation / task_id / count`
- 来源：`assets/business_concepts.json`

### 工作流数量
- 说明：当前平台中满足过滤条件的工作流数量。
- 默认映射：`data_workflow / id / count`
- 来源：`assets/business_concepts.json`

### 数据表数量
- 说明：当前元数据中满足过滤条件的数据表数量。
- 默认映射：`data_table / id / count`
- 来源：`assets/business_concepts.json`

### 血缘关系数
- 说明：表级血缘边数量。
- 默认映射：`data_lineage / id / count`
- 来源：`assets/business_concepts.json`

## 语义映射补充

### 任务数量
- 同义词：调度任务数、任务总数
- 候选表字段：`data_task / id`
- 说明：默认统计 data_task 中未删除的任务记录数。
- 来源：`assets/semantic_mappings.json`

### 发布记录数
- 同义词：发布次数、发布记录数量
- 候选表字段：`workflow_publish_record / id`
- 说明：默认统计 workflow_publish_record 中的发布流水数量。
- 来源：`assets/semantic_mappings.json`

### 失败发布次数
- 同义词：发布失败次数、失败发布数
- 候选表字段：`workflow_publish_record / status`
- 说明：按 workflow_publish_record.status = 'failed' 过滤后计数。
- 来源：`assets/semantic_mappings.json`

### 工作流数量
- 同义词：工作流总数、流程数量
- 候选表字段：`data_workflow / id`
- 说明：默认统计 data_workflow 中的工作流定义数量。
- 来源：`assets/semantic_mappings.json`

### 数据表数量
- 同义词：表数量、表总数、元数据表数量
- 候选表字段：`data_table / id`
- 说明：默认统计 data_table 中未删除的数据表记录数。
- 来源：`assets/semantic_mappings.json`

### 血缘关系数
- 同义词：血缘边数、上下游关系数
- 候选表字段：`data_lineage / id`
- 说明：默认统计 data_lineage 中的表级血缘边数量。
- 来源：`assets/semantic_mappings.json`
