---
name: dataagent-nl2sql
description: "Use this skill for Chinese intelligent-query and NL2SQL work: answering business data questions, locating tables, routing between MySQL and Doris, generating or executing read-only SQL, checking lineage or datasource metadata, explaining metrics and business terms, and shaping results into table/bar/line/pie outputs. Use it whenever the user asks for 数据问答、取数、统计、对比、趋势、占比、明细、诊断、血缘排查、指标口径、术语解释 or SQL 示例, even if they do not explicitly mention SQL or charts. Do not use it for general chat, write/update/delete operations, or cross-source federated joins."
compatibility: "Requires DATAAGENT_PYTHON_BIN, DATAAGENT_SKILL_ROOT, ${DATAAGENT_SKILL_ROOT}/bin/odw-cli, ODW_BACKEND_BASE_URL, ODW_AGENT_SERVICE_TOKEN, and host sh+curl+pymysql."
tools: [Bash, Read]
---

# DataAgent NL2SQL Skill

Convert Chinese natural-language data questions into read-only SQL, execute against MySQL or Doris, and return structured results with optional chart specs.

## Scope

**Covered scenarios:** 数据问答、取数、统计、对比、趋势、占比、明细、诊断、血缘排查、指标口径、术语解释、SQL 示例

**Out of scope:** general chat, write/update/delete SQL, cross-source federated joins, scenarios where the target table cannot be determined and the user refuses to clarify.

## Iron Laws

1. **ALWAYS** read [`reference/00-skill-map.md`](reference/00-skill-map.md) first, then progressively load references as needed — never bulk-read all assets upfront.
2. **NEVER** execute `run_sql.py` without first confirming the target database, engine, metrics, and time range.
3. **ALWAYS** write table names as `<schema>.<table>` in SQL — never omit the schema, and never use engine names (`mysql`/`doris`) as schema.
4. **NEVER** execute INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER, or CREATE statements.
5. **ALWAYS** include a LIMIT clause on SELECT queries (default 100).
6. **ALWAYS** ask the user to clarify before guessing when terminology, target table, time range, or comparison dimension is ambiguous.
7. **NEVER** run `pip install`, `uv add`, `which python`, `python --version`, or any environment probing commands.
8. **ALWAYS** verify `${DATAAGENT_SKILL_ROOT}/bin/odw-cli` exists before calling any metadata script — if missing, stop and tell the user to install it. A missing execute bit is tolerated at runtime via `sh`.
9. **ALWAYS** respond in Chinese: conclusion first, then evidence. Never echo back raw tool output verbatim.
10. **ALWAYS** stop after the first correct `sql_execution` or `chart_spec` — do not re-execute equivalent SQL or continue reading assets.

## Anti-Patterns

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| Bulk-reading `assets/*.json` at the start | Wastes tokens, ignores progressive disclosure | Follow the fixed reading order; only drill into assets when references are insufficient |
| Using `mysql` or `doris` as SQL schema | Engine type is not a database name | Use metadata-returned `db_name` as the schema prefix |
| Running `run_sql.py` without database confirmation | Generates blind-guess SQL | Route through `inspect_metadata.py` → `resolve_datasource.py` first for managed tables |
| Querying Doris `di` table without time range | Full-table scan on incremental data | Always require explicit `ds BETWEEN ... AND ...` for `di` tables |
| Querying Doris `df` table across full history | Unnecessary data scan on snapshot tables | Default to latest `ds` partition unless user explicitly requests historical range |
| Retrying with different interpreters on script error | Probes the environment instead of fixing the input | Diagnose from the actual error message; adjust parameters or ask the user |
| Generating chart when data is unsuitable | Forces visual output on 1-row or text results | Only produce `chart_spec` when the data structure genuinely fits a chart |
| Re-executing equivalent SQL after getting results | Wastes resources and confuses the answer | Stop after the first correct result |

## Fixed Reading Order

Process any question in this order; stop as soon as sufficient context is gathered:

1. Read [`reference/00-skill-map.md`](reference/00-skill-map.md) — classify the question type and execution path
2. Read [`reference/10-query-playbooks.md`](reference/10-query-playbooks.md) — match the concrete playbook
3. If datasource routing is unclear → [`reference/11-datasource-routing.md`](reference/11-datasource-routing.md)
4. If business semantics are unclear → [`reference/20-term-index.md`](reference/20-term-index.md), [`reference/21-metric-index.md`](reference/21-metric-index.md), [`reference/22-sql-example-index.md`](reference/22-sql-example-index.md)
5. If script usage details are unclear → [`reference/30-tool-recipes.md`](reference/30-tool-recipes.md), [`reference/40-runtime-metadata.md`](reference/40-runtime-metadata.md), [`reference/50-tool-output-contract.md`](reference/50-tool-output-contract.md)
6. Only when all references above are insufficient → drill into `assets/*` or execute `scripts/*`

## Fixed Execution Order

### Step A: Classify the Question

Assign one primary type: 统计 | 对比 | 趋势 | 占比 | 明细 | 诊断 | 术语解释 | SQL 示例

If a question spans multiple types, identify the primary goal first, then supplement.

### Step B: Determine Whether to Ask for Clarification

Ask before guessing when any of these apply:

- Terminology ambiguity (数据层级, 发布状态, 任务依赖, Doris 只读账号)
- Target database or table is not unique
- Time range or granularity is unspecified
- User says "对比" without specifying the comparison dimension
- User says "趋势" without specifying the metric
- User says "环境" without clarifying `env_name` vs. data-center name vs. CFC environment name
- Doris `df` table but unclear whether to query latest snapshot or historical range
- Doris `di` table but no time range provided

