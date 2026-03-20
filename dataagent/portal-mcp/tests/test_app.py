from __future__ import annotations

import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from portal_mcp.app import create_app
from portal_mcp.backend_client import BackendApiError
from portal_mcp.config import Settings
from portal_mcp.service import PortalToolService


class FakeBackendClient:
    async def inspect(self, **params):
        return {"kind": "metadata_snapshot", "database": params.get("database"), "table_count": 1, "tables": []}

    async def lineage(self, **params):
        return {"kind": "lineage_snapshot", "table": params.get("table"), "lineage": []}

    async def resolve_datasource(self, **params):
        return {"engine": "mysql", "database": params.get("database")}

    async def export_metadata(self, **params):
        return [{"kind": params.get("kind"), "db_name": params.get("database")}]

    async def get_table_ddl(self, **params):
        return {"kind": "table_ddl", "database": params.get("database"), "ddl": "CREATE TABLE demo (...)"}

    async def query_readonly(self, payload):
        return {"kind": "query_result", "database": payload.get("database"), "rows": [{"value": 1}], "row_count": 1}


class FailingBackendClient(FakeBackendClient):
    async def query_readonly(self, payload):
        raise BackendApiError("backend rejected query", status_code=400)


def _settings() -> Settings:
    return Settings(
        backend_base_url="http://backend:8080/api",
        backend_service_token="service-token",
        backend_token_header_name="X-Agent-Service-Token",
        backend_timeout_seconds=30,
        frontdoor_token="portal-token",
        frontdoor_token_header_name="X-Portal-MCP-Token",
        host="0.0.0.0",
        port=8801,
        mcp_mount_path="/mcp",
    )


def test_health_does_not_require_frontdoor_token():
    app = create_app(settings=_settings(), backend_client=FakeBackendClient())
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_mcp_path_rejects_missing_frontdoor_token():
    app = create_app(settings=_settings(), backend_client=FakeBackendClient())
    with TestClient(app) as client:
        response = client.post("/mcp", json={})

    assert response.status_code == 401
    assert response.json()["message"] == "portal mcp token 无效"


def test_mcp_path_accepts_valid_frontdoor_token():
    app = create_app(settings=_settings(), backend_client=FakeBackendClient())
    with TestClient(app) as client:
        response = client.post("/mcp", headers={"X-Portal-MCP-Token": "portal-token"}, json={})

    assert response.status_code != 401


@pytest.mark.anyio
async def test_all_tool_service_methods_return_backend_shapes():
    service = PortalToolService(FakeBackendClient())

    search = await service.search_tables({"database": "opendataworks", "table": "workflow_publish_record"})
    lineage = await service.get_lineage({"table": "ads_sales_di"})
    datasource = await service.resolve_datasource({"database": "opendataworks"})
    exported = await service.export_metadata({"kind": "tables", "database": "opendataworks"})
    ddl = await service.get_table_ddl({"database": "opendataworks", "table": "workflow_publish_record"})
    query = await service.query_readonly({"database": "opendataworks", "sql": "SELECT 1"})

    assert search["kind"] == "metadata_snapshot"
    assert lineage["kind"] == "lineage_snapshot"
    assert datasource["engine"] == "mysql"
    assert exported[0]["kind"] == "tables"
    assert ddl["kind"] == "table_ddl"
    assert query["kind"] == "query_result"
    assert query["row_count"] == 1


@pytest.mark.anyio
async def test_backend_error_is_mapped_to_runtime_error():
    service = PortalToolService(FailingBackendClient())

    with pytest.raises(RuntimeError, match="backend rejected query"):
        await service.query_readonly({"database": "opendataworks", "sql": "SELECT 1"})
