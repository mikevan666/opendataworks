from __future__ import annotations

from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "dataagent-nl2sql"


def _skill_text_snapshot() -> str:
    paths = [SKILL_ROOT / "SKILL.md"]
    paths.extend(sorted((SKILL_ROOT / "reference").rglob("*.md")))
    paths.extend(sorted((SKILL_ROOT / "assets").rglob("*.json")))
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_builtin_skill_keeps_generic_df_di_rules_without_business_defaults():
    snapshot = _skill_text_snapshot()

    forbidden_tokens = [
        "CFC环境名称",
        "数据中心名称",
        "组件名称",
        "接口名称",
        "env_name",
        "PROD",
        "SIM",
        "component_name",
        "interface_name",
        "dwd_tech_dev_inspection_rule_cnt_di",
    ]
    for token in forbidden_tokens:
        assert token not in snapshot

    required_tokens = [
        "DF快照表",
        "DI增量表",
        "workflow_publish_record",
        "data_lineage",
        "ds",
    ]
    for token in required_tokens:
        assert token in snapshot
