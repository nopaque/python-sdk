"""Mapping resource - all /mapping endpoints."""
from __future__ import annotations

from typing import Any, Callable, List, Literal
from urllib.parse import quote

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._polling import wait_for_async, wait_for_sync
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.mapping import (
    MappingJob,
    MappingJobConfig,
    MappingJobListItem,
    MappingPath,
    MappingRun,
    MappingStep,
    MappingTree,
    ProbeResult,
)

TERMINAL_STATUSES: set[str] = {"completed", "failed", "limited", "cancelled"}
TreeFormat = Literal["tree", "flat"]
MappingListStatus = Literal["idle", "running", "completed", "failed", "limited"]
MappingSort = Literal["createdAt"]
SortDir = Literal["asc", "desc"]


def _encode(v: str) -> str:
    return quote(v, safe="")


def _build_mapping_list_params(
    *,
    workspace_id: str | None,
    phone_number: str | None,
    name: str | None,
    profile_id: str | None,
    tag: str | None,
    status: str | None,
    created_after: str | None,
    created_before: str | None,
    sort: str | None,
    sort_dir: str | None,
    limit: int | None,
    cursor: str | None,
    next_token: str | None,
) -> dict:
    params: dict = {}
    if workspace_id:
        params["workspaceId"] = workspace_id
    if phone_number is not None:
        params["phoneNumber"] = phone_number
    if name is not None:
        params["name"] = name
    if profile_id is not None:
        params["profileId"] = profile_id
    if tag is not None:
        params["tag"] = tag
    if status is not None:
        params["status"] = status
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
    # `cursor` is the spec param; `next_token` kept as a back-compat alias.
    if cursor is not None:
        params["cursor"] = cursor
    elif next_token is not None:
        params["cursor"] = next_token
    return params


def _normalize_cursor_page(raw: dict, items_key: str = "items") -> dict:
    """Normalize a `{ items, nextCursor?, nextToken? }` body for the paginator.

    Reads `nextCursor` first, falling back to `nextToken`, and exposes it under
    the paginator's expected `nextToken` key.
    """
    return {
        "items": raw.get(items_key, raw.get("items", [])),
        "nextToken": raw.get("nextCursor", raw.get("nextToken")),
    }


def _apply_cursor(params: dict) -> dict:
    """Translate the paginator's injected `nextToken` into the spec `cursor` param."""
    p = dict(params)
    if "nextToken" in p:
        p["cursor"] = p.pop("nextToken")
    return p


