"""Common Amap API client for future business commands."""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from amap_cli import __version__
from amap_cli.config import AmapConfig, load_config
from amap_cli.errors import ApiRequestError, ApiResponseError, MissingConfigError


class AmapApiClient:
    """HTTP client that injects config and normalizes Amap failures."""

    def __init__(self, config: AmapConfig | None = None) -> None:
        self.config = config or load_config(required=True)
        if self.config is None or not self.config.api_key:
            raise MissingConfigError(
                "缺少高德 API Key，请先执行 `amap-cli config set --api-key <KEY>`。"
            )

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a GET request to the Amap REST API."""
        query_params = dict(params or {})
        query_params["key"] = self.config.api_key

        url = self._build_url(path, query_params)
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": f"amap-cli/{__version__}",
            },
            method="GET",
        )

        try:
            try:
                with urlopen(request, timeout=self.config.timeout_seconds) as response:
                    body = response.read().decode("utf-8")
            except HTTPError as exc:
                response_body = exc.read().decode("utf-8", errors="ignore")
                raise ApiRequestError(
                    f"高德 API HTTP 请求失败：{exc.code}",
                    details={"status": exc.code, "body": response_body},
                ) from exc
            except URLError as exc:
                raise ApiRequestError(
                    "无法连接高德 API。",
                    details={"reason": str(exc.reason)},
                ) from exc
            except TimeoutError as exc:
                raise ApiRequestError("请求高德 API 超时。") from exc

            try:
                payload = json.loads(body)
            except json.JSONDecodeError as exc:
                raise ApiRequestError(
                    "高德 API 返回了非 JSON 响应。",
                    details={"body": body[:500]},
                ) from exc

            self._raise_for_amap_error(payload)
            return payload
        finally:
            if self.config.request_sleep_seconds > 0:
                time.sleep(self.config.request_sleep_seconds)

    def _build_url(self, path: str, params: dict[str, Any]) -> str:
        """Build a full request URL from config and query params."""
        normalized_path = path if path.startswith("/") else f"/{path}"
        query = urlencode(params, doseq=True)
        return f"{self.config.base_url.rstrip('/')}{normalized_path}?{query}"

    def _raise_for_amap_error(self, payload: dict[str, Any]) -> None:
        """Convert business-level Amap error payloads to exceptions."""
        status = payload.get("status")
        if status is None:
            return

        if str(status) == "1":
            return

        raise ApiResponseError(
            payload.get("info") or "高德 API 返回失败。",
            details={
                "infocode": payload.get("infocode"),
                "info": payload.get("info"),
            },
        )
