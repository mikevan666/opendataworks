from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


def skills_root_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def metadata_cli_bin() -> str:
    override = str(os.getenv("ODW_CLI_BIN", "")).strip()
    if override:
        return override
    return str(skills_root_dir() / "bin" / "odw-cli")


def metadata_cli_command(subcommand: str, **options: Any) -> list[str]:
    cli_path = Path(metadata_cli_bin())
    if not cli_path.is_file():
        raise RuntimeError(
            f"odw-cli 不存在: {cli_path}。请先同步根 skills 并保证 CLI 已镜像到运行环境。"
        )

    command = [str(cli_path)] if os.access(cli_path, os.X_OK) else ["sh", str(cli_path)]
    command.append(str(subcommand).strip())

    for key, value in options.items():
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        command.extend([f"--{str(key).replace('_', '-')}", text])

    return command


def call_metadata_cli(subcommand: str, **options: Any) -> Any:
    command = metadata_cli_command(subcommand, **options)
    cli_path = metadata_cli_bin()
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except PermissionError as exc:
        if command[:1] == ["sh"]:
            raise RuntimeError(
                f"odw-cli 不可执行: {cli_path}。请先修正权限或挂载策略。"
            ) from exc
        completed = subprocess.run(
            ["sh", cli_path, *command[1:]],
            check=False,
            capture_output=True,
            text=True,
        )

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(detail or f"odw-cli 执行失败: {' '.join(command[:2])}")

    raw_output = str(completed.stdout or "").strip()
    if not raw_output:
        raise RuntimeError("odw-cli 未返回 JSON")
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise RuntimeError("odw-cli 返回的不是合法 JSON") from exc


def serializable_value(value: Any) -> Any:
    if value is None or isinstance(value, (int, float, str, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def serializable_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {str(key): serializable_value(val) for key, val in dict(row).items()}
        for row in rows
    ]


def print_json(payload: dict[str, Any]):
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def error_payload(kind: str, message: str, **extra: Any) -> dict[str, Any]:
    payload = {"kind": kind, "error": message}
    payload.update(extra)
    return payload


def repo_python_bin() -> str:
    override = str(os.getenv("ODW_PYTHON_BIN", "")).strip()
    if override:
        return override
    return sys.executable
