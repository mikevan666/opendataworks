from __future__ import annotations

import sys
import types
from pathlib import Path

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
            "enabled_models": [],
            "custom_models": [],
            "enabled": False,
            "validation_status": "unverified",
            "validation_message": "请至少开启一个模型",
        }
    }
    patch = {
        "anyrouter": {
            "provider_id": "anyrouter",
            "auth_token": "existing-token",
            "base_url": "https://a-ocnfniawgw.cn-shanghai.fcapp.run",
            "enabled_models": ["claude-opus-4-6"],
            "custom_models": [],
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
                "enabled_models": ["claude-sonnet-4.5"],
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
                    "auth_token": "relay-token",
                    "base_url": "https://relay.example.invalid",
                    "enabled_models": ["claude-sonnet-4.5"],
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
