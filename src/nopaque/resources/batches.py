"""Batches resource - /testing/batches and /testing/batch-runs."""
from __future__ import annotations

from typing import Callable

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._polling import wait_for_async, wait_for_sync
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.batches import Batch, BatchRun

RUN_TERMINAL_STATUSES: set[str] = {"completed", "failed", "cancelled"}


class BatchesResource(SyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[Batch]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/testing/batches", params=p, request_options=request_options
            )

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=Batch, items_key="batches"
        )

    def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[Batch]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/testing/batches", params=params, request_options=request_options
        )
        raw_items = raw.get("batches", raw.get("items", []))
        items = [Batch.model_validate(i) for i in raw_items]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, batch_id: str, *, request_options: RequestOptions | None = None
    ) -> Batch:
        raw = self._transport.request(
            "GET", f"/testing/batches/{batch_id}", request_options=request_options
        )
        return Batch.model_validate(raw)

    def create(
        self,
        *,
        name: str,
        config_id: str,
        dataset_id: str,
        request_options: RequestOptions | None = None,
    ) -> Batch:
        raw = self._transport.request(
            "POST",
            "/testing/batches",
            json={"name": name, "configId": config_id, "datasetId": dataset_id},
            request_options=request_options,
        )
        return Batch.model_validate(raw)

    def update(
        self,
        batch_id: str,
        *,
        name: str | None = None,
        dataset_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Batch:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if dataset_id is not None:
            body["datasetId"] = dataset_id
        raw = self._transport.request(
            "PUT",
            f"/testing/batches/{batch_id}",
            json=body,
            request_options=request_options,
        )
        return Batch.model_validate(raw)

    def delete(
        self, batch_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        self._transport.request(
            "DELETE", f"/testing/batches/{batch_id}", request_options=request_options
        )

    def run(
        self, batch_id: str, *, request_options: RequestOptions | None = None
    ) -> BatchRun:
        raw = self._transport.request(
            "POST",
            f"/testing/batches/{batch_id}/run",
            request_options=request_options,
        )
        return BatchRun.model_validate(raw)

    def runs(
        self,
        batch_id: str,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[BatchRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET",
                f"/testing/batches/{batch_id}/runs",
                params=p,
                request_options=request_options,
            )

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=BatchRun, items_key="runs"
        )

    def list_runs(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[BatchRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/testing/batch-runs", params=p, request_options=request_options
            )

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=BatchRun, items_key="runs"
        )

    def get_run(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> BatchRun:
        raw = self._transport.request(
            "GET", f"/testing/batch-runs/{run_id}", request_options=request_options
        )
        return BatchRun.model_validate(raw)

    def wait_for_run(
        self,
        run_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Callable[[BatchRun], None] | None = None,
        request_options: RequestOptions | None = None,
    ) -> BatchRun:
        def fetch() -> BatchRun:
            return self.get_run(run_id, request_options=request_options)

        return wait_for_sync(
            fetch=fetch,
            is_terminal=lambda r: r.status in RUN_TERMINAL_STATUSES,
            timeout=timeout,
            initial_interval=poll_interval,
            on_update=on_update,
        )


class AsyncBatchesResource(AsyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[Batch]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/testing/batches", params=p, request_options=request_options
            )

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=Batch, items_key="batches"
        )

    async def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[Batch]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/testing/batches", params=params, request_options=request_options
        )
        raw_items = raw.get("batches", raw.get("items", []))
        items = [Batch.model_validate(i) for i in raw_items]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, batch_id: str, *, request_options: RequestOptions | None = None
    ) -> Batch:
        raw = await self._transport.request(
            "GET", f"/testing/batches/{batch_id}", request_options=request_options
        )
        return Batch.model_validate(raw)

    async def create(
        self,
        *,
        name: str,
        config_id: str,
        dataset_id: str,
        request_options: RequestOptions | None = None,
    ) -> Batch:
        raw = await self._transport.request(
            "POST",
            "/testing/batches",
            json={"name": name, "configId": config_id, "datasetId": dataset_id},
            request_options=request_options,
        )
        return Batch.model_validate(raw)

    async def update(
        self,
        batch_id: str,
        *,
        name: str | None = None,
        dataset_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Batch:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if dataset_id is not None:
            body["datasetId"] = dataset_id
        raw = await self._transport.request(
            "PUT",
            f"/testing/batches/{batch_id}",
            json=body,
            request_options=request_options,
        )
        return Batch.model_validate(raw)

    async def delete(
        self, batch_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        await self._transport.request(
            "DELETE", f"/testing/batches/{batch_id}", request_options=request_options
        )

    async def run(
        self, batch_id: str, *, request_options: RequestOptions | None = None
    ) -> BatchRun:
        raw = await self._transport.request(
            "POST",
            f"/testing/batches/{batch_id}/run",
            request_options=request_options,
        )
        return BatchRun.model_validate(raw)

    def runs(
        self,
        batch_id: str,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[BatchRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET",
                f"/testing/batches/{batch_id}/runs",
                params=p,
                request_options=request_options,
            )

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=BatchRun, items_key="runs"
        )

    def list_runs(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[BatchRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/testing/batch-runs", params=p, request_options=request_options
            )

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=BatchRun, items_key="runs"
        )

    async def get_run(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> BatchRun:
        raw = await self._transport.request(
            "GET", f"/testing/batch-runs/{run_id}", request_options=request_options
        )
        return BatchRun.model_validate(raw)

    async def wait_for_run(
        self,
        run_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Callable[[BatchRun], None] | None = None,
        request_options: RequestOptions | None = None,
    ) -> BatchRun:
        async def fetch() -> BatchRun:
            return await self.get_run(run_id, request_options=request_options)

        return await wait_for_async(
            fetch=fetch,
            is_terminal=lambda r: r.status in RUN_TERMINAL_STATUSES,
            timeout=timeout,
            initial_interval=poll_interval,
            on_update=on_update,
        )
