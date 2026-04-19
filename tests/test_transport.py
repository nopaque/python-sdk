import httpx
import pytest
from pytest_httpx import HTTPXMock

from nopaque._config import NopaqueConfig
from nopaque._transport import SyncTransport, AsyncTransport
from nopaque._errors import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    ServerError,
    APIConnectionError,
    APITimeoutError,
)


def make_config(**kw):
    return NopaqueConfig(api_key="nop_live_test", **kw)


def test_sync_get_sends_api_key_header(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/m_1",
        json={"id": "m_1", "name": "Main IVR"},
    )
    t = SyncTransport(make_config())
    data = t.request("GET", "/mapping/m_1")
    assert data == {"id": "m_1", "name": "Main IVR"}
    req = httpx_mock.get_requests()[0]
    assert req.headers["x-api-key"] == "nop_live_test"
    assert req.headers["user-agent"].startswith("nopaque-python/")
    t.close()


def test_sync_404_raises_not_found(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/none",
        status_code=404,
        json={"error": "not found", "code": "mapping_not_found"},
    )
    t = SyncTransport(make_config(max_retries=0))
    with pytest.raises(NotFoundError) as ei:
        t.request("GET", "/mapping/none")
    assert ei.value.status == 404
    assert ei.value.code == "mapping_not_found"
    t.close()


def test_sync_429_parses_retry_after_header(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping",
        status_code=429,
        headers={"retry-after": "7"},
        json={"error": "rate limited"},
    )
    t = SyncTransport(make_config(max_retries=0))
    with pytest.raises(RateLimitError) as ei:
        t.request("GET", "/mapping")
    assert ei.value.retry_after == 7.0
    t.close()


def test_sync_unknown_status_falls_back_to_api_error(httpx_mock: HTTPXMock):
    from nopaque._errors import NopaqueAPIError
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/x",
        status_code=418,
        json={"error": "teapot"},
    )
    t = SyncTransport(make_config(max_retries=0))
    with pytest.raises(NopaqueAPIError):
        t.request("GET", "/x")
    t.close()


def test_sync_connection_error_raises_api_connection_error(monkeypatch):
    def boom(*a, **kw):
        raise httpx.ConnectError("nope")
    t = SyncTransport(make_config(max_retries=0))
    monkeypatch.setattr(t._client, "request", boom)
    with pytest.raises(APIConnectionError):
        t.request("GET", "/mapping")
    t.close()


def test_sync_timeout_error_raises_timeout(monkeypatch):
    def slow(*a, **kw):
        raise httpx.TimeoutException("slow")
    t = SyncTransport(make_config(max_retries=0))
    monkeypatch.setattr(t._client, "request", slow)
    with pytest.raises(APITimeoutError):
        t.request("GET", "/mapping")
    t.close()


def test_sync_custom_default_header_sent(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url="https://api.nopaque.co.uk/x", json={})
    t = SyncTransport(make_config(default_headers={"X-Source": "worker"}))
    t.request("GET", "/x")
    req = httpx_mock.get_requests()[0]
    assert req.headers["x-source"] == "worker"
    t.close()


def test_sync_per_call_header_override(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url="https://api.nopaque.co.uk/x", json={})
    t = SyncTransport(make_config())
    t.request("GET", "/x", request_options={"headers": {"X-Trace": "abc"}})
    req = httpx_mock.get_requests()[0]
    assert req.headers["x-trace"] == "abc"
    t.close()


@pytest.mark.asyncio
async def test_async_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/m_1", json={"id": "m_1"}
    )
    t = AsyncTransport(make_config())
    data = await t.request("GET", "/mapping/m_1")
    assert data == {"id": "m_1"}
    await t.aclose()


@pytest.mark.asyncio
async def test_async_404_raises(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/x", status_code=404, json={"error": "x"}
    )
    t = AsyncTransport(make_config(max_retries=0))
    with pytest.raises(NotFoundError):
        await t.request("GET", "/x")
    await t.aclose()
