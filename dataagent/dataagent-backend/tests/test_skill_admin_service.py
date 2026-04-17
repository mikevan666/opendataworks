from __future__ import annotations

import sys
import types
from pathlib import Path

import anyio

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core import skill_admin_service
from core.skill_admin_service import _merge_provider_settings, _merge_settings_payload


def test_merge_provider_settings_can_reenable_provider_with_models():
    current = {
        "anyrouter": {
            "provider_id": "anyrouter",
            "auth_token": "existing-token",
            "base_url": "https://a-ocnfniawgw.cn-shanghai.fcapp.run",
            "provider_enabled": True,
            "enabled_models": [],
            "custom_models": [],
            "model_detections": {},
            "enabled": False,
            "validation_status": "unverified",
            "validation_message": "请先检测并启用至少一个模型",
        }
    }
    patch = {
        "anyrouter": {
            "provider_id": "anyrouter",
            "provider_enabled": True,
            "auth_token": "existing-token",
            "base_url": "https://a-ocnfniawgw.cn-shanghai.fcapp.run",
            "enabled_models": ["claude-opus-4-6"],
            "custom_models": [],
            "model_detections": {
                "claude-opus-4-6": {
                    "status": "verified",
                    "message": "模型检测通过",
                    "checked_at": "2026-04-17T10:00:00",
                }
            },
        }
    }

    merged = _merge_provider_settings(
        current,
        patch,
        legacy_payload={"provider_id": "anyrouter", "model": "claude-opus-4-6"},
    )

    provider = merged["anyrouter"]
    assert provider["enabled_models"] == ["claude-opus-4-6"]
    assert provider["validation_status"] == "verified"
    assert provider["enabled"] is True


def test_merge_provider_settings_preserves_partial_capability_flag():
    merged = _merge_provider_settings(
        {
            "anthropic_compatible": {
                "provider_id": "anthropic_compatible",
                "auth_token": "relay-token",
                "base_url": "https://relay.example.invalid",
                "provider_enabled": True,
                "enabled_models": ["claude-sonnet-4.5"],
                "model_detections": {
                    "claude-sonnet-4.5": {
                        "status": "verified",
                        "message": "模型检测通过",
                        "checked_at": "2026-04-17T10:00:00",
                    }
                },
                "supports_partial_messages": True,
            }
        },
        {
            "anthropic_compatible": {
                "provider_id": "anthropic_compatible",
                "supports_partial_messages": False,
            }
        },
    )

    provider = merged["anthropic_compatible"]
    assert provider["supports_partial_messages"] is False
    assert provider["validation_status"] == "verified"
    assert provider["enabled"] is True


def test_merge_provider_settings_requires_verified_model_detection():
    merged = _merge_provider_settings(
        {},
        {
            "openrouter": {
                "provider_id": "openrouter",
                "provider_enabled": True,
                "auth_token": "token",
                "base_url": "https://openrouter.ai/api",
                "enabled_models": ["anthropic/claude-sonnet-4.5"],
                "model_detections": {},
            }
        },
    )

    provider = merged["openrouter"]
    assert provider["enabled_models"] == []
    assert provider["validation_status"] == "unverified"
    assert provider["enabled"] is False


def test_merge_settings_payload_keeps_provider_and_model_empty_without_enabled_provider():
    merged = _merge_settings_payload(
        {
            "provider_id": "",
            "model": "",
            "skills_output_dir": "../.claude/skills/dataagent-nl2sql",
            "session_mysql_database": "dataagent",
        },
        {},
    )

    assert merged["provider_id"] == ""
    assert merged["model"] == ""
    assert merged["validated_provider_id"] == ""
    assert merged["validated_model"] == ""


def test_bootstrap_admin_settings_persists_blank_provider_and_model(monkeypatch):
    captured = {}

    class FakeStore:
        def init_schema(self):
            return None

        def load_settings_record(self):
            return None

        def save_settings_record(self, payload):
            captured["saved"] = dict(payload)
            return dict(payload)

    monkeypatch.setattr(skill_admin_service, "get_skill_admin_store", lambda: FakeStore())
    monkeypatch.setattr(
        skill_admin_service,
        "get_settings",
        lambda: types.SimpleNamespace(
            llm_provider="",
            claude_model="",
            anthropic_api_key="",
            anthropic_auth_token="",
            anthropic_base_url="",
            mysql_host="",
            mysql_port=3306,
            mysql_user="",
            mysql_password="",
            mysql_database="",
            doris_host="",
            doris_port=9030,
            doris_user="",
            doris_password="",
            doris_database="",
            skills_output_dir="../.claude/skills/dataagent-nl2sql",
            session_mysql_database="dataagent",
        ),
    )
    monkeypatch.setattr(skill_admin_service, "update_settings", lambda patch: patch)

    resolved = skill_admin_service.bootstrap_admin_settings()

    assert captured["saved"]["provider_id"] == ""
    assert captured["saved"]["model"] == ""
    assert resolved["provider_id"] == ""
    assert resolved["model"] == ""


