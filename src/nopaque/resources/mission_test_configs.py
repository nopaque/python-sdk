"""Mission test configs resource - all /testing/mission-test-configs endpoints."""
from __future__ import annotations

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.mission_test_configs import (
    CreateMissionTestConfigRequest,
    MissionTestConfig,
)
from ..models.mission_tests import MissionTestRun


class MissionTestConfigsResource(SyncResource):
    """Synchronous /testing/mission-test-configs endpoints."""

    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[MissionTestConfig]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET",
                "/testing/mission-test-configs",
                params=p,
                request_options=request_options,
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=MissionTestConfig)

    def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[MissionTestConfig]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET",
            "/testing/mission-test-configs",
            params=params,
            request_options=request_options,
        )
        items = [MissionTestConfig.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    def create(
        self,
        *,
        name: str,
        sector: str,
        mission: str,
        acceptance: str,
        profile_id: str,
        request_options: RequestOptions | None = None,
    ) -> MissionTestConfig:
        body = CreateMissionTestConfigRequest(
            name=name,
            sector=sector,
            mission=mission,
            acceptance=acceptance,
            profile_id=profile_id,
        ).model_dump(by_alias=True, exclude_none=True)
        raw = self._transport.request(
            "POST",
            "/testing/mission-test-configs",
            json=body,
            request_options=request_options,
        )
        return MissionTestConfig.model_validate(raw)

    def get(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> MissionTestConfig:
        raw = self._transport.request(
            "GET",
            f"/testing/mission-test-configs/{config_id}",
            request_options=request_options,
        )
        return MissionTestConfig.model_validate(raw)

    def delete(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        self._transport.request(
            "DELETE",
            f"/testing/mission-test-configs/{config_id}",
            request_options=request_options,
        )

    def run(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> MissionTestRun:
        """Launch a mission test run from a saved config.

        The returned run is freeform-shaped.
        """
        raw = self._transport.request(
            "POST",
            f"/testing/mission-test-configs/{config_id}/runs",
            request_options=request_options,
        )
        return MissionTestRun.model_validate(raw)


class AsyncMissionTestConfigsResource(AsyncResource):
    """Asynchronous /testing/mission-test-configs endpoints."""

    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[MissionTestConfig]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET",
                "/testing/mission-test-configs",
                params=p,
                request_options=request_options,
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=MissionTestConfig)

    async def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[MissionTestConfig]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET",
            "/testing/mission-test-configs",
            params=params,
            request_options=request_options,
        )
        items = [MissionTestConfig.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def create(
        self,
        *,
        name: str,
        sector: str,
        mission: str,
        acceptance: str,
        profile_id: str,
        request_options: RequestOptions | None = None,
    ) -> MissionTestConfig:
        body = CreateMissionTestConfigRequest(
            name=name,
            sector=sector,
            mission=mission,
            acceptance=acceptance,
            profile_id=profile_id,
        ).model_dump(by_alias=True, exclude_none=True)
        raw = await self._transport.request(
            "POST",
            "/testing/mission-test-configs",
            json=body,
            request_options=request_options,
        )
        return MissionTestConfig.model_validate(raw)

    async def get(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> MissionTestConfig:
        raw = await self._transport.request(
            "GET",
            f"/testing/mission-test-configs/{config_id}",
            request_options=request_options,
        )
        return MissionTestConfig.model_validate(raw)

    async def delete(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        await self._transport.request(
            "DELETE",
            f"/testing/mission-test-configs/{config_id}",
            request_options=request_options,
        )

    async def run(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> MissionTestRun:
        raw = await self._transport.request(
            "POST",
            f"/testing/mission-test-configs/{config_id}/runs",
            request_options=request_options,
        )
        return MissionTestRun.model_validate(raw)
