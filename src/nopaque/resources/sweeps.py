"""Sweeps resource - /testing/sweeps and /testing/sweep-runs."""
from __future__ import annotations

import builtins
from typing import Callable

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._polling import wait_for_async, wait_for_sync
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.sweeps import Sweep, SweepRun

RUN_TERMINAL_STATUSES: set[str] = {"completed", "failed", "cancelled"}


class SweepsResource(SyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[Sweep]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/testing/sweeps", params=p, request_options=request_options
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=Sweep)

    def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[Sweep]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/testing/sweeps", params=params, request_options=request_options
        )
        items = [Sweep.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, sweep_id: str, *, request_options: RequestOptions | None = None
    ) -> Sweep:
        raw = self._transport.request(
            "GET", f"/testing/sweeps/{sweep_id}", request_options=request_options
        )
        return Sweep.model_validate(raw)

    def create(
        self,
        *,
        name: str,
        config_id: str,
        parameters: dict[str, builtins.list[str]],
        request_options: RequestOptions | None = None,
    ) -> Sweep:
        raw = self._transport.request(
            "POST",
            "/testing/sweeps",
            json={"name": name, "configId": config_id, "parameters": parameters},
            request_options=request_options,
        )
        return Sweep.model_validate(raw)

    def update(
        self,
        sweep_id: str,
        *,
        name: str | None = None,
        parameters: dict[str, builtins.list[str]] | None = None,
        request_options: RequestOptions | None = None,
    ) -> Sweep:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if parameters is not None:
            body["parameters"] = parameters
        raw = self._transport.request(
            "PUT",
            f"/testing/sweeps/{sweep_id}",
            json=body,
            request_options=request_options,
        )
        return Sweep.model_validate(raw)

    def delete(
        self, sweep_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        self._transport.request(
            "DELETE", f"/testing/sweeps/{sweep_id}", request_options=request_options
        )

    def run(
        self, sweep_id: str, *, request_options: RequestOptions | None = None
    ) -> SweepRun:
        raw = self._transport.request(
            "POST",
            f"/testing/sweeps/{sweep_id}/run",
            request_options=request_options,
        )
        return SweepRun.model_validate(raw)

    def runs(
        self,
        sweep_id: str,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[SweepRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET",
                f"/testing/sweeps/{sweep_id}/runs",
                params=p,
                request_options=request_options,
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=SweepRun)

    def list_runs(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[SweepRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/testing/sweep-runs", params=p, request_options=request_options
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=SweepRun)

    def get_run(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> SweepRun:
        raw = self._transport.request(
            "GET", f"/testing/sweep-runs/{run_id}", request_options=request_options
        )
        return SweepRun.model_validate(raw)

    def wait_for_run(
        self,
        run_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Callable[[SweepRun], None] | None = None,
        request_options: RequestOptions | None = None,
    ) -> SweepRun:
        def fetch() -> SweepRun:
            return self.get_run(run_id, request_options=request_options)

        return wait_for_sync(
            fetch=fetch,
            is_terminal=lambda r: r.status in RUN_TERMINAL_STATUSES,
            timeout=timeout,
            initial_interval=poll_interval,
            on_update=on_update,
        )


class AsyncSweepsResource(AsyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[Sweep]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/testing/sweeps", params=p, request_options=request_options
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=Sweep)

    async def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[Sweep]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/testing/sweeps", params=params, request_options=request_options
        )
        items = [Sweep.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, sweep_id: str, *, request_options: RequestOptions | None = None
    ) -> Sweep:
        raw = await self._transport.request(
            "GET", f"/testing/sweeps/{sweep_id}", request_options=request_options
        )
        return Sweep.model_validate(raw)

    async def create(
        self,
        *,
        name: str,
        config_id: str,
        parameters: dict[str, builtins.list[str]],
        request_options: RequestOptions | None = None,
    ) -> Sweep:
        raw = await self._transport.request(
            "POST",
            "/testing/sweeps",
            json={"name": name, "configId": config_id, "parameters": parameters},
            request_options=request_options,
        )
        return Sweep.model_validate(raw)

    async def update(
        self,
        sweep_id: str,
        *,
        name: str | None = None,
        parameters: dict[str, builtins.list[str]] | None = None,
        request_options: RequestOptions | None = None,
    ) -> Sweep:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if parameters is not None:
            body["parameters"] = parameters
        raw = await self._transport.request(
            "PUT",
            f"/testing/sweeps/{sweep_id}",
            json=body,
            request_options=request_options,
        )
        return Sweep.model_validate(raw)

    async def delete(
        self, sweep_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        await self._transport.request(
            "DELETE", f"/testing/sweeps/{sweep_id}", request_options=request_options
        )

    async def run(
        self, sweep_id: str, *, request_options: RequestOptions | None = None
    ) -> SweepRun:
        raw = await self._transport.request(
            "POST",
            f"/testing/sweeps/{sweep_id}/run",
            request_options=request_options,
        )
        return SweepRun.model_validate(raw)

    def runs(
        self,
        sweep_id: str,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[SweepRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET",
                f"/testing/sweeps/{sweep_id}/runs",
                params=p,
                request_options=request_options,
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=SweepRun)

    def list_runs(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[SweepRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/testing/sweep-runs", params=p, request_options=request_options
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=SweepRun)

    async def get_run(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> SweepRun:
        raw = await self._transport.request(
            "GET", f"/testing/sweep-runs/{run_id}", request_options=request_options
        )
        return SweepRun.model_validate(raw)

    async def wait_for_run(
        self,
        run_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Callable[[SweepRun], None] | None = None,
        request_options: RequestOptions | None = None,
    ) -> SweepRun:
        async def fetch() -> SweepRun:
            return await self.get_run(run_id, request_options=request_options)

        return await wait_for_async(
            fetch=fetch,
            is_terminal=lambda r: r.status in RUN_TERMINAL_STATUSES,
            timeout=timeout,
            initial_interval=poll_interval,
            on_update=on_update,
        )
