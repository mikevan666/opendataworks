from __future__ import annotations

from typing import Any

from .backend_client import BackendApiClient, BackendApiError


class PortalToolService:
    def __init__(self, backend_client: BackendApiClient):
        self.backend_client = backend_client

    async def search_tables(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._wrap(self.backend_client.inspect(**payload))

    async def get_lineage(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._wrap(self.backend_client.lineage(**payload))

    async def resolve_datasource(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._wrap(self.backend_client.resolve_datasource(**payload))

    async def export_metadata(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        return await self._wrap(self.backend_client.export_metadata(**payload))

    async def get_table_ddl(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._wrap(self.backend_client.get_table_ddl(**payload))

    async def query_readonly(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._wrap(self.backend_client.query_readonly(payload))

    async def _wrap(self, awaitable):
        try:
            return await awaitable
        except BackendApiError as exc:
            raise RuntimeError(str(exc)) from exc
