"""Mission test configs resource - all /testing/mission-test-configs endpoints."""
from __future__ import annotations

from typing import Any, List, Optional

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.mission_test_configs import (
    CreateMissionTestConfigRequest,
    MissionTestConfig,
    MissionTestConfigListItem,
)
from ..models.mission_tests import MissionTestRun

# Sentinel distinguishing "omit this field" (leave unchanged) from an explicit
# `None`, which clears the attribute server-side (PATCH nullable-to-clear).
_UNSET: Any = object()


def _build_config_list_params(
    *,
    name: Optional[str],
    phone_number: Optional[str],
    sector: Optional[str],
    profile_id: Optional[str],
    tag: Optional[str],
    created_after: Optional[str],
    created_before: Optional[str],
    sort: Optional[str],
    sort_dir: Optional[str],
    limit: Optional[int],
    cursor: Optional[str],
    next_token: Optional[str],
) -> dict:
    params: dict = {}
    if name is not None:
        params["name"] = name
    if phone_number is not None:
        params["phoneNumber"] = phone_number
    if sector is not None:
        params["sector"] = sector
    if profile_id is not None:
        params["profileId"] = profile_id
    if tag is not None:
        params["tag"] = tag
    if created_after is not None:
        params["createdAfter"] = created_after
    if created_before is not None:
        params["createdBefore"] = created_before
    if sort is not None:
        params["sort"] = sort
    if sort_dir is not None:
        params["sortDir"] = sort_dir
    if limit is not None:
        params["limit"] = limit
    if cursor is not None:
        params["cursor"] = cursor
    elif next_token is not None:
        params["cursor"] = next_token
    return params


def _build_update_body(
    *,
    name: Optional[str],
    description: Any,
    phone_number: Optional[str],
    sector: Optional[str],
    mission: Optional[str],
    acceptance: Optional[str],
    profile_id: Optional[str],
    tags: Any,
) -> dict:
    body: dict = {}
    if name is not None:
        body["name"] = name
    if description is not _UNSET:
        body["description"] = description  # may be None to clear
    if phone_number is not None:
        body["phoneNumber"] = phone_number
    if sector is not None:
        body["sector"] = sector
    if mission is not None:
        body["mission"] = mission
    if acceptance is not None:
        body["acceptance"] = acceptance
    if profile_id is not None:
        body["profileId"] = profile_id
    if tags is not _UNSET:
        body["tags"] = tags  # may be None to clear
    if not body:
        raise ValueError("update() requires at least one field to change")
    return body


def _apply_cursor(params: dict) -> dict:
    """Translate the paginator's injected `nextToken` into the spec `cursor` param."""
    p = dict(params)
    if "nextToken" in p:
        p["cursor"] = p.pop("nextToken")
    return p


