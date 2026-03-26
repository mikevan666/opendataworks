# 数据源路由

先结论：所有问数只允许单源路由。问题明确指向 `opendataworks` 平台核心表时直接走 MySQL；托管数据表先用元数据判断库表归属，再决定落到 MySQL 还是 Doris。

## 路由规则

- `data_table`、`data_field`、`data_lineage`、`data_task`、`data_workflow`、`workflow_*`、`doris_*` 这类平台核心表查询走 MySQL
- 托管数据表、事实表、汇总表先通过 metadata 定位数据库，再由 `resolve_datasource.py` 判断引擎
- 若 `resolve_datasource.py` 返回 `mysql`，则按 MySQL 语法和能力执行
- 若返回 `doris`，则按 Doris 语法和能力执行
- metadata 返回的 `db_name` / schema 才是 SQL 的库名前缀；`mysql` / `doris` 只是引擎类型，不是 schema
- 数据库明确后，SQL 统一写 `<database>.<table>`；平台核心表固定写 `opendataworks.<table>`
- 若 Doris 表名体现 `df` 快照含义，默认视为每日全量快照表，日期字段优先 `ds`；除非归因分析或用户明确要求历史区间，否则只查最新 `ds`
- 若 Doris 表名体现 `di` 增量含义，默认视为每日增量表，日期字段优先 `ds`；这类表必须按时间范围过滤

## 选择 MySQL 的典型情况

- 查询平台元数据与治理表
- 查询维表或轻量明细表
- 数据库明确位于 MySQL

## 选择 Doris 的典型情况

- 趋势分析
- 对比分析
- 汇总统计
- 大表聚合或日汇总表分析

## 必须先追问的路由冲突

- 用户问题同时命中多个数据库
- 候选表分布在不同引擎
- 同一指标在多张表中都有口径实现
- 用户命中 Doris `di` 增量表，但没有提供时间范围
- 问题依赖当前内置 skill 未定义的租户业务术语、对象或默认过滤

## 禁止事项

- 不要在单次回答里拼接跨源联查 SQL
- 不要在没确认目标数据库前直接 `run_sql.py`
- 不要把示例 SQL 的引擎直接套到真实问题里
- 不要把 `doris` / `mysql` 写成 SQL 的 schema 名
- 不要对 `df` 快照表默认扫全历史；未要求历史时先收敛到最新 `ds`
- 不要对 `di` 增量表省略时间范围过滤
