import pytest
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque
from nopaque._errors import NopaqueConfigError


def test_nopaque_constructor_missing_key(monkeypatch):
    monkeypatch.delenv("NOPAQUE_API_KEY", raising=False)
    with pytest.raises(NopaqueConfigError):
        Nopaque()


def test_nopaque_context_manager(httpx_mock: HTTPXMock):
    with Nopaque(api_key="k") as client:
        assert client.config.api_key == "k"


def test_nopaque_resources_attached():
    client = Nopaque(api_key="k")
    # Sanity check: the namespaces exist even if no methods yet.
    assert hasattr(client, "mapping")
    assert hasattr(client, "audio")
    assert hasattr(client, "profiles")
    assert hasattr(client, "testing")
    assert hasattr(client, "batches")
    assert hasattr(client, "sweeps")
    assert hasattr(client, "datasets")
    assert hasattr(client, "load_testing")
    assert hasattr(client, "scheduler")
    assert hasattr(client, "enrichment")
    client.close()


@pytest.mark.asyncio
async def test_async_nopaque_resources_attached():
    client = AsyncNopaque(api_key="k")
    assert hasattr(client, "mapping")
    assert hasattr(client, "audio")
    await client.aclose()
