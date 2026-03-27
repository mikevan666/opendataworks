from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core import nl2sql_agent


def test_build_runtime_env_does_not_expose_direct_db_connection_settings(monkeypatch):
    monkeypatch.setattr(nl2sql_agent, "resolve_builtin_skill_root_dir", lambda: Path("/tmp/skill-root"))

    cfg = SimpleNamespace(query_result_limit=120)
    params = SimpleNamespace(sql_read_timeout_seconds=45, sql_write_timeout_seconds=90)

    runtime_env = nl2sql_agent._build_runtime_env(cfg, {"CUSTOM_FLAG": "1"}, params)

    assert runtime_env["CUSTOM_FLAG"] == "1"
    assert runtime_env["DATAAGENT_QUERY_LIMIT"] == "120"
    assert runtime_env["DATAAGENT_RESULT_PREVIEW_ROWS"] == "20"
    assert runtime_env["DATAAGENT_SQL_READ_TIMEOUT_SECONDS"] == "45"
    assert runtime_env["DATAAGENT_SKILL_ROOT"] == "/tmp/skill-root"
    assert "ODW_MYSQL_HOST" not in runtime_env
    assert "ODW_MYSQL_PORT" not in runtime_env
    assert "ODW_MYSQL_USER" not in runtime_env
    assert "ODW_MYSQL_PASSWORD" not in runtime_env
    assert "ODW_MYSQL_DATABASE" not in runtime_env
    assert "DATAAGENT_SQL_WRITE_TIMEOUT_SECONDS" not in runtime_env


def test_build_portal_mcp_servers_returns_http_config():
    cfg = SimpleNamespace(
        dataagent_portal_mcp_enabled=True,
        dataagent_portal_mcp_base_url="http://portal-mcp:8801/mcp/",
        dataagent_portal_mcp_token="portal-token",
        dataagent_portal_mcp_token_header_name="X-Portal-MCP-Token",
    )

    actual = nl2sql_agent._build_portal_mcp_servers(cfg)

    assert actual == {
        "portal": {
            "type": "http",
            "url": "http://portal-mcp:8801/mcp",
            "headers": {"X-Portal-MCP-Token": "portal-token"},
        }
    }


def test_build_portal_mcp_servers_returns_empty_when_disabled_or_incomplete():
    disabled = SimpleNamespace(
        dataagent_portal_mcp_enabled=False,
        dataagent_portal_mcp_base_url="http://portal-mcp:8801/mcp",
        dataagent_portal_mcp_token="portal-token",
    )
    missing_token = SimpleNamespace(
        dataagent_portal_mcp_enabled=True,
        dataagent_portal_mcp_base_url="http://portal-mcp:8801/mcp",
        dataagent_portal_mcp_token="",
    )

    assert nl2sql_agent._build_portal_mcp_servers(disabled) == {}
    assert nl2sql_agent._build_portal_mcp_servers(missing_token) == {}


def test_build_allowed_tools_includes_portal_mcp_tools_once():
    allowed_tools = nl2sql_agent._build_allowed_tools(
        {
            "portal": {
                "type": "http",
                "url": "http://portal-mcp:8801/mcp",
                "headers": {"X-Portal-MCP-Token": "portal-token"},
            }
        }
    )

    assert allowed_tools[:6] == ["Skill", "Bash", "Read", "LS", "Glob", "Grep"]
    assert "mcp__portal__portal_search_tables" in allowed_tools
    assert "mcp__portal__portal_query_readonly" in allowed_tools
    assert len(allowed_tools) == len(set(allowed_tools))


class _ClaudeAgentOptions:
    last_kwargs = None

    def __init__(self, **kwargs):
        type(self).last_kwargs = kwargs
        self.kwargs = kwargs


class _ResultMessage:
    def __init__(self, subtype="success", result=None):
        self.subtype = subtype
        self.result = result


def test_stream_agent_reply_injects_portal_mcp_servers(monkeypatch, tmp_path: Path):
    async def fake_query(*, prompt, options):
        yield _ResultMessage("success", result="smoke-ok")

    monkeypatch.setitem(
        sys.modules,
        "claude_agent_sdk",
        SimpleNamespace(ClaudeAgentOptions=_ClaudeAgentOptions, query=fake_query),
    )
    monkeypatch.setattr(
        nl2sql_agent,
        "get_settings",
        lambda: SimpleNamespace(
            claude_model="",
            agent_timeout_seconds=60,
            agent_interactive_max_turns=24,
            agent_max_turns=20,
            query_result_limit=100,
            dataagent_portal_mcp_enabled=True,
            dataagent_portal_mcp_base_url="http://portal-mcp:8801/mcp",
            dataagent_portal_mcp_token="portal-token",
            dataagent_portal_mcp_token_header_name="X-Portal-MCP-Token",
        ),
    )
    monkeypatch.setattr(
        nl2sql_agent,
        "resolve_runtime_provider_selection",
        lambda provider_id, model: {
            "provider_id": provider_id,
            "model": model,
            "api_key": "",
            "auth_token": "",
            "base_url": "https://example.invalid",
            "supports_partial_messages": True,
        },
    )
    monkeypatch.setattr(nl2sql_agent, "resolve_agent_project_cwd", lambda: tmp_path)
    monkeypatch.setattr(nl2sql_agent, "resolve_builtin_skill_root_dir", lambda: Path("/tmp/skill-root"))

    async def _run():
        events = []
        async for item in nl2sql_agent.stream_agent_reply(
            nl2sql_agent.AgentRunInput(
                run_id="run-1",
                session_id="session-1",
                message_id="message-1",
                question="最近 30 天工作流发布次数趋势",
                history=[],
                provider_id="openrouter",
                model="anthropic/claude-sonnet-4.5",
                database_hint=None,
                timeout_seconds=60,
                sql_read_timeout_seconds=45,
            )
        ):
            events.append(item)
        return events

    emitted = asyncio.run(_run())

    assert emitted
    assert _ClaudeAgentOptions.last_kwargs["mcp_servers"] == {
        "portal": {
            "type": "http",
            "url": "http://portal-mcp:8801/mcp",
            "headers": {"X-Portal-MCP-Token": "portal-token"},
        }
    }
    assert "mcp__portal__portal_query_readonly" in _ClaudeAgentOptions.last_kwargs["allowed_tools"]
