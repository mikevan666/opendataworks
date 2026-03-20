from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    value = str(os.getenv(name, "")).strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    backend_base_url: str
    backend_service_token: str
    backend_token_header_name: str
    backend_timeout_seconds: int
    frontdoor_token: str
    frontdoor_token_header_name: str
    host: str
    port: int
    mcp_mount_path: str


def load_settings() -> Settings:
    backend_base_url = str(
        os.getenv("PORTAL_MCP_BACKEND_BASE_URL", "http://backend:8080/api")
    ).strip().rstrip("/")
    return Settings(
        backend_base_url=backend_base_url,
        backend_service_token=str(os.getenv("PORTAL_MCP_BACKEND_SERVICE_TOKEN", "")).strip(),
        backend_token_header_name=str(
            os.getenv("PORTAL_MCP_BACKEND_TOKEN_HEADER_NAME", "X-Agent-Service-Token")
        ).strip()
        or "X-Agent-Service-Token",
        backend_timeout_seconds=max(1, _env_int("PORTAL_MCP_BACKEND_TIMEOUT_SECONDS", 30)),
        frontdoor_token=str(os.getenv("PORTAL_MCP_FRONTDOOR_TOKEN", "")).strip(),
        frontdoor_token_header_name=str(
            os.getenv("PORTAL_MCP_FRONTDOOR_TOKEN_HEADER_NAME", "X-Portal-MCP-Token")
        ).strip()
        or "X-Portal-MCP-Token",
        host=str(os.getenv("PORTAL_MCP_HOST", "0.0.0.0")).strip() or "0.0.0.0",
        port=max(1, _env_int("PORTAL_MCP_PORT", 8801)),
        mcp_mount_path=str(os.getenv("PORTAL_MCP_MOUNT_PATH", "/mcp")).strip() or "/mcp",
    )
