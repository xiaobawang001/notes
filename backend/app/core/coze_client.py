"""Coze API HTTP 客户端：封装 Coze 多维表格 REST API"""
import json
import time
from typing import Optional, Any

import httpx

from app.core.config import get_settings


class CozeApiError(Exception):
    """Coze API 调用异常"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"[Coze {status_code}] {message}")


class CozeApiClient:
    """异步 Coze API 客户端，用于操作 Coze 多维表格（users / notes）"""

    def __init__(self):
        settings = get_settings()
        self._token = settings.COZE_TOKEN
        self._base_url = settings.COZE_BASE_URL.rstrip("/")
        self._logging = settings.COZE_API_LOGGING
        self._http = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self._http.aclose()

    async def _request(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        """统一请求入口，带日志和错误处理"""
        url = f"{self._base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        start = time.monotonic()
        if self._logging:
            print(f"[Coze API Request] {method} {url}", json.dumps(body or {}))

        resp = await self._http.request(method, url, headers=headers, json=body)
        data = resp.json()
        elapsed = (time.monotonic() - start) * 1000
        if self._logging:
            print(f"[Coze API Response] {resp.status_code} ({elapsed:.0f}ms)",
                  json.dumps(data, ensure_ascii=False)[:2000])

        if resp.status_code >= 400 or data.get("code") != 0:
            raise CozeApiError(
                status_code=resp.status_code,
                message=data.get("msg") or f"Coze API error: {resp.status_code}"
            )
        return data.get("data") or data

    # ── 查询 ──
    async def query(self, database_id: str, body: dict) -> dict:
        """POST /v1/databases/{id}/records/query"""
        full_body = {"is_async": False, "page_num": 1, "page_size": 500, **body}
        return await self._request("POST", f"/v1/databases/{database_id}/records/query", full_body)

    # ── 插入 ──
    async def insert(self, database_id: str, body: dict) -> dict:
        """POST /v1/databases/{id}/records"""
        full_body = {"is_async": False, **body}
        return await self._request("POST", f"/v1/databases/{database_id}/records", full_body)

    # ── 更新 ──
    async def update(self, database_id: str, body: dict) -> dict:
        """PUT /v1/databases/{id}/records"""
        full_body = {"is_async": False, **body}
        return await self._request("PUT", f"/v1/databases/{database_id}/records", full_body)

    # ── 删除 ──
    async def delete(self, database_id: str, body: dict) -> dict:
        """DELETE /v1/databases/{id}/records"""
        full_body = {"is_async": False, **body}
        return await self._request("DELETE", f"/v1/databases/{database_id}/records", full_body)


# 全局单例
coze_client: Optional[CozeApiClient] = None


async def get_coze_client() -> CozeApiClient:
    global coze_client
    if coze_client is None:
        coze_client = CozeApiClient()
    return coze_client
