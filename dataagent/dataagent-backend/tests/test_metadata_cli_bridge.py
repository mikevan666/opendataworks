from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS_ROOT = BACKEND_ROOT.parent / ".claude" / "skills" / "dataagent-nl2sql" / "scripts"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _load_runtime_module():
    module_path = SKILL_SCRIPTS_ROOT / "_opendataworks_runtime.py"
    spec = importlib.util.spec_from_file_location("dataagent_odw_runtime", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_resolve_datasource_uses_backend_cli(monkeypatch):
    runtime = _load_runtime_module()
    captured = {}

    def fake_call_metadata_cli(subcommand, **options):
        captured["subcommand"] = subcommand
        captured["options"] = options
        return {
            "engine": "doris",
            "database": "doris_ods",
            "host": "doris-fe",
            "port": 9030,
            "user": "readonly_user",
            "password": "readonly_pass",
            "source_type": "DORIS",
            "cluster_id": 8,
            "cluster_name": "cluster-a",
            "resolved_by": "readonly_user",
        }

    monkeypatch.setattr(runtime, "call_metadata_cli", fake_call_metadata_cli)

    result = runtime.resolve_datasource("doris_ods", preferred_engine="doris")

    assert captured["subcommand"] == "resolve-datasource"
    assert captured["options"]["database"] == "doris_ods"
    assert captured["options"]["preferred_engine"] == "doris"
    assert result["cluster_id"] == 8
    assert result["resolved_by"] == "readonly_user"


def test_call_metadata_cli_rejects_invalid_json(monkeypatch):
    runtime = _load_runtime_module()

    def fake_run(command, check, capture_output, text):
        return SimpleNamespace(returncode=0, stdout="not-json", stderr="")

    monkeypatch.setattr(runtime.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="不是合法 JSON"):
        runtime.call_metadata_cli("inspect", keyword="工作流")


def test_call_metadata_cli_surfaces_non_zero_exit(monkeypatch):
    runtime = _load_runtime_module()

    def fake_run(command, check, capture_output, text):
        return SimpleNamespace(returncode=22, stdout="", stderr="agent api token 无效")

    monkeypatch.setattr(runtime.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="agent api token 无效"):
        runtime.call_metadata_cli("export", kind="tables")


def test_metadata_cli_bin_defaults_to_bundled_skill_cli(monkeypatch):
    runtime = _load_runtime_module()
    monkeypatch.delenv("DATAAGENT_SKILL_ROOT", raising=False)

    cli_path = Path(runtime.metadata_cli_bin())

    assert cli_path.name == "odw-cli"
    assert cli_path.parent.name == "bin"
    assert str(cli_path) == str(SKILL_SCRIPTS_ROOT.parent / "bin" / "odw-cli")


def test_call_metadata_cli_non_executable_bin_falls_back_to_sh(monkeypatch):
    runtime = _load_runtime_module()
    cli_path = Path(runtime.metadata_cli_bin())
    captured = {}

    def fake_access(path, mode):
        if Path(path) == cli_path and mode == runtime.os.X_OK:
            return False
        return os.access(path, mode)

    def fake_run(command, check, capture_output, text):
        captured["command"] = command
        return SimpleNamespace(returncode=0, stdout='{"kind":"ok"}', stderr="")

    monkeypatch.setattr(runtime.os, "access", fake_access)
    monkeypatch.setattr(runtime.subprocess, "run", fake_run)

    payload = runtime.call_metadata_cli("inspect", keyword="工作流")

    assert payload == {"kind": "ok"}
    assert captured["command"][:3] == ["sh", str(cli_path), "inspect"]
    assert captured["command"][3:] == ["--keyword", "工作流"]


def test_call_metadata_cli_missing_binary_requires_user_install(monkeypatch):
    runtime = _load_runtime_module()
    missing_path = SKILL_SCRIPTS_ROOT.parent / "bin" / "missing-odw-cli"

    monkeypatch.setattr(runtime, "metadata_cli_bin", lambda: str(missing_path))

    with pytest.raises(RuntimeError, match="请先由用户自行安装到该路径后再重试"):
        runtime.call_metadata_cli("inspect", keyword="工作流")
