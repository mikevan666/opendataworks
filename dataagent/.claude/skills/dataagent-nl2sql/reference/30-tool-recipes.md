# 工具 Recipes

先结论：脚本调用必须按“先澄清、再定位、后执行”的顺序进行。`run_sql.py` 不是盲猜工具；但如果问题已经明确指向 `opendataworks` 平台核心表且字段清楚，可以直接执行。

## 统一命令规则

- 所有命令都直接执行 skill 包内脚本：`"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/<name>.py" ...`
- 固定脚本只有：`inspect_metadata.py`、`resolve_datasource.py`、`run_sql.py`、`build_chart_spec.py`、`format_answer.py`、`query_opendataworks_metadata.py`
- 不要自己拼脚本路径或脚本名；禁止使用 `/app/scripts/...`、`scripts/<name>.py`、`resolvedadatsource.py` 这类猜测路径或拼写。
- 不要执行 `pip install`、`uv add`、`which python`、`python --version` 这类环境探测或依赖安装命令。
- 如果脚本报错，优先收敛输入参数或向用户追问，不要切换解释器反复试探。
- 没有真实 Bash 报错时，不要自行下结论说“缺少依赖”或“环境异常”。
- 统计 / 对比 / 趋势 / 占比 / 明细 / 诊断问题，不要用读取 `assets/*.json` 代替脚本执行；`assets` 只用于术语解释或 SQL 示例补充。

## inspect_metadata.py

- 用途：定位托管业务表的数据库、表、字段、血缘
- 返回原则：
  - 只返回匹配到的客观候选，不做推荐、打分或排序
  - 由模型根据场景、字段和 reference 规则自己决定用哪张表
- 适用场景：
  - 用户没有给出明确表名
  - 需要确认托管业务表中的指标字段和维度字段
  - 需要判断候选数据库
- 不适用场景：
  - 问题已经明确指向 `data_table`、`data_lineage`、`data_task`、`data_workflow`、`workflow_*`、`doris_*` 这些平台核心表
- 典型调用参数：
  - `--database`
  - `--table`
  - `--keyword`
- 命令模板：
  - `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/inspect_metadata.py" --keyword "工作流发布"`
  - `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/inspect_metadata.py" --database doris_ods --table dwd_tech_ops_cmp_performance_10m_di`
- 典型顺序：
  - 托管业务表场景的第一脚本

## resolve_datasource.py

- 用途：根据 database 判断引擎和数据源
- 适用场景：
  - metadata 已经确定 database
  - 还不清楚是 MySQL 还是 Doris
- 不适用场景：
  - 平台核心表问题；这类问题固定走 `opendataworks` MySQL
- 必须满足：
  - `--database` 必填，值直接取自 metadata 返回的 `db_name`
  - 成功一次后不要重复调用
  - `--database` 表示真实 database / schema，不是引擎名
- 命令模板：
  - `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/resolve_datasource.py" --database doris_ods`
- 典型顺序：
  - `inspect_metadata.py` 之后
  - `run_sql.py` 之前

## run_sql.py

- 用途：执行只读 SQL
- 适用场景：
  - 数据库明确
  - 引擎明确
  - SQL 已形成
- 可以直接执行的场景：
  - 已明确要查 `opendataworks` 的平台核心表，且字段名已知
- 必须先满足：
  - 指标清楚
  - 时间范围清楚
  - 维度清楚
  - 数据库清楚
- SQL 编写规则：
  - 平台核心表统一写 `opendataworks.<table>`
  - 托管业务表统一写 `<db_name>.<table>`
  - `mysql` / `doris` 只放在 `--engine`，不要写进 SQL schema
  - 对 Doris `df` 快照表，未指定历史区间时默认加最新 `ds` 过滤
  - 对 Doris `di` 增量表，必须显式加时间范围过滤，优先使用 `ds >= ... AND ds <= ...`
  - 业务环境默认优先过滤 `env_name` 的大写值；如果用户说的是数据中心或 CFC 环境，必须先改用对应字段
- 命令模板：
  - `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/run_sql.py" --database opendataworks --engine mysql --sql "SELECT layer, COUNT(*) AS table_cnt FROM opendataworks.data_table WHERE deleted = 0 GROUP BY layer ORDER BY table_cnt DESC LIMIT 20"`
  - `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/run_sql.py" --database doris_ods --engine doris --sql "SELECT * FROM doris_ods.some_table_df WHERE ds = (SELECT MAX(ds) FROM doris_ods.some_table_df) LIMIT 100"`
  - `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/run_sql.py" --database doris_ods --engine doris --sql "SELECT * FROM doris_ods.some_table_di WHERE ds BETWEEN '2026-03-01' AND '2026-03-13' LIMIT 100"`
