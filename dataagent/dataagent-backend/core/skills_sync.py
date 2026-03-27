from __future__ import annotations

"""
Skills 静态模板初始化/校验
- 统一技能结构：SKILL.md / reference / scripts / assets
- 只补骨架，不覆盖现有内容
"""

import json
from pathlib import Path
from typing import Any

from config import get_settings


def ensure_static_skills_bundle() -> dict[str, Any]:
    cfg = get_settings()
    root = _resolve_output_dir(cfg.skills_output_dir)
    paths = _ensure_structure(root)
    files: list[Path] = []

    _remove_legacy_files(
        [
            root / "README.md",
            root / "manifest.json",
            root / "methodology/nl2semantic2lf2sql.md",
            root / "references/opendataworks-dynamic-metadata.md",
            root / "references/tool-output-contract.md",
            root / "ontology/ontology.json",
            root / "ontology/business_concepts.json",
            root / "ontology/metrics.json",
            root / "ontology/constraints.json",
            root / "knowledge/few_shots.json",
            root / "knowledge/business_rules.json",
            root / "metadata/metadata_catalog.json",
            root / "metadata/lineage_catalog.json",
            root / "metadata/semantic_mappings.json",
            root / "metadata/source_mapping.json",
            root / "governance/policies.json",
        ]
    )

    files.extend(
        filter(
            None,
            [
                _write_text_if_absent(root / "SKILL.md", _default_skill_md()),
                _write_text_if_absent(paths["reference"] / "00-skill-map.md", _default_reference_skill_map()),
                _write_text_if_absent(paths["reference"] / "10-query-playbooks.md", _default_reference_playbooks()),
                _write_text_if_absent(paths["reference"] / "11-datasource-routing.md", _default_reference_datasource()),
                _write_text_if_absent(paths["reference"] / "20-term-index.md", _default_reference_term_index()),
                _write_text_if_absent(paths["reference"] / "21-metric-index.md", _default_reference_metric_index()),
                _write_text_if_absent(paths["reference"] / "22-sql-example-index.md", _default_reference_sql_examples()),
                _write_text_if_absent(paths["reference"] / "30-tool-recipes.md", _default_reference_tools()),
                _write_text_if_absent(paths["reference"] / "40-runtime-metadata.md", _default_reference_runtime()),
                _write_text_if_absent(paths["reference"] / "50-tool-output-contract.md", _default_reference_output_contract()),
                _write_text_if_absent(paths["scripts"] / "_opendataworks_runtime.py", _default_runtime_helper()),
                _write_text_if_absent(paths["scripts"] / "inspect_metadata.py", _default_script_stub("inspect_metadata")),
                _write_text_if_absent(paths["scripts"] / "resolve_datasource.py", _default_script_stub("resolve_datasource")),
                _write_text_if_absent(paths["scripts"] / "run_sql.py", _default_script_stub("run_sql")),
                _write_text_if_absent(paths["scripts"] / "build_chart_spec.py", _default_script_stub("build_chart_spec")),
                _write_text_if_absent(paths["scripts"] / "format_answer.py", _default_script_stub("format_answer")),
                _write_text_if_absent(paths["scripts"] / "build_reference_digest.py", _default_script_stub("build_reference_digest")),
                _write_text_if_absent(paths["scripts"] / "query_opendataworks_metadata.py", _default_query_metadata_script()),
            ],
        )
    )

    templates: dict[Path, Any] = {
        paths["assets"] / "ontology.json": {"schema_version": "1.0", "items": []},
        paths["assets"] / "business_concepts.json": {"schema_version": "1.0", "items": []},
        paths["assets"] / "metrics.json": {"schema_version": "1.0", "items": []},
        paths["assets"] / "constraints.json": {
            "schema_version": "1.0",
            "global": {
                "row_limit_max": 1000,
                "timezone": "Asia/Shanghai",
                "forbidden_ops": ["drop", "truncate", "delete", "alter", "create", "insert", "update"],
            },
            "items": [],
        },
        paths["assets"] / "few_shots.json": {"schema_version": "1.0", "items": []},
        paths["assets"] / "business_rules.json": {"schema_version": "1.0", "items": []},
        paths["assets"] / "semantic_mappings.json": {"schema_version": "1.0", "items": []},
        paths["assets"] / "policies.json": {
            "schema_version": "1.0",
            "items": [
                {"policy_key": "sql_read_only", "description": "仅允许查询语句", "enabled": True},
                {"policy_key": "require_limit", "description": "查询必须包含 LIMIT 保护", "enabled": True},
            ],
        },
        paths["assets"] / "term_explanations.json": {"schema_version": "1.0", "items": []},
        paths["assets"] / "sql_examples.json": {"schema_version": "1.0", "items": []},
        paths["chart_template"] / "table.json": {
            "chart_type": "table",
            "usage": "默认保底结果表达",
            "required_fields": ["columns", "rows"],
        },
        paths["chart_template"] / "bar.json": {
            "chart_type": "bar",
            "usage": "分类对比或 TopN",
            "required_fields": ["x_field", "series", "dataset"],
        },
        paths["chart_template"] / "line.json": {
            "chart_type": "line",
            "usage": "时间趋势",
            "required_fields": ["x_field", "series", "dataset"],
        },
        paths["chart_template"] / "pie.json": {
            "chart_type": "pie",
            "usage": "少类别占比分析",
            "required_fields": ["series", "dataset"],
        },
    }
    for path, payload in templates.items():
        created = _write_json_if_absent(path, payload)
        if created:
            files.append(created)

    return {
        "output_dir": str(root),
        "files": [str(x) for x in files],
    }