class MappingResource(SyncResource):
    """Synchronous /mapping endpoints."""

    def list(
        self,
        *,
        workspace_id: str | None = None,
        phone_number: str | None = None,
        name: str | None = None,
        profile_id: str | None = None,
        tag: str | None = None,
        status: MappingListStatus | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        sort: MappingSort | None = None,
        sort_dir: SortDir | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[MappingJobListItem]:
        params = _build_mapping_list_params(
            workspace_id=workspace_id,
            phone_number=phone_number,
            name=name,
            profile_id=profile_id,
            tag=tag,
            status=status,
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
                "GET", "/mapping", params=_apply_cursor(p), request_options=request_options
            )
            return _normalize_cursor_page(raw)

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=MappingJobListItem)

    def list_page(
        self,
        *,
        workspace_id: str | None = None,
        phone_number: str | None = None,
        name: str | None = None,
        profile_id: str | None = None,
        tag: str | None = None,
        status: MappingListStatus | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        sort: MappingSort | None = None,
        sort_dir: SortDir | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[MappingJobListItem]:
        params = _build_mapping_list_params(
            workspace_id=workspace_id,
            phone_number=phone_number,
            name=name,
            profile_id=profile_id,
            tag=tag,
            status=status,
            created_after=created_after,
            created_before=created_before,
            sort=sort,
            sort_dir=sort_dir,
            limit=limit,
            cursor=cursor,
            next_token=next_token,
        )
        raw = self._transport.request(
            "GET", "/mapping", params=params, request_options=request_options
        )
        items = [MappingJobListItem.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextCursor", raw.get("nextToken")))

    def get(
        self, job_id: str, *, request_options: RequestOptions | None = None
    ) -> MappingJob:
        raw = self._transport.request(
            "GET", f"/mapping/{job_id}", request_options=request_options
        )
        return MappingJob.model_validate(raw)

    def create(
        self,
        *,
        name: str,
        phone_number: str,
        config: MappingJobConfig,
        profile_id: str | None = None,
        tags: List[str] | None = None,
        request_options: RequestOptions | None = None,
    ) -> MappingJob:
        body: dict = {
            "name": name,
            "phoneNumber": phone_number,
            "config": config.model_dump(by_alias=True, exclude_none=True),
        }
        if profile_id:
            body["profileId"] = profile_id
        if tags is not None:
            body["tags"] = tags
        raw = self._transport.request(
            "POST", "/mapping", json=body, request_options=request_options
        )
        return MappingJob.model_validate(raw)

    def update(
        self,
        job_id: str,
        *,
        name: str | None = None,
        phone_number: str | None = None,
        config: MappingJobConfig | None = None,
        tags: List[str] | None = None,
        request_options: RequestOptions | None = None,
    ) -> MappingJob:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if phone_number is not None:
            body["phoneNumber"] = phone_number
        if config is not None:
            body["config"] = config.model_dump(by_alias=True, exclude_none=True)
        if tags is not None:
            body["tags"] = tags
        raw = self._transport.request(
            "PATCH", f"/mapping/{job_id}", json=body, request_options=request_options
        )
        return MappingJob.model_validate(raw)

    def delete(
        self, job_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        self._transport.request(
            "DELETE", f"/mapping/{job_id}", request_options=request_options
        )

    def start(
        self, job_id: str, *, request_options: RequestOptions | None = None
    ) -> MappingJob:
        raw = self._transport.request(
            "POST", f"/mapping/{job_id}/start", request_options=request_options
        )
        return MappingJob.model_validate(raw)

    def cancel(
        self, job_id: str, *, request_options: RequestOptions | None = None
    ) -> MappingJob:
        raw = self._transport.request(
            "POST", f"/mapping/{job_id}/cancel", request_options=request_options
        )
        return MappingJob.model_validate(raw)

    def attest(
        self, job_id: str, *, request_options: RequestOptions | None = None
    ) -> dict:
        return self._transport.request(
            "POST",
            "/mapping/attest",
            json={"jobId": job_id},
            request_options=request_options,
        )

    def steps(
        self,
        job_id: str,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[MappingStep]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET",
                f"/mapping/{job_id}/steps",
                params=p,
                request_options=request_options,
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=MappingStep)

    def tree(
        self,
        job_id: str,
        *,
        format: TreeFormat = "tree",
        request_options: RequestOptions | None = None,
    ) -> MappingTree:
        raw = self._transport.request(
            "GET",
            f"/mapping/{job_id}/tree",
            params={"format": format},
            request_options=request_options,
        )
        return MappingTree.model_validate(raw)

    def runs(
        self,
        job_id: str,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[MappingRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET",
                f"/mapping/{job_id}/runs",
                params=p,
                request_options=request_options,
            )

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=MappingRun, items_key="runs"
        )

    def paths(
        self,
        job_id: str,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[MappingPath]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET",
                f"/mapping/{job_id}/paths",
                params=p,
                request_options=request_options,
            )

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=MappingPath, items_key="rules"
        )

    def update_path(
        self,
        job_id: str,
        path: str,
        *,
        repeat_behavior: str | None = None,
        request_options: RequestOptions | None = None,
        **extra: Any,
    ) -> MappingPath:
        body: dict = {**extra}
        if repeat_behavior is not None:
            body["repeatBehavior"] = repeat_behavior
        raw = self._transport.request(
            "PATCH",
            f"/mapping/{job_id}/paths/{_encode(path)}",
            json=body,
            request_options=request_options,
        )
        return MappingPath.model_validate(raw)

    def delete_path(
        self,
        job_id: str,
        path: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> None:
        self._transport.request(
            "DELETE",
            f"/mapping/{job_id}/paths/{_encode(path)}",
            request_options=request_options,
        )

    def remap(
        self,
        job_id: str,
        path: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> MappingJob:
        raw = self._transport.request(
            "POST",
            f"/mapping/{job_id}/remap/{_encode(path)}",
            request_options=request_options,
        )
        return MappingJob.model_validate(raw)

    def probe(
        self,
        job_id: str,
        run_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> ProbeResult:
        """Trigger on-demand security-probe analysis on a completed run.

        Returns the queue summary ``{ message, probe_count }``; poll the run
        / steps afterwards to see classified results land.
        """
        raw = self._transport.request(
            "POST",
            f"/mapping/{job_id}/runs/{run_id}/probe",
            request_options=request_options,
        )
        return ProbeResult.model_validate(raw)

    def wait_for_complete(
        self,
        job_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Callable[[MappingJob], None] | None = None,
        request_options: RequestOptions | None = None,
    ) -> MappingJob:
        def fetch() -> MappingJob:
            return self.get(job_id, request_options=request_options)

        return wait_for_sync(
            fetch=fetch,
            is_terminal=lambda job: job.status in TERMINAL_STATUSES,
            timeout=timeout,
            initial_interval=poll_interval,
            on_update=on_update,
        )


class AsyncMappingResource(AsyncResource):
    """Asynchronous /mapping endpoints."""

    def list(
        self,
        *,
        workspace_id: str | None = None,
        phone_number: str | None = None,
        name: str | None = None,
        profile_id: str | None = None,
        tag: str | None = None,
        status: MappingListStatus | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        sort: MappingSort | None = None,
        sort_dir: SortDir | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[MappingJobListItem]:
        params = _build_mapping_list_params(
            workspace_id=workspace_id,
            phone_number=phone_number,
            name=name,
            profile_id=profile_id,
            tag=tag,
            status=status,
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
                "GET", "/mapping", params=_apply_cursor(p), request_options=request_options
            )
            return _normalize_cursor_page(raw)

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=MappingJobListItem)

    async def list_page(
        self,
        *,
        workspace_id: str | None = None,
        phone_number: str | None = None,
        name: str | None = None,
        profile_id: str | None = None,
        tag: str | None = None,
        status: MappingListStatus | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        sort: MappingSort | None = None,
        sort_dir: SortDir | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[MappingJobListItem]:
        params = _build_mapping_list_params(
            workspace_id=workspace_id,
            phone_number=phone_number,
            name=name,
            profile_id=profile_id,
            tag=tag,
            status=status,
            created_after=created_after,
            created_before=created_before,
            sort=sort,
            sort_dir=sort_dir,
            limit=limit,
            cursor=cursor,
            next_token=next_token,
        )
        raw = await self._transport.request(
            "GET", "/mapping", params=params, request_options=request_options
        )
        items = [MappingJobListItem.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextCursor", raw.get("nextToken")))

    async def get(
        self, job_id: str, *, request_options: RequestOptions | None = None
    ) -> MappingJob:
        raw = await self._transport.request(
            "GET", f"/mapping/{job_id}", request_options=request_options
        )
        return MappingJob.model_validate(raw)

    async def create(
        self,
        *,
        name: str,
        phone_number: str,
        config: MappingJobConfig,
        profile_id: str | None = None,
        tags: List[str] | None = None,
        request_options: RequestOptions | None = None,
    ) -> MappingJob:
        body: dict = {
            "name": name,
            "phoneNumber": phone_number,
            "config": config.model_dump(by_alias=True, exclude_none=True),
        }
        if profile_id:
            body["profileId"] = profile_id
        if tags is not None:
            body["tags"] = tags
        raw = await self._transport.request(
            "POST", "/mapping", json=body, request_options=request_options
        )
        return MappingJob.model_validate(raw)

    async def update(
        self,
        job_id: str,
        *,
        name: str | None = None,
        phone_number: str | None = None,
        config: MappingJobConfig | None = None,
        tags: List[str] | None = None,
        request_options: RequestOptions | None = None,
    ) -> MappingJob:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if phone_number is not None:
            body["phoneNumber"] = phone_number
        if config is not None:
            body["config"] = config.model_dump(by_alias=True, exclude_none=True)
        if tags is not None:
            body["tags"] = tags
        raw = await self._transport.request(
            "PATCH", f"/mapping/{job_id}", json=body, request_options=request_options
        )
        return MappingJob.model_validate(raw)

    async def delete(
        self, job_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        await self._transport.request(
            "DELETE", f"/mapping/{job_id}", request_options=request_options
        )

    async def start(
        self, job_id: str, *, request_options: RequestOptions | None = None
    ) -> MappingJob:
        raw = await self._transport.request(
            "POST", f"/mapping/{job_id}/start", request_options=request_options
        )
        return MappingJob.model_validate(raw)

    async def cancel(
        self, job_id: str, *, request_options: RequestOptions | None = None
    ) -> MappingJob:
        raw = await self._transport.request(
            "POST", f"/mapping/{job_id}/cancel", request_options=request_options
        )
        return MappingJob.model_validate(raw)

    async def attest(
        self, job_id: str, *, request_options: RequestOptions | None = None
    ) -> dict:
        return await self._transport.request(
            "POST",
            "/mapping/attest",
            json={"jobId": job_id},
            request_options=request_options,
        )

    def steps(
        self,
        job_id: str,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[MappingStep]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET",
                f"/mapping/{job_id}/steps",
                params=p,
                request_options=request_options,
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=MappingStep)

    async def tree(
        self,
        job_id: str,
        *,
        format: TreeFormat = "tree",
        request_options: RequestOptions | None = None,
    ) -> MappingTree:
        raw = await self._transport.request(
            "GET",
            f"/mapping/{job_id}/tree",
            params={"format": format},
            request_options=request_options,
        )
        return MappingTree.model_validate(raw)

    def runs(
        self,
        job_id: str,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[MappingRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET",
                f"/mapping/{job_id}/runs",
                params=p,
                request_options=request_options,
            )

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=MappingRun, items_key="runs"
        )

    def paths(
        self,
        job_id: str,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[MappingPath]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET",
                f"/mapping/{job_id}/paths",
                params=p,
                request_options=request_options,
            )

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=MappingPath, items_key="rules"
        )

    async def update_path(
        self,
        job_id: str,
        path: str,
        *,
        repeat_behavior: str | None = None,
        request_options: RequestOptions | None = None,
        **extra: Any,
    ) -> MappingPath:
        body: dict = {**extra}
        if repeat_behavior is not None:
            body["repeatBehavior"] = repeat_behavior
        raw = await self._transport.request(
            "PATCH",
            f"/mapping/{job_id}/paths/{_encode(path)}",
            json=body,
            request_options=request_options,
        )
        return MappingPath.model_validate(raw)

    async def delete_path(
        self,
        job_id: str,
        path: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> None:
        await self._transport.request(
            "DELETE",
            f"/mapping/{job_id}/paths/{_encode(path)}",
            request_options=request_options,
        )

    async def remap(
        self,
        job_id: str,
        path: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> MappingJob:
        raw = await self._transport.request(
            "POST",
            f"/mapping/{job_id}/remap/{_encode(path)}",
            request_options=request_options,
        )
        return MappingJob.model_validate(raw)

    async def probe(
        self,
        job_id: str,
        run_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> ProbeResult:
        """Trigger on-demand security-probe analysis on a completed run.

        Returns the queue summary ``{ message, probe_count }``; poll the run
        / steps afterwards to see classified results land.
        """
        raw = await self._transport.request(
            "POST",
            f"/mapping/{job_id}/runs/{run_id}/probe",
            request_options=request_options,
        )
        return ProbeResult.model_validate(raw)

    async def wait_for_complete(
        self,
        job_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Callable[[MappingJob], None] | None = None,
        request_options: RequestOptions | None = None,
    ) -> MappingJob:
        async def fetch() -> MappingJob:
            return await self.get(job_id, request_options=request_options)

        return await wait_for_async(
            fetch=fetch,
            is_terminal=lambda job: job.status in TERMINAL_STATUSES,
            timeout=timeout,
            initial_interval=poll_interval,
            on_update=on_update,
        )
