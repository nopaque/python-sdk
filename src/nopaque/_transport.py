"""Shared HTTP transport for sync + async clients.

Owns: URL composition, auth header injection, User-Agent, JSON (de)serialization,
error classification, per-request timeouts, and retry orchestration.

Retry logic itself lives in _retry.py and is added in a subsequent task.
"""
from __future__ import annotations

import json as jsonlib
from typing import Any, Dict, Optional

import httpx

from ._config import NopaqueConfig
from ._errors import (
    APIConnectionError,
    APITimeoutError,
    NopaqueAPIError,
    RateLimitError,
    classify_status,
)
from ._request_options import RequestOptions, merge_options
from ._user_agent import compose_user_agent


def _merge_headers(
    config: NopaqueConfig, options: Optional[RequestOptions]
) -> Dict[str, str]:
    headers: Dict[str, str] = {
        "x-api-key": config.api_key,
        "user-agent": compose_user_agent(),
        "accept": "application/json",
    }
    if config.default_headers:
        headers.update(config.default_headers)
    if options and options.get("headers"):
        headers.update(options["headers"])  # type: ignore[arg-type]
    return headers


def _build_url(config: NopaqueConfig, path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{config.base_url}{path}"


def _raise_for_status(response: httpx.Response) -> None:
    """Map a non-2xx response to the appropriate typed exception."""
    if 200 <= response.status_code < 300:
        return
    try:
        body = response.json()
    except (ValueError, jsonlib.JSONDecodeError):
        body = {}
    error_message = body.get("error") if isinstance(body, dict) else None
    code = body.get("code") if isinstance(body, dict) else None
    details = body.get("details") if isinstance(body, dict) else None
    request_id = response.headers.get("x-request-id")

    cls = classify_status(response.status_code)
    if cls is RateLimitError:
        retry_after_raw = response.headers.get("retry-after")
        retry_after: Optional[float] = None
        if retry_after_raw is not None:
            try:
                retry_after = float(retry_after_raw)
            except ValueError:
                retry_after = None
        raise RateLimitError(
            status=response.status_code,
            code=code,
            message=error_message or "rate limit exceeded",
            details=details,
            request_id=request_id,
            response=response,
            retry_after=retry_after,
        )
    raise cls(
        status=response.status_code,
        code=code,
        message=error_message or f"HTTP {response.status_code}",
        details=details,
        request_id=request_id,
        response=response,
    )


class SyncTransport:
    """Synchronous HTTP transport."""

    def __init__(
        self, config: NopaqueConfig, *, http_client: Optional[httpx.Client] = None
    ) -> None:
        self._config = config
        self._client = http_client or httpx.Client(timeout=config.timeout)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        json: Any = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Any:
        headers = _merge_headers(self._config, request_options)
        url = _build_url(self._config, path)
        opts = merge_options(None, request_options)
        timeout = opts.get("timeout", self._config.timeout)

        try:
            response = self._client.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers,
                timeout=timeout,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(str(e)) from e
        except httpx.HTTPError as e:
            raise APIConnectionError(str(e), cause=e) from e

        _raise_for_status(response)

        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SyncTransport":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()


class AsyncTransport:
    """Asynchronous HTTP transport."""

    def __init__(
        self,
        config: NopaqueConfig,
        *,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._config = config
        self._client = http_client or httpx.AsyncClient(timeout=config.timeout)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        json: Any = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Any:
        headers = _merge_headers(self._config, request_options)
        url = _build_url(self._config, path)
        opts = merge_options(None, request_options)
        timeout = opts.get("timeout", self._config.timeout)

        try:
            response = await self._client.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers,
                timeout=timeout,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(str(e)) from e
        except httpx.HTTPError as e:
            raise APIConnectionError(str(e), cause=e) from e

        _raise_for_status(response)

        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncTransport":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.aclose()
