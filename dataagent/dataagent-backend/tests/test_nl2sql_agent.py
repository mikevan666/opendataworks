from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core import nl2sql_agent as agent


class ClaudeAgentOptions:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class StreamEvent:
    def __init__(self, event):
        self.event = event


class SystemMessage:
    def __init__(self, subtype="init"):
        self.subtype = subtype


class UserMessage:
    def __init__(self, content, subtype=""):
        self.content = content
        self.subtype = subtype


class ResultMessage:
    def __init__(self, subtype="success", result=None):
        self.subtype = subtype
        self.result = result


def _install_fake_sdk(monkeypatch, messages):
    async def fake_query(*, prompt, options):
        for message in messages:
            yield message

    fake_module = SimpleNamespace(
        ClaudeAgentOptions=ClaudeAgentOptions,
        query=fake_query,
    )
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", fake_module)


def _build_run_input(question: str = "最近 30 天工作流发布次数趋势"):
    return agent.AgentRunInput(
        run_id="run-1",
        session_id="session-1",
        message_id="message-1",
        question=question,
        history=[],
        provider_id="anyrouter",
        model="claude-opus-4-6",
        database_hint=None,
        debug=False,
    )


def _collect_done_payload(run_input):
    async def _collect():
        done = None
        async for event in agent.stream_agent_reply(run_input):
            if event.get("type") == "done":
                done = event.get("payload") or {}
        return done

    return asyncio.run(_collect())


