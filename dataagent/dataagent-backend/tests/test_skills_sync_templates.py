from __future__ import annotations

from core import skills_sync


def test_default_query_metadata_script_uses_cli_only_runtime():
    template = skills_sync._default_query_metadata_script()

    assert 'call_metadata_cli(' in template
    assert '"export"' in template
    assert "pymysql" not in template
    assert "ODW_MYSQL_" not in template


def test_default_get_table_ddl_script_uses_cli_only_runtime():
    template = skills_sync._default_get_table_ddl_script()

    assert 'call_metadata_cli(' in template
    assert '"ddl"' in template
    assert "pymysql" not in template
    assert "ODW_MYSQL_" not in template


def test_default_get_lineage_script_uses_cli_only_runtime():
    template = skills_sync._default_get_lineage_script()

    assert 'call_metadata_cli(' in template
    assert '"lineage"' in template
    assert "pymysql" not in template
    assert "ODW_MYSQL_" not in template


def test_default_reference_templates_describe_cli_only_runtime():
    combined = "\n".join(
        [
            skills_sync._default_skill_md(),
            skills_sync._default_reference_tools(),
            skills_sync._default_reference_runtime(),
        ]
    )

    assert "portal-mcp" in combined
    assert "mcp__portal__portal_search_tables" in combined
    assert "mcp__portal__portal_get_lineage" in combined
    assert "mcp__portal__portal_get_table_ddl" in combined
    assert "mcp__portal__portal_query_readonly" in combined
    assert "get_lineage.py" in combined
    assert "get_table_ddl.py" in combined
    assert "odw-cli" in combined
    assert "/api/v1/ai/*" in combined
    assert "MCP 不可用" in combined
    assert "不直连数据库" in combined
    assert "pymysql" not in combined
    assert "ODW_MYSQL_" not in combined