- 禁止：
  - 没定位到数据库就执行
  - 用来“试着猜一下”
- 收口规则：
  - `sql_execution` 返回后就优先结束本轮推理
  - 首次返回非空且口径正确的 `sql_execution` 后，不要继续换表、换字段或重复执行等价 SQL
  - 若 `row_count = 0`，直接说明无数据，不要继续无休止换表或重复试探

## build_chart_spec.py

- 用途：把 SQL 结果转换成图表规范
- 典型决策：
  - 分类对比 -> `bar`
  - 时间趋势 -> `line`
  - 占比分析 -> `pie`
  - 用户明确要独立表格 -> `table`
  - 其他 -> 只保留 `sql_execution`
- 默认保底：
  - 不适合图表时不输出图表，直接保留 `sql_execution`
- 收口规则：
  - 成功返回一次 `chart_spec` 后就结束本轮，不要再次调用图表脚本
- 参数规则：
  - 优先使用 `--input '<sql_execution_json>'`
  - 只有 JSON 过长时才使用 `--input-file`
  - 对比必须显式传 `--chart-type bar`
  - 趋势必须显式传 `--chart-type line`
  - 占比必须显式传 `--chart-type pie`
  - 只有用户明确要独立表格时才传 `--chart-type table`
- 命令模板：
  - `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/build_chart_spec.py" --chart-type bar --input '{"kind":"sql_execution","rows":[...]}'`
  - `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/build_chart_spec.py" --chart-type line --input-file /tmp/sql_execution.json`

## format_answer.py

- 用途：整理最终中文结论
- 使用时机：
  - 已经拿到 SQL 执行结果
  - 需要压缩成用户可直接消费的结论
- 命令模板：
  - `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/format_answer.py" --input-file /tmp/sql_execution.json`

## 推荐脚本序列

- 统计：平台核心表可直接 `run_sql.py`；托管业务表用 `inspect_metadata.py` -> `run_sql.py`
- 对比：平台核心表可直接 `run_sql.py` -> `build_chart_spec.py --chart-type bar`；托管业务表用 `inspect_metadata.py` -> `run_sql.py` -> `build_chart_spec.py --chart-type bar`
- 趋势：平台核心表可直接 `run_sql.py` -> `build_chart_spec.py --chart-type line`；托管业务表用 `inspect_metadata.py` -> `run_sql.py` -> `build_chart_spec.py --chart-type line`
- 占比：平台核心表可直接 `run_sql.py` -> `build_chart_spec.py --chart-type pie`；托管业务表用 `inspect_metadata.py` -> `run_sql.py` -> `build_chart_spec.py --chart-type pie`
- 明细：平台核心表可直接 `run_sql.py`；托管业务表用 `inspect_metadata.py` -> `run_sql.py`
- 诊断：平台核心表可直接 `run_sql.py`；托管业务表用 `inspect_metadata.py` -> `resolve_datasource.py` -> `run_sql.py`
- 工作流发布趋势快路径：`21-metric-index.md` -> `22-sql-example-index.md` -> `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/run_sql.py" --database opendataworks --engine mysql --sql "<按 created_at 按天聚合 workflow_publish_record 的 SQL>"` -> `build_chart_spec.py --chart-type line`；首个有效结果返回后直接总结

## 诊断直达规则

- 对 `dwd_order`、`workflow_publish_record` 这类已经给出明确表名的平台核心表诊断问题，不要再搜索仓库代码、测试文件或文档实现。
- 这类问题的第一动作应是直接执行平台表 SQL，或用 `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/query_opendataworks_metadata.py" --kind lineage` / `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/run_sql.py" --database opendataworks --engine mysql --sql "<SQL>"` 查询 `data_lineage + data_table`。
- 如果第一次血缘 SQL 已返回非空结果，即使部分 `upstream_table` / `downstream_table` 为空，也直接基于现有结果总结；不要为了补齐空列继续追加第二条 SQL。
- 只有表名不唯一、数据库不清或字段不清时，才允许退回 `inspect_metadata.py` 或追问。

## 何时必须先追问

- 数据层级定义不清
- 发布状态口径不清
- 用户说“对比”但没说维度
- 用户说“趋势”但没说指标
- 目标表名存在多个候选