def test_resolve_runtime_provider_selection_returns_partial_capability(monkeypatch):
    monkeypatch.setattr(
        skill_admin_service,
        "current_settings_payload",
        lambda: {
            "provider_id": "anthropic_compatible",
            "model": "claude-sonnet-4.5",
            "provider_settings": {
                "anthropic_compatible": {
                    "provider_id": "anthropic_compatible",
                    "provider_enabled": True,
                    "auth_token": "relay-token",
                    "base_url": "https://relay.example.invalid",
                    "enabled_models": ["claude-sonnet-4.5"],
                    "model_detections": {
                        "claude-sonnet-4.5": {
                            "status": "verified",
                            "message": "模型检测通过",
                            "checked_at": "2026-04-17T10:00:00",
                        }
                    },
                    "supports_partial_messages": False,
                }
            },
        },
    )

    resolved = skill_admin_service.resolve_runtime_provider_selection("anthropic_compatible", "claude-sonnet-4.5")
    assert resolved["provider_id"] == "anthropic_compatible"
    assert resolved["model"] == "claude-sonnet-4.5"
    assert resolved["supports_partial_messages"] is False


def test_resolve_runtime_provider_selection_requires_enabled_provider(monkeypatch):
    monkeypatch.setattr(
        skill_admin_service,
        "current_settings_payload",
        lambda: {
            "provider_id": "",
            "model": "",
            "provider_settings": {},
        },
    )

    try:
        skill_admin_service.resolve_runtime_provider_selection(None, None)
    except ValueError as exc:
        assert str(exc) == "尚未配置可用大模型供应商"
    else:
        raise AssertionError("expected ValueError")


def test_detect_model_availability_returns_verified_detection(monkeypatch):
    captured = {}

    class FakeOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    async def fake_query(prompt, options):
        captured["prompt"] = prompt
        captured["options"] = options.kwargs
        yield types.SimpleNamespace(subtype="")

    monkeypatch.setitem(
        sys.modules,
        "claude_agent_sdk",
        types.SimpleNamespace(ClaudeAgentOptions=FakeOptions, query=fake_query),
    )
    monkeypatch.setattr(skill_admin_service, "resolve_agent_project_cwd", lambda: Path("/tmp"))
    monkeypatch.setattr(
        skill_admin_service,
        "current_settings_payload",
        lambda: {
            "provider_id": "openrouter",
            "model": "",
            "provider_settings": {
                "openrouter": {
                    "provider_id": "openrouter",
                    "provider_enabled": True,
                    "auth_token": "saved-token",
                    "base_url": "https://openrouter.ai/api",
                    "enabled_models": [],
                    "custom_models": [],
                    "model_detections": {},
                }
            },
        },
    )

    result = anyio.run(
        skill_admin_service.detect_model_availability,
        {
            "provider_id": "openrouter",
            "model": "anthropic/claude-sonnet-4.5",
        },
    )

    assert result["status"] == "verified"
    assert captured["options"]["model"] == "anthropic/claude-sonnet-4.5"


def test_detect_model_availability_returns_failed_without_token(monkeypatch):
    monkeypatch.setattr(
        skill_admin_service,
        "current_settings_payload",
        lambda: {
            "provider_id": "openrouter",
            "model": "",
            "provider_settings": {
                "openrouter": {
                    "provider_id": "openrouter",
                    "provider_enabled": True,
                    "auth_token": "",
                    "base_url": "https://openrouter.ai/api",
                    "enabled_models": [],
                    "custom_models": [],
                    "model_detections": {},
                }
            },
        },
    )

    result = anyio.run(
        skill_admin_service.detect_model_availability,
        {
            "provider_id": "openrouter",
            "model": "anthropic/claude-sonnet-4.5",
        },
    )

    assert result["status"] == "failed"
    assert "Token" in result["message"]