### Step C: Execute Scripts

Follow this script pipeline:

1. **Terminology unclear** → consult `reference/20-*`, `21-*`, `22-*`
2. **Platform core table with known fields** → directly execute `run_sql.py` against `opendataworks` MySQL
3. **Managed business table, fields unclear** → `inspect_metadata.py` first
4. **Engine unclear** → `resolve_datasource.py`
5. **SQL confirmed** → `run_sql.py`
6. **Result suits a chart** → `build_chart_spec.py` with explicit `--chart-type bar|line|pie`
7. **User explicitly wants standalone table** → `build_chart_spec.py --chart-type table`
8. **Need summary** → `format_answer.py`

Do not execute `run_sql.py` without confirmed database, metrics, and dimensions.

### Step D: Script Execution Rules

All scripts execute via: `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/<name>.py" ...`

Allowed scripts only: `inspect_metadata.py`, `resolve_datasource.py`, `run_sql.py`, `build_chart_spec.py`, `format_answer.py`, `query_opendataworks_metadata.py`, `build_reference_digest.py`

Command templates:

```bash
# Metadata inspection
"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/inspect_metadata.py" --database <db> --table <table> --keyword <keyword>

# Datasource resolution
"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/resolve_datasource.py" --database <db_name> [--engine mysql|doris]

# SQL execution
"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/run_sql.py" --database <db_name> --engine <mysql|doris> --sql "<SQL>"

# Chart generation
"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/build_chart_spec.py" --chart-type <bar|line|pie|table> --input '<sql_execution_json>'

# Answer formatting
"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/format_answer.py" --input '<sql_execution_json>'
```

Prohibitions:
- Never fabricate script paths or names (no `/app/scripts/...`, no bare `scripts/<name>.py`)
- Never call `odw-cli` directly — it is an internal implementation detail of the Python scripts
- Never run environment probing commands (`pip install`, `which python`, etc.)
- If a script returns an error, diagnose from the error output — do not blindly retry with different interpreters
- Read the corresponding `reference/*` before executing a script — do not interleave reading and executing
- For 统计/对比/趋势/占比/明细/诊断 questions, the first real action must be a concrete script call or a clarifying question — not reading `assets/*.json`
- Once script parameters are clear, always execute the script — do not skip execution and give SQL conclusions based solely on references

## Multi-Datasource Constraints

- Platform core tables (`data_table`, `data_field`, `data_lineage`, `data_task`, `data_workflow`, `workflow_*`, `doris_*`) → always MySQL via `opendataworks`
- Managed business tables may be on MySQL or Doris — always do single-source routing first
- If candidate tables span different engines or databases within the same answer, ask the user to narrow scope

## Chart Constraints

| Chart Type | When to Use | Explicit Flag |
|---|---|---|
| Table | Default fallback; always safe | `--chart-type table` (only when user explicitly requests standalone table) |
| Bar | Category comparison, TopN, ranking | `--chart-type bar` |
| Line | Time-series trends | `--chart-type line` |
| Pie | Proportional analysis with 2–8 categories | `--chart-type pie` |

Do not generate `chart_spec` when data is unsuitable for visualization — retain `sql_execution` only. Always pass explicit `--chart-type` — never let the script auto-guess.

## Assets & Scripts Reference

### Reference Documents

- [`reference/00-skill-map.md`](reference/00-skill-map.md) — question type → execution path mapping
- [`reference/10-query-playbooks.md`](reference/10-query-playbooks.md) — concrete playbooks per question type
- [`reference/11-datasource-routing.md`](reference/11-datasource-routing.md) — MySQL vs. Doris routing rules
- [`reference/20-term-index.md`](reference/20-term-index.md) — business term glossary
- [`reference/21-metric-index.md`](reference/21-metric-index.md) — metric formulas and constraints
- [`reference/22-sql-example-index.md`](reference/22-sql-example-index.md) — SQL templates by scenario
- [`reference/30-tool-recipes.md`](reference/30-tool-recipes.md) — detailed script usage recipes
- [`reference/40-runtime-metadata.md`](reference/40-runtime-metadata.md) — core table schema and runtime details
- [`reference/50-tool-output-contract.md`](reference/50-tool-output-contract.md) — output format contracts

### Scripts

- [`scripts/inspect_metadata.py`](scripts/inspect_metadata.py) — locate managed business tables
- [`scripts/resolve_datasource.py`](scripts/resolve_datasource.py) — resolve engine and datasource
- [`scripts/run_sql.py`](scripts/run_sql.py) — execute read-only SQL
- [`scripts/build_chart_spec.py`](scripts/build_chart_spec.py) — generate chart spec from SQL results
- [`scripts/format_answer.py`](scripts/format_answer.py) — summarize results for final answer
- [`scripts/query_opendataworks_metadata.py`](scripts/query_opendataworks_metadata.py) — export platform metadata
- [`scripts/build_reference_digest.py`](scripts/build_reference_digest.py) — regenerate reference index files from assets

### Structured Assets

- `assets/term_explanations.json`, `assets/business_concepts.json`, `assets/semantic_mappings.json`
- `assets/metrics.json`, `assets/business_rules.json`, `assets/constraints.json`
- `assets/sql_examples.json`, `assets/few_shots.json`
- `assets/chart-template/*.json`

## Final Answer Requirements

- Lead with the conclusion, then provide supporting evidence
- If a query was executed, cite the structured result — do not repeat raw tool output
- For pure terminology or SQL example questions, SQL execution is not required
- If information is insufficient, state what is missing and ask a minimal clarifying question
- Never expose internal steps (reading docs, locating scripts, preparing execution) in the final answer
