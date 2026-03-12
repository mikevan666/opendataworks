# 场景 Playbooks

先结论：本技能优先覆盖统计、对比、趋势、占比、明细、诊断六类问题。对于 `opendataworks` 平台核心表问题，字段已清楚时可以直接走 MySQL；对于托管业务表问题，再走 metadata -> datasource -> SQL。

## 统计

- 典型问题：当前 active 状态的数据表数量、最近 30 天新增工作流数量
- 先确认：
  - 统计指标
  - 时间范围
  - 是否需要过滤状态
- 推荐顺序：
  1. `21-metric-index.md`
  2. 平台核心表已明确时直接 `run_sql.py`
  3. 托管业务表场景才用 `inspect_metadata.py`
- 默认输出：表格
- 追问条件：
  - 指标口径不清
  - 时间范围不清

## 对比

- 典型问题：各数据层表数量对比、各工作流任务数对比
- 先确认：
  - 对比维度
  - 指标
  - 时间范围是否一致
- 推荐顺序：
  1. `21-metric-index.md`
  2. `20-term-index.md`
  3. 平台核心表已明确时直接 `run_sql.py`
  4. 托管业务表场景才用 `inspect_metadata.py`
  5. `build_chart_spec.py --chart-type bar`
- 默认图表：条形图
- 回退输出：表格

## 趋势分析

- 典型问题：最近 30 天工作流发布次数趋势、最近 14 天新增任务趋势
- 先确认：
  - 指标
  - 时间粒度（日 / 周 / 月）
  - 时间范围
- 推荐顺序：
  1. `21-metric-index.md`
  2. `22-sql-example-index.md`
  3. 平台核心表已明确时直接 `run_sql.py`
  4. 托管业务表场景才用 `inspect_metadata.py`
  5. `build_chart_spec.py --chart-type line`
- 第一条脚本动作：
  - 平台核心表场景：直接执行 `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/run_sql.py" --database opendataworks --engine mysql --sql "SELECT ..."`
  - 托管业务表场景：先 `inspect_metadata.py`
- 选表规则：
  - 平台核心表问题优先直接用已知表结构，不要先兜圈读资产。
  - 托管业务表候选由模型根据字段与 reference 自己判断，不依赖脚本推荐。
  - 若时间字段不唯一，优先使用业务记录时间或 `created_at`，仍不明确就追问。
- 数据源规则：
  - 平台核心表固定走 `opendataworks` MySQL。
  - 托管业务表若已确定 `db_name`，再调用 `resolve_datasource.py`；成功一次后不要重复调用。
- 快路径示例：
  - `最近 30 天工作流发布次数趋势` 命中 `workflow_publish_record` 时，固定按 `21-metric-index.md` -> `22-sql-example-index.md` -> `run_sql.py` -> `build_chart_spec.py --chart-type line` 执行。
  - 默认使用 `workflow_publish_record.created_at` 按天聚合发布记录数；第一次返回口径正确的 `sql_execution` 和 `chart_spec` 后就直接总结，不再重复执行等价 SQL。
- 执行结果规则：
  - `run_sql.py` 返回 `sql_execution` 后就直接基于结果收口。
  - 如果结果为空，直接说明“当前筛选条件下无数据”，不要继续无休止切换口径。
  - `build_chart_spec.py` 成功返回一次 `chart_spec` 后就直接结束本轮。
- 强约束：
  - 完成 `21` 和 `22` 后就进入脚本，不要继续读取原始 JSON。
  - 只要脚本参数已明确，就必须真实执行 Bash；不要停留在 reference 阅读层直接给最终 SQL。
  - 没有实际 Bash 报错时，不要声称“缺少依赖”或“环境异常”。
- 默认图表：折线图
- 回退输出：表格

## 占比

- 典型问题：各工作流发布操作类型占比、各发布状态工作流占比
- 先确认：
  - 分类维度
  - 指标
  - 类别数量是否适合占比图
- 推荐顺序：
  1. `20-term-index.md`
  2. `21-metric-index.md`
  3. 平台核心表已明确时直接 `run_sql.py`
  4. 托管业务表场景才用 `inspect_metadata.py`
  5. `build_chart_spec.py --chart-type pie`
- 默认图表：饼图
- 回退条件：
  - 类别超过 8 个
  - 更适合条形图

## 明细

- 典型问题：最近工作流发布记录、某个数据库下的数据表清单
- 先确认：
  - 明细对象
  - 过滤条件
  - 需要哪些字段
- 推荐顺序：
  1. `20-term-index.md`
  2. `30-tool-recipes.md`
  3. 平台核心表已明确时直接 `run_sql.py`
  4. 托管业务表场景才用 `inspect_metadata.py`
- 默认输出：表格
- 约束：
  - 必须带 LIMIT
  - 不要强行出图

## 诊断

- 典型问题：某张表有哪些上游下游血缘、某个数据库路由到哪个 Doris 集群
- 先确认：
  - 目标表或目标数据库
  - 是否需要补充 db_name
  - 是否要看表级血缘还是任务级关系
- 推荐顺序：
  1. `20-term-index.md`
  2. `40-runtime-metadata.md`
  3. 平台核心表已明确时直接 `run_sql.py`
  4. 托管业务表场景才用 `inspect_metadata.py`
  5. 必要时 `resolve_datasource.py`
- 默认输出：表格 + 诊断结论
- 强约束：
  - 用户已给出具体表名时，不要在仓库代码、测试文件或参考文档中搜索 lineage/血缘实现。
  - 直接执行 `data_lineage + data_table` 的查询脚本；只有表名不唯一时才追问。

## 术语解释

- 典型问题：什么是数据层级、什么是工作流发布记录
- 推荐顺序：
  1. `20-term-index.md`
  2. 必要时回看 `assets/term_explanations.json`
- 通常不执行 SQL

## SQL 示例

- 典型问题：给我一个工作流发布趋势 SQL、血缘定位 SQL 怎么写
- 推荐顺序：
  1. `22-sql-example-index.md`
  2. 必要时回看 `assets/sql_examples.json`
- 输出要求：
  - 标明适用场景和引擎
  - 明确“示例仅用于参考，落地前需按真实库表校正”