class MissionTestConfigsResource(SyncResource):
    """Synchronous /testing/mission-test-configs endpoints."""

    def list(
        self,
        *,
        name: str | None = None,
        phone_number: str | None = None,
        sector: str | None = None,
        profile_id: str | None = None,
        tag: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        sort: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[MissionTestConfigListItem]:
        params = _build_config_list_params(
            name=name,
            phone_number=phone_number,
            sector=sector,
            profile_id=profile_id,
            tag=tag,
            created_after=created_after,
            created_before=created_before,
            sort=sort,
            sort_dir=sort_dir,
            limit=limit,
            cursor=cursor,
            next_token=next_token,
        )

        def fetch(p: dict) -> dict:
            raw = self._transport.request(
                "GET",
                "/testing/mission-test-configs",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return {
                "items": raw.get("items", []),
                "nextToken": raw.get("nextCursor", raw.get("nextToken")),
            }

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=MissionTestConfigListItem
        )

    def list_page(
        self,
        *,
        name: str | None = None,
        phone_number: str | None = None,
        sector: str | None = None,
        profile_id: str | None = None,
        tag: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        sort: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[MissionTestConfigListItem]:
        params = _build_config_list_params(
            name=name,
            phone_number=phone_number,
            sector=sector,
            profile_id=profile_id,
            tag=tag,
            created_after=created_after,
            created_before=created_before,
            sort=sort,
            sort_dir=sort_dir,
            limit=limit,
            cursor=cursor,
            next_token=next_token,
        )
        raw = self._transport.request(
            "GET",
            "/testing/mission-test-configs",
            params=params,
            request_options=request_options,
        )
        items = [MissionTestConfigListItem.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextCursor", raw.get("nextToken")))

    def create(
        self,
        *,
        name: str,
        sector: str,
        mission: str,
        acceptance: str,
        profile_id: str,
        phone_number: str | None = None,
        description: str | None = None,
        tags: List[str] | None = None,
        request_options: RequestOptions | None = None,
    ) -> MissionTestConfig:
        body = CreateMissionTestConfigRequest(
            name=name,
            sector=sector,
            mission=mission,
            acceptance=acceptance,
            profile_id=profile_id,
            phone_number=phone_number,
            description=description,
            tags=tags,
        ).model_dump(by_alias=True, exclude_none=True)
        raw = self._transport.request(
            "POST",
            "/testing/mission-test-configs",
            json=body,
            request_options=request_options,
        )
        return MissionTestConfig.model_validate(raw)

    def update(
        self,
        config_id: str,
        *,
        name: str | None = None,
        description: Any = _UNSET,
        phone_number: str | None = None,
        sector: str | None = None,
        mission: str | None = None,
        acceptance: str | None = None,
        profile_id: str | None = None,
        tags: Any = _UNSET,
        request_options: RequestOptions | None = None,
    ) -> MissionTestConfig:
        """Partially update a mission test config (PATCH).

        At least one field is required. Pass ``description=None`` or
        ``tags=None`` explicitly to clear those attributes server-side.
        """
        body = _build_update_body(
            name=name,
            description=description,
            phone_number=phone_number,
            sector=sector,
            mission=mission,
            acceptance=acceptance,
            profile_id=profile_id,
            tags=tags,
        )
        raw = self._transport.request(
            "PATCH",
            f"/testing/mission-test-configs/{config_id}",
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
        name: str | None = None,
        phone_number: str | None = None,
        sector: str | None = None,
        profile_id: str | None = None,
        tag: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        sort: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[MissionTestConfigListItem]:
        params = _build_config_list_params(
            name=name,
            phone_number=phone_number,
            sector=sector,
            profile_id=profile_id,
            tag=tag,
            created_after=created_after,
            created_before=created_before,
            sort=sort,
            sort_dir=sort_dir,
            limit=limit,
            cursor=cursor,
            next_token=next_token,
        )

        async def fetch(p: dict) -> dict:
            raw = await self._transport.request(
                "GET",
                "/testing/mission-test-configs",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return {
                "items": raw.get("items", []),
                "nextToken": raw.get("nextCursor", raw.get("nextToken")),
            }

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=MissionTestConfigListItem
        )

    async def list_page(
        self,
        *,
        name: str | None = None,
        phone_number: str | None = None,
        sector: str | None = None,
        profile_id: str | None = None,
        tag: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        sort: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[MissionTestConfigListItem]:
        params = _build_config_list_params(
            name=name,
            phone_number=phone_number,
            sector=sector,
            profile_id=profile_id,
            tag=tag,
            created_after=created_after,
            created_before=created_before,
            sort=sort,
            sort_dir=sort_dir,
            limit=limit,
            cursor=cursor,
            next_token=next_token,
        )
        raw = await self._transport.request(
            "GET",
            "/testing/mission-test-configs",
            params=params,
            request_options=request_options,
        )
        items = [MissionTestConfigListItem.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextCursor", raw.get("nextToken")))

    async def create(
        self,
        *,
        name: str,
        sector: str,
        mission: str,
        acceptance: str,
        profile_id: str,
        phone_number: str | None = None,
        description: str | None = None,
        tags: List[str] | None = None,
        request_options: RequestOptions | None = None,
    ) -> MissionTestConfig:
        body = CreateMissionTestConfigRequest(
            name=name,
            sector=sector,
            mission=mission,
            acceptance=acceptance,
            profile_id=profile_id,
            phone_number=phone_number,
            description=description,
            tags=tags,
        ).model_dump(by_alias=True, exclude_none=True)
        raw = await self._transport.request(
            "POST",
            "/testing/mission-test-configs",
            json=body,
            request_options=request_options,
        )
        return MissionTestConfig.model_validate(raw)

    async def update(
        self,
        config_id: str,
        *,
        name: str | None = None,
        description: Any = _UNSET,
        phone_number: str | None = None,
        sector: str | None = None,
        mission: str | None = None,
        acceptance: str | None = None,
        profile_id: str | None = None,
        tags: Any = _UNSET,
        request_options: RequestOptions | None = None,
    ) -> MissionTestConfig:
        """Partially update a mission test config (PATCH).

        At least one field is required. Pass ``description=None`` or
        ``tags=None`` explicitly to clear those attributes server-side.
        """
        body = _build_update_body(
            name=name,
            description=description,
            phone_number=phone_number,
            sector=sector,
            mission=mission,
            acceptance=acceptance,
            profile_id=profile_id,
            tags=tags,
        )
        raw = await self._transport.request(
            "PATCH",
            f"/testing/mission-test-configs/{config_id}",
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
