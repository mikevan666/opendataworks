from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core import skill_admin_service
from core.skill_admin_service import _merge_provider_settings


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