def test_skill_bootstrap_text_is_not_written_into_main_text(monkeypatch, tmp_path: Path):
    _install_fake_sdk(
        monkeypatch,
        [
            SystemMessage(),
            StreamEvent(
                {
                    "type": "content_block_start",
                    "index": 0,
                    "content_block": {"type": "tool_use", "id": "skill-1", "name": "Skill", "input": {}},
                }
            ),
            StreamEvent({"type": "content_block_stop", "index": 0}),
            StreamEvent({"type": "message_stop"}),
            UserMessage([{"type": "tool_result", "tool_use_id": "skill-1", "name": "Skill", "content": "Launching skill: dataagent-nl2sql"}]),
            UserMessage([{"type": "text", "text": "Base directory for this skill: /tmp/skill\n\n# DataAgent NL2SQL Skill"}]),
            StreamEvent({"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}),
            StreamEvent({"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "最终回答"}}),
            StreamEvent({"type": "content_block_stop", "index": 0}),
            StreamEvent({"type": "message_stop"}),
            ResultMessage("success"),
        ],
    )
    monkeypatch.setattr(
        agent,
        "resolve_runtime_provider_selection",
        lambda provider_id, model: {
            "provider_id": provider_id,
            "model": model,
            "api_key": "",
            "auth_token": "",
            "base_url": "https://example.invalid",
        },
    )
    monkeypatch.setattr(agent, "resolve_agent_project_cwd", lambda: tmp_path)

    done = _collect_done_payload(_build_run_input())

    assert done["status"] == "success"
    assert done["content"] == "最终回答"
    assert "Base directory for this skill:" not in done["content"]
    main_text_blocks = [block for block in done["blocks"] if block.get("type") == "main_text"]
    assert len(main_text_blocks) == 1
    assert main_text_blocks[0]["text"] == "最终回答"


def test_user_tool_results_are_not_skipped_after_partial_stream(monkeypatch, tmp_path: Path):
    _install_fake_sdk(
        monkeypatch,
        [
            SystemMessage(),
            StreamEvent({"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}),
            StreamEvent({"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "先给出结论。"}}),
            StreamEvent({"type": "content_block_stop", "index": 0}),
            StreamEvent(
                {
                    "type": "content_block_start",
                    "index": 1,
                    "content_block": {"type": "tool_use", "id": "read-1", "name": "Read", "input": {"file_path": "reference/21-metric-index.md"}},
                }
            ),
            StreamEvent({"type": "content_block_stop", "index": 1}),
            StreamEvent({"type": "message_stop"}),
            UserMessage(
                [
                    {
                        "type": "tool_result",
                        "tool_use_id": "read-1",
                        "name": "Read",
                        "content": "{\"kind\":\"python_execution\",\"summary\":\"ok\"}",
                    }
                ]
            ),
            ResultMessage("success"),
        ],
    )
    monkeypatch.setattr(
        agent,
        "resolve_runtime_provider_selection",
        lambda provider_id, model: {
            "provider_id": provider_id,
            "model": model,
            "api_key": "",
            "auth_token": "",
            "base_url": "https://example.invalid",
        },
    )
    monkeypatch.setattr(agent, "resolve_agent_project_cwd", lambda: tmp_path)

    done = _collect_done_payload(_build_run_input())

    tool_blocks = [block for block in done["blocks"] if str(block.get("tool_name") or "") == "Read"]
    assert tool_blocks
    assert "{\"kind\":\"python_execution\",\"summary\":\"ok\"}" in str(tool_blocks[0].get("output") or "")


def test_runtime_env_keeps_virtualenv_python_path(monkeypatch):
    fake_cfg = SimpleNamespace(
        mysql_host="127.0.0.1",
        mysql_port=3306,
        mysql_user="root",
        mysql_password="secret",
        mysql_database="opendataworks",
        query_result_limit=100,
    )
    monkeypatch.setattr(agent.sys, "executable", "/tmp/project/.venv/bin/python")

    runtime_env = agent._build_runtime_env(fake_cfg, {})

    assert runtime_env["DATAAGENT_PYTHON_BIN"] == "/tmp/project/.venv/bin/python"
    assert runtime_env["VIRTUAL_ENV"] == "/tmp/project/.venv"


@pytest.mark.parametrize(
    ("question", "tool_result_payload", "final_text", "expected_kind", "expected_fragment"),
    [
        (
            "最近 30 天工作流发布次数趋势",
            {
                "kind": "chart_spec",
                "version": 1,
                "chart_type": "line",
                "title": "最近30天工作流发布趋势",
                "x_field": "stat_day",
                "series": [{"name": "发布次数", "field": "publish_cnt", "type": "line"}],
                "dataset": [{"stat_day": "2026-03-01", "publish_cnt": 3}],
                "error": None,
            },
            "最近 30 天工作流发布次数整体平稳。",
            "chart_spec",
            "发布次数",
        ),
        (
            "各数据层表数量对比",
            {
                "kind": "chart_spec",
                "version": 1,
                "chart_type": "bar",
                "title": "各数据层表数量对比",
                "x_field": "layer",
                "series": [{"name": "表数量", "field": "table_cnt", "type": "bar"}],
                "dataset": [{"layer": "DWD", "table_cnt": 18}],
                "error": None,
            },
            "当前 DWD 层表数量最多。",
            "chart_spec",
            "table_cnt",
        ),
        (
            "各工作流发布操作类型占比",
            {
                "kind": "chart_spec",
                "version": 1,
                "chart_type": "pie",
                "title": "各工作流发布操作类型占比",
                "x_field": "operation",
                "series": [{"name": "发布次数", "field": "publish_cnt", "type": "pie"}],
                "dataset": [{"operation": "deploy", "publish_cnt": 33}, {"operation": "online", "publish_cnt": 9}],
                "error": None,
            },
            "当前工作流发布以 deploy 操作为主。",
            "chart_spec",
            "deploy",
        ),
        (
            "最近工作流发布记录",
            {
                "kind": "sql_execution",
                "engine": "mysql",
                "database": "opendataworks",
                "sql": "select workflow_id, version_id, target_engine, operation, status, operator, created_at from workflow_publish_record order by created_at desc limit 100",
                "columns": ["workflow_id", "version_id", "target_engine", "status", "created_at"],
                "rows": [{"workflow_id": 173, "version_id": 546, "target_engine": "dolphin", "status": "success", "created_at": "2026-02-26 16:34:27"}],
                "row_count": 1,
                "has_more": False,
                "duration_ms": 35,
                "summary": "返回最近工作流发布记录",
                "error": None,
            },
            "最近一条工作流发布记录发生在 2026-02-26 16:34:27。",
            "sql_execution",
            "workflow_publish_record",
        ),
        (
            "查看 dwd_tech_dev_inspection_rule_cnt_di 的上下游血缘",
            {
                "kind": "sql_execution",
                "engine": "mysql",
                "database": "opendataworks",
                "sql": "select dl.lineage_type, ut.table_name as upstream_table, dt.table_name as downstream_table from data_lineage dl left join data_table ut on ut.id = dl.upstream_table_id and ut.deleted = 0 left join data_table dt on dt.id = dl.downstream_table_id and dt.deleted = 0 where ut.table_name = 'dwd_tech_dev_inspection_rule_cnt_di' or dt.table_name = 'dwd_tech_dev_inspection_rule_cnt_di' order by dl.id desc limit 100",
                "columns": ["lineage_type", "upstream_table", "downstream_table"],
                "rows": [{"lineage_type": "input", "upstream_table": "dwd_tech_dev_inspection_rule_cnt_di", "downstream_table": None}],
                "row_count": 1,
                "has_more": False,
                "duration_ms": 28,
                "summary": "返回 dwd_tech_dev_inspection_rule_cnt_di 的上下游血缘",
                "error": None,
            },
            "已返回 dwd_tech_dev_inspection_rule_cnt_di 的上下游血缘关系。",
            "sql_execution",
            "dwd_tech_dev_inspection_rule_cnt_di",
        ),
    ],
)
def test_multiple_odw_question_scenarios_reach_final_done(
    monkeypatch,
    tmp_path: Path,
    question: str,
    tool_result_payload: dict,
    final_text: str,
    expected_kind: str,
    expected_fragment: str,
):
    _install_fake_sdk(
        monkeypatch,
        [
            SystemMessage(),
            StreamEvent(
                {
                    "type": "content_block_start",
                    "index": 0,
                    "content_block": {
                        "type": "tool_use",
                        "id": "bash-1",
                        "name": "Bash",
                        "input": {"command": "run scenario"},
                    },
                }
            ),
            StreamEvent({"type": "content_block_stop", "index": 0}),
            StreamEvent({"type": "message_stop"}),
            UserMessage(
                [
                    {
                        "type": "tool_result",
                        "tool_use_id": "bash-1",
                        "name": "Bash",
                        "content": json.dumps(tool_result_payload, ensure_ascii=False),
                    }
                ]
            ),
            StreamEvent({"type": "content_block_start", "index": 1, "content_block": {"type": "text", "text": ""}}),
            StreamEvent({"type": "content_block_delta", "index": 1, "delta": {"type": "text_delta", "text": final_text}}),
            StreamEvent({"type": "content_block_stop", "index": 1}),
            StreamEvent({"type": "message_stop"}),
            ResultMessage("success"),
        ],
    )
    monkeypatch.setattr(
        agent,
        "resolve_runtime_provider_selection",
        lambda provider_id, model: {
            "provider_id": provider_id,
            "model": model,
            "api_key": "",
            "auth_token": "",
            "base_url": "https://example.invalid",
        },
    )
    monkeypatch.setattr(agent, "resolve_agent_project_cwd", lambda: tmp_path)

    done = _collect_done_payload(_build_run_input(question))

    assert done["status"] == "success"
    assert done["content"] == final_text

    tool_blocks = [block for block in done["blocks"] if str(block.get("tool_name") or "") == "Bash"]
    assert len(tool_blocks) == 1
    output = str(tool_blocks[0].get("output") or "")
    assert expected_kind in output
    assert expected_fragment in output
