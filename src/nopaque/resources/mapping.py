"""Mapping resource - all /mapping endpoints."""
from __future__ import annotations

from typing import Any, Callable, Literal, Optional, Set
from urllib.parse import quote

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._polling import wait_for_async, wait_for_sync
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.mapping import (
    MappingJob,
    MappingJobConfig,
    MappingPath,
    MappingRun,
    MappingStep,
    MappingTree,
)

TERMINAL_STATUSES: Set[str] = {"completed", "failed", "limited", "cancelled"}
TreeFormat = Literal["tree", "flat"]


def _encode(v: str) -> str:
    return quote(v, safe="")


class MappingResource(SyncResource):
    """Synchronous /mapping endpoints."""

    def list(
        self,
        *,
        workspace_id: Optional[str] = None,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> SyncPaginator[MappingJob]:
        params: dict = {}
        if workspace_id:
            params["workspaceId"] = workspace_id
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/mapping", params=p, request_options=request_options
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=MappingJob)

    def list_page(
        self,
        *,
        workspace_id: Optional[str] = None,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Page[MappingJob]:
        params: dict = {}
        if workspace_id:
            params["workspaceId"] = workspace_id
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/mapping", params=params, request_options=request_options
        )
        items = [MappingJob.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
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
        mapping_mode: str,
        profile_id: Optional[str] = None,
        config: Optional[MappingJobConfig] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> MappingJob:
        body: dict = {
            "name": name,
            "phoneNumber": phone_number,
            "mappingMode": mapping_mode,
        }
        if profile_id:
            body["profileId"] = profile_id
        if config:
            body["config"] = config.model_dump(by_alias=True, exclude_none=True)
        raw = self._transport.request(
            "POST", "/mapping", json=body, request_options=request_options
        )
        return MappingJob.model_validate(raw)

    def update(
        self,
        job_id: str,
        *,
        name: Optional[str] = None,
        phone_number: Optional[str] = None,
        mapping_mode: Optional[str] = None,
        config: Optional[MappingJobConfig] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> MappingJob:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if phone_number is not None:
            body["phoneNumber"] = phone_number
        if mapping_mode is not None:
            body["mappingMode"] = mapping_mode
        if config is not None:
            body["config"] = config.model_dump(by_alias=True, exclude_none=True)
        raw = self._transport.request(
            "PATCH", f"/mapping/{job_id}", json=body, request_options=request_options
        )
        return MappingJob.model_validate(raw)

    def delete(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> None:
        self._transport.request(
            "DELETE", f"/mapping/{job_id}", request_options=request_options
        )

    def start(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> MappingJob:
        raw = self._transport.request(
            "POST", f"/mapping/{job_id}/start", request_options=request_options
        )
        return MappingJob.model_validate(raw)

    def cancel(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> MappingJob:
        raw = self._transport.request(
            "POST", f"/mapping/{job_id}/cancel", request_options=request_options
        )
        return MappingJob.model_validate(raw)

    def attest(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
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
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
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
        request_options: Optional[RequestOptions] = None,
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
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
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

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=MappingRun)

    def paths(
        self,
        job_id: str,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
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

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=MappingPath)

    def update_path(
        self,
        job_id: str,
        path: str,
        *,
        repeat_behavior: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
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
        request_options: Optional[RequestOptions] = None,
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
        request_options: Optional[RequestOptions] = None,
    ) -> MappingJob:
        raw = self._transport.request(
            "POST",
            f"/mapping/{job_id}/remap/{_encode(path)}",
            request_options=request_options,
        )
        return MappingJob.model_validate(raw)

    def wait_for_complete(
        self,
        job_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Optional[Callable[[MappingJob], None]] = None,
        request_options: Optional[RequestOptions] = None,
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
        workspace_id: Optional[str] = None,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> AsyncPaginator[MappingJob]:
        params: dict = {}
        if workspace_id:
            params["workspaceId"] = workspace_id
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/mapping", params=p, request_options=request_options
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=MappingJob)

    async def list_page(
        self,
        *,
        workspace_id: Optional[str] = None,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Page[MappingJob]:
        params: dict = {}
        if workspace_id:
            params["workspaceId"] = workspace_id
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/mapping", params=params, request_options=request_options
        )
        items = [MappingJob.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
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
        mapping_mode: str,
        profile_id: Optional[str] = None,
        config: Optional[MappingJobConfig] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> MappingJob:
        body: dict = {
            "name": name,
            "phoneNumber": phone_number,
            "mappingMode": mapping_mode,
        }
        if profile_id:
            body["profileId"] = profile_id
        if config:
            body["config"] = config.model_dump(by_alias=True, exclude_none=True)
        raw = await self._transport.request(
            "POST", "/mapping", json=body, request_options=request_options
        )
        return MappingJob.model_validate(raw)

    async def update(
        self,
        job_id: str,
        *,
        name: Optional[str] = None,
        phone_number: Optional[str] = None,
        mapping_mode: Optional[str] = None,
        config: Optional[MappingJobConfig] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> MappingJob:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if phone_number is not None:
            body["phoneNumber"] = phone_number
        if mapping_mode is not None:
            body["mappingMode"] = mapping_mode
        if config is not None:
            body["config"] = config.model_dump(by_alias=True, exclude_none=True)
        raw = await self._transport.request(
            "PATCH", f"/mapping/{job_id}", json=body, request_options=request_options
        )
        return MappingJob.model_validate(raw)

    async def delete(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> None:
        await self._transport.request(
            "DELETE", f"/mapping/{job_id}", request_options=request_options
        )

    async def start(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> MappingJob:
        raw = await self._transport.request(
            "POST", f"/mapping/{job_id}/start", request_options=request_options
        )
        return MappingJob.model_validate(raw)

    async def cancel(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> MappingJob:
        raw = await self._transport.request(
            "POST", f"/mapping/{job_id}/cancel", request_options=request_options
        )
        return MappingJob.model_validate(raw)

    async def attest(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
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
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
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
        request_options: Optional[RequestOptions] = None,
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
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
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

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=MappingRun)

    def paths(
        self,
        job_id: str,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
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

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=MappingPath)

    async def update_path(
        self,
        job_id: str,
        path: str,
        *,
        repeat_behavior: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
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
        request_options: Optional[RequestOptions] = None,
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
        request_options: Optional[RequestOptions] = None,
    ) -> MappingJob:
        raw = await self._transport.request(
            "POST",
            f"/mapping/{job_id}/remap/{_encode(path)}",
            request_options=request_options,
        )
        return MappingJob.model_validate(raw)

    async def wait_for_complete(
        self,
        job_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Optional[Callable[[MappingJob], None]] = None,
        request_options: Optional[RequestOptions] = None,
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
