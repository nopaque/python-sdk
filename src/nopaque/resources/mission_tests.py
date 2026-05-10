"""Mission tests resource - all /testing/mission-tests endpoints."""
from __future__ import annotations

from typing import Union

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.mission_tests import (
    CreateMissionTestRequest,
    MissionTestDefaults,
    MissionTestProfile,
    MissionTestRun,
)


def _build_create_body(
    *,
    sector: str,
    mission: str,
    acceptance: str,
    profile: Union[MissionTestProfile, dict],
) -> dict:
    if isinstance(profile, MissionTestProfile):
        profile_model = profile
    else:
        profile_model = MissionTestProfile.model_validate(profile)
    request = CreateMissionTestRequest(
        sector=sector,
        mission=mission,
        acceptance=acceptance,
        profile=profile_model,
    )
    return request.model_dump(by_alias=True, exclude_none=True)


class MissionTestsResource(SyncResource):
    """Synchronous /testing/mission-tests endpoints."""

    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[MissionTestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/testing/mission-tests", params=p, request_options=request_options
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=MissionTestRun)

    def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[MissionTestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/testing/mission-tests", params=params, request_options=request_options
        )
        items = [MissionTestRun.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    def create(
        self,
        *,
        sector: str,
        mission: str,
        acceptance: str,
        profile: Union[MissionTestProfile, dict],
        request_options: RequestOptions | None = None,
    ) -> MissionTestRun:
        body = _build_create_body(
            sector=sector, mission=mission, acceptance=acceptance, profile=profile
        )
        raw = self._transport.request(
            "POST", "/testing/mission-tests", json=body, request_options=request_options
        )
        return MissionTestRun.model_validate(raw)

    def get_defaults(
        self, *, request_options: RequestOptions | None = None
    ) -> MissionTestDefaults:
        """Get default sector/mission/acceptance for ad-hoc runs.

        Raises ``ServerError`` with ``code='CATALOG_NOT_READY'`` until the
        mission-tester service publishes its SSM payload. Callers can catch
        and retry, or fall back to a known-good default sector/mission/acceptance.
        """
        raw = self._transport.request(
            "GET", "/testing/mission-tests/defaults", request_options=request_options
        )
        return MissionTestDefaults.model_validate(raw)

    def get(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> MissionTestRun:
        raw = self._transport.request(
            "GET", f"/testing/mission-tests/{run_id}", request_options=request_options
        )
        return MissionTestRun.model_validate(raw)

    def cancel(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> MissionTestRun:
        raw = self._transport.request(
            "POST", f"/testing/mission-tests/{run_id}/cancel", request_options=request_options
        )
        return MissionTestRun.model_validate(raw)


class AsyncMissionTestsResource(AsyncResource):
    """Asynchronous /testing/mission-tests endpoints."""

    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[MissionTestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/testing/mission-tests", params=p, request_options=request_options
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=MissionTestRun)

    async def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[MissionTestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/testing/mission-tests", params=params, request_options=request_options
        )
        items = [MissionTestRun.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def create(
        self,
        *,
        sector: str,
        mission: str,
        acceptance: str,
        profile: Union[MissionTestProfile, dict],
        request_options: RequestOptions | None = None,
    ) -> MissionTestRun:
        body = _build_create_body(
            sector=sector, mission=mission, acceptance=acceptance, profile=profile
        )
        raw = await self._transport.request(
            "POST", "/testing/mission-tests", json=body, request_options=request_options
        )
        return MissionTestRun.model_validate(raw)

    async def get_defaults(
        self, *, request_options: RequestOptions | None = None
    ) -> MissionTestDefaults:
        raw = await self._transport.request(
            "GET", "/testing/mission-tests/defaults", request_options=request_options
        )
        return MissionTestDefaults.model_validate(raw)

    async def get(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> MissionTestRun:
        raw = await self._transport.request(
            "GET", f"/testing/mission-tests/{run_id}", request_options=request_options
        )
        return MissionTestRun.model_validate(raw)

    async def cancel(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> MissionTestRun:
        raw = await self._transport.request(
            "POST", f"/testing/mission-tests/{run_id}/cancel", request_options=request_options
        )
        return MissionTestRun.model_validate(raw)