def _resolve_output_dir(raw: str) -> Path:
    base = Path(__file__).resolve().parent.parent
    path = Path(raw or "../.claude/skills/dataagent-nl2sql")
    if path.is_absolute():
        return path
    return (base / path).resolve()


def _ensure_structure(root: Path) -> dict[str, Path]:
    paths = {
        "root": root,
        "reference": root / "reference",
        "scripts": root / "scripts",
        "assets": root / "assets",
        "chart_template": root / "assets" / "chart-template",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_json_if_absent(path: Path, payload: Any) -> Path | None:
    if path.exists():
        return None
    return _write_json(path, payload)


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path


def _write_text_if_absent(path: Path, content: str) -> Path | None:
    if path.exists():
        return None
    return _write_text(path, content)


def _remove_legacy_files(paths: list[Path]):
    for path in paths:
        if path.exists() and path.is_file():
            path.unlink()


def _default_skill_md() -> str:
    return """---
name: dataagent-nl2sql
description: Use this built-in skill for Chinese OpenDataWorks intelligent-query and NL2SQL work across MySQL and Doris: platform metadata, workflow, lineage, datasource routing, generic table discovery, backend-routed read-only SQL execution, term explanation, and chart-oriented answers. Prefer MCP-first via portal-mcp when `mcp__portal__portal_*` tools are visible, and fall back to CLI/scripts only when MCP is unavailable. Prefer platform terms and generic data-platform rules; do not assume tenant-specific business defaults.
---

# DataAgent NL2SQL Skill

## 适用范围

- 数据问答、统计、对比、趋势、占比、明细、诊断
- 术语解释、SQL 示例
- 表格、条形图、折线图、饼图

## 固定阅读顺序

1. `reference/00-skill-map.md`
2. `reference/10-query-playbooks.md`
3. 按需阅读 `reference/11/20/21/22/30/40/50`
4. 仍有缺口时再下钻 `assets/*` 或执行 `scripts/*`

## 固定执行顺序

1. 先判问题类型
2. 术语、指标、数据库不清则先追问
3. 若可见 `mcp__portal__portal_*`，优先直接调用 portal-mcp 工具
4. 若 MCP 不可用，表字段不清先 `inspect_metadata.py`
5. 若 MCP 不可用，引擎不清再 `resolve_datasource.py`
6. SQL 明确后才 `run_sql.py` 或 `mcp__portal__portal_query_readonly`
7. 结果适合图表时再 `build_chart_spec.py`

## 脚本执行规范

- 本地脚本统一通过 `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/<name>.py" ...` 调用
- 若运行时已注入 `portal-mcp`，优先直接调用 `mcp__portal__portal_search_tables`、`mcp__portal__portal_get_lineage`、`mcp__portal__portal_resolve_datasource`、`mcp__portal__portal_export_metadata`、`mcp__portal__portal_get_table_ddl`、`mcp__portal__portal_query_readonly`
- metadata 与只读 SQL 的 fallback 路径固定通过 `${DATAAGENT_SKILL_ROOT}/bin/odw-cli` 转发到 backend `/api/v1/ai/*`
- 固定脚本：`inspect_metadata.py`、`resolve_datasource.py`、`run_sql.py`、`build_chart_spec.py`、`format_answer.py`、`query_opendataworks_metadata.py`
- 禁止自己拼 `/app/scripts/...`、`scripts/<name>.py` 或手写猜测脚本名。
"""


def _default_reference_skill_map() -> str:
    return """# 技能地图

先结论：先分类，再看摘要，再决定是否执行 portal-mcp 工具或 fallback 脚本。

- 统计：先看 `10-query-playbooks.md`、`21-metric-index.md`，优先 `mcp__portal__portal_query_readonly`
- 对比：先看 `10-query-playbooks.md`、`21-metric-index.md`，优先 `mcp__portal__portal_search_tables`
- 趋势：先看 `10-query-playbooks.md`、`21-metric-index.md`，优先 `mcp__portal__portal_query_readonly`
- 占比：先看 `10-query-playbooks.md`、`20-term-index.md`，优先 `mcp__portal__portal_query_readonly`
- 术语解释：先看 `20-term-index.md`
- SQL 示例：先看 `22-sql-example-index.md`
"""


def _default_reference_playbooks() -> str:
    return """# 场景 Playbooks

先结论：统计默认表格，对比默认条形图，趋势默认折线图，占比默认饼图。portal-mcp 可见时优先 `mcp__portal__portal_*`，否则回退脚本。

- 统计：确认指标与时间范围
- 对比：确认对比维度、指标、时间范围
- 趋势：确认指标、时间粒度、时间范围
- 占比：确认分类维度和指标
- 明细：确认对象、过滤条件、字段
- 诊断：确认异常指标和对比基线
"""


def _default_reference_datasource() -> str:
    return """# 数据源路由

先结论：所有问数只允许单源路由。优先 `mcp__portal__portal_resolve_datasource`；无 MCP 时再走 `resolve_datasource.py`。

- 平台元数据查询固定使用 `database=opendataworks`、`engine=mysql` 的只读查询路径
- 托管数据表的事实与汇总查询由 `resolve_datasource.py` 判断 MySQL 或 Doris
- 不做跨源联查
"""


def _default_reference_term_index() -> str:
    return """# 术语索引

先结论：遇到平台术语、库表别名或通用口径不清时先看本页；仍不清晰再下钻 `assets/term_explanations.json`。
"""


def _default_reference_metric_index() -> str:
    return """# 指标索引

先结论：遇到统计、对比、趋势问题，先确认指标公式、默认时间字段和约束。
"""


def _default_reference_sql_examples() -> str:
    return """# SQL 示例索引

先结论：示例只用于校准结构，不要直接照抄到最终回答。
"""


def _default_reference_tools() -> str:
    return """# 工具 Recipes

先结论：portal-mcp 是首选工具面；只有 MCP 不可用时才走脚本调用。两条路径都必须按“先澄清、再定位、后执行”的顺序进行。

- 统一命令格式：`"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/<name>.py" ...`
- 首选 MCP tools：`mcp__portal__portal_search_tables`、`mcp__portal__portal_get_lineage`、`mcp__portal__portal_resolve_datasource`、`mcp__portal__portal_export_metadata`、`mcp__portal__portal_get_table_ddl`、`mcp__portal__portal_query_readonly`
- `inspect_metadata.py`、`resolve_datasource.py`、`query_opendataworks_metadata.py`、`run_sql.py` 都只通过 `odw-cli -> backend /api/v1/ai/*` 执行，不直连数据库
- 固定脚本：`inspect_metadata.py`、`resolve_datasource.py`、`run_sql.py`、`build_chart_spec.py`、`format_answer.py`、`query_opendataworks_metadata.py`
- 禁止使用 `/app/scripts/...`、`scripts/<name>.py` 或自己猜脚本名
- `inspect_metadata.py`：定位数据库、表、字段、血缘
- `resolve_datasource.py`：判断目标引擎与数据源
- `run_sql.py`：执行只读 SQL
- `build_chart_spec.py`：根据结果决定是否出图
- `format_answer.py`：整理最终中文结论
"""


def _default_reference_runtime() -> str:
    return """# 运行时元数据与数据源说明

先结论：需要动态补齐库表结构、血缘、数据源或只读 SQL 时，优先走 `portal-mcp`；只有 MCP 不可用时才回退到 skill 自带 `odw-cli`，不要直连数据库。
"""


def _default_reference_output_contract() -> str:
    return """# 工具输出契约

先结论：表格保底来自 `sql_execution`，图表来自 `chart_spec`。

- `metadata_snapshot`
- `datasource_resolution`
- `sql_execution`
- `python_execution`
- `chart_spec`
"""


def _default_runtime_helper() -> str:
    return """from __future__ import annotations

# OpenDataWorks 运行时帮助函数留在真实 skill 包里，这里只提供最小骨架。
"""


def _default_script_stub(name: str) -> str:
    return f"""from __future__ import annotations


def main() -> None:
    raise SystemExit("{name}.py is a placeholder. Replace it with the real skill implementation.")


if __name__ == "__main__":
    main()
"""


def _default_query_metadata_script() -> str:
    return '''from __future__ import annotations

import argparse
import json

from _opendataworks_runtime import call_metadata_cli


def main() -> None:
    parser = argparse.ArgumentParser(description="Query OpenDataWorks metadata tables")
    parser.add_argument("--kind", choices=["tables", "lineage", "datasource"], required=True)
    parser.add_argument("--database", default="")
    args = parser.parse_args()

    payload = call_metadata_cli(
        "export",
        kind=args.kind,
        database=str(args.database or "").strip(),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''
