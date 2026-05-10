"""Top-level Nopaque and AsyncNopaque clients."""
from __future__ import annotations

from typing import Any, Callable

import httpx

from ._config import NopaqueConfig
from ._transport import AsyncTransport, SyncTransport
from .resources.audio import AsyncAudioResource, AudioResource
from .resources.batches import AsyncBatchesResource, BatchesResource
from .resources.datasets import AsyncDatasetsResource, DatasetsResource
from .resources.enrichment import AsyncEnrichmentResource, EnrichmentResource
from .resources.load_testing import AsyncLoadTestingResource, LoadTestingResource
from .resources.mapping import AsyncMappingResource, MappingResource
from .resources.mission_test_configs import (
    AsyncMissionTestConfigsResource,
    MissionTestConfigsResource,
)
from .resources.mission_tests import AsyncMissionTestsResource, MissionTestsResource
from .resources.profiles import AsyncProfilesResource, ProfilesResource
from .resources.scheduler import AsyncSchedulerResource, SchedulerResource
from .resources.sweeps import AsyncSweepsResource, SweepsResource
from .resources.testing import AsyncTestingResource, TestingResource


class Nopaque:
    """Synchronous Nopaque API client."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        default_headers: dict | None = None,
        on_retry: Callable[[int, Any, float], None] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.config = NopaqueConfig(
            api_key=api_key or "",
            base_url=base_url or "",
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers or {},
            on_retry=on_retry,
        )
        self._transport = SyncTransport(self.config, http_client=http_client)
        self.mapping = MappingResource(self._transport)
        self.audio = AudioResource(self._transport)
        self.profiles = ProfilesResource(self._transport)
        self.testing = TestingResource(self._transport)
        self.batches = BatchesResource(self._transport)
        self.sweeps = SweepsResource(self._transport)
        self.datasets = DatasetsResource(self._transport)
        self.load_testing = LoadTestingResource(self._transport)
        self.scheduler = SchedulerResource(self._transport)
        self.enrichment = EnrichmentResource(self._transport)
        self.mission_tests = MissionTestsResource(self._transport)
        self.mission_test_configs = MissionTestConfigsResource(self._transport)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> Nopaque:
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()


class AsyncNopaque:
    """Asynchronous Nopaque API client."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        default_headers: dict | None = None,
        on_retry: Callable[[int, Any, float], None] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = NopaqueConfig(
            api_key=api_key or "",
            base_url=base_url or "",
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers or {},
            on_retry=on_retry,
        )
        self._transport = AsyncTransport(self.config, http_client=http_client)
        self.mapping = AsyncMappingResource(self._transport)
        self.audio = AsyncAudioResource(self._transport)
        self.profiles = AsyncProfilesResource(self._transport)
        self.testing = AsyncTestingResource(self._transport)
        self.batches = AsyncBatchesResource(self._transport)
        self.sweeps = AsyncSweepsResource(self._transport)
        self.datasets = AsyncDatasetsResource(self._transport)
        self.load_testing = AsyncLoadTestingResource(self._transport)
        self.scheduler = AsyncSchedulerResource(self._transport)
        self.enrichment = AsyncEnrichmentResource(self._transport)
        self.mission_tests = AsyncMissionTestsResource(self._transport)
        self.mission_test_configs = AsyncMissionTestConfigsResource(self._transport)

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> AsyncNopaque:
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.aclose()
