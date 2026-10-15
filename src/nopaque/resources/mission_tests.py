"""Mission tests resource - all /testing/mission-tests endpoints."""
from __future__ import annotations

from typing import Optional, Sequence, Union

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.mission_tests import (
    CreateMissionTestRequest,
    MissionTestDefaults,
    MissionTestKind,
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


def _build_list_params(
    *,
    kind: Optional[str],
    config_id: Optional[str],
    q: Optional[str],
    phone_number: Optional[str],
    tags: Union[str, Sequence[str], None],
    limit: Optional[int],
    next_token: Optional[str],
) -> dict:
    """Query params for GET /testing/mission-tests. All filters are server-side.

    - kind: "freeform" (missions) or "compliance".
    - config_id: only runs launched from this mission test config.
    - q: case-insensitive text search on the run's sector or mission.
    - phone_number: substring match on the number called.
    - tags: runs whose config carries ANY of these tags (str or list).
    """
    params: dict = {}
    if kind is not None:
        params["kind"] = kind
    if config_id is not None:
        params["configId"] = config_id
    if q is not None:
        params["q"] = q
    if phone_number is not None:
        params["phoneNumber"] = phone_number
    if tags is not None:
        params["tags"] = tags if isinstance(tags, str) else ",".join(tags)
    if limit is not None:
        params["limit"] = limit
    if next_token is not None:
        params["nextToken"] = next_token
    return params


def _apply_cursor(params: dict) -> dict:
    """Translate the paginator's `nextToken` into the api's `cursor` param."""
    p = dict(params)
    if "nextToken" in p:
        p["cursor"] = p.pop("nextToken")
    return p


def _to_page(raw: dict) -> dict:
    """The api returns `{runs, nextCursor}`; the paginator expects `{items, nextToken}`."""
    return {"items": raw.get("runs", []), "nextToken": raw.get("nextCursor")}


class MissionTestsResource(SyncResource):
    """Synchronous /testing/mission-tests endpoints."""

    def list(
        self,
        *,
        kind: MissionTestKind | None = None,
        config_id: str | None = None,
        q: str | None = None,
        phone_number: str | None = None,
        tags: Union[str, Sequence[str], None] = None,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[MissionTestRun]:
        params = _build_list_params(
            kind=kind,
            config_id=config_id,
            q=q,
            phone_number=phone_number,
            tags=tags,
            limit=limit,
            next_token=next_token,
        )

        def fetch(p: dict) -> dict:
            raw = self._transport.request(
                "GET",
                "/testing/mission-tests",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return _to_page(raw)

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=MissionTestRun)

    def list_page(
        self,
        *,
        kind: MissionTestKind | None = None,
        config_id: str | None = None,
        q: str | None = None,
        phone_number: str | None = None,
        tags: Union[str, Sequence[str], None] = None,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[MissionTestRun]:
        params = _build_list_params(
            kind=kind,
            config_id=config_id,
            q=q,
            phone_number=phone_number,
            tags=tags,
            limit=limit,
            next_token=next_token,
        )
        raw = self._transport.request(
            "GET",
            "/testing/mission-tests",
            params=_apply_cursor(params),
            request_options=request_options,
        )
        items = [MissionTestRun.model_validate(i) for i in raw.get("runs", [])]
        return Page(items=items, next_token=raw.get("nextCursor"))

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
        kind: MissionTestKind | None = None,
        config_id: str | None = None,
        q: str | None = None,
        phone_number: str | None = None,
        tags: Union[str, Sequence[str], None] = None,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[MissionTestRun]:
        params = _build_list_params(
            kind=kind,
            config_id=config_id,
            q=q,
            phone_number=phone_number,
            tags=tags,
            limit=limit,
            next_token=next_token,
        )

        async def fetch(p: dict) -> dict:
            raw = await self._transport.request(
                "GET",
                "/testing/mission-tests",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return _to_page(raw)

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=MissionTestRun)

    async def list_page(
        self,
        *,
        kind: MissionTestKind | None = None,
        config_id: str | None = None,
        q: str | None = None,
        phone_number: str | None = None,
        tags: Union[str, Sequence[str], None] = None,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[MissionTestRun]:
        params = _build_list_params(
            kind=kind,
            config_id=config_id,
            q=q,
            phone_number=phone_number,
            tags=tags,
            limit=limit,
            next_token=next_token,
        )
        raw = await self._transport.request(
            "GET",
            "/testing/mission-tests",
            params=_apply_cursor(params),
            request_options=request_options,
        )
        items = [MissionTestRun.model_validate(i) for i in raw.get("runs", [])]
        return Page(items=items, next_token=raw.get("nextCursor"))

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
