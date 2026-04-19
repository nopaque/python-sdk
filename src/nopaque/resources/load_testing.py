"""Load testing resource - /testing/load-tests."""
from __future__ import annotations

from typing import Callable, Optional, Set

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._polling import wait_for_async, wait_for_sync
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.load_testing import (
    LoadTest,
    LoadTestEstimate,
    LoadTestRun,
    LoadTestStatus,
)

TERMINAL_STATUSES: Set[str] = {"completed", "aborted", "failed"}


class LoadTestingResource(SyncResource):
    def list(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> SyncPaginator[LoadTest]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/testing/load-tests", params=p, request_options=request_options
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=LoadTest)

    def list_page(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Page[LoadTest]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/testing/load-tests", params=params, request_options=request_options
        )
        items = [LoadTest.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, load_test_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> LoadTest:
        raw = self._transport.request(
            "GET",
            f"/testing/load-tests/{load_test_id}",
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    def create(
        self,
        *,
        name: str,
        config_id: str,
        concurrency: int,
        total_calls: int,
        request_options: Optional[RequestOptions] = None,
    ) -> LoadTest:
        raw = self._transport.request(
            "POST",
            "/testing/load-tests",
            json={
                "name": name,
                "configId": config_id,
                "concurrency": concurrency,
                "totalCalls": total_calls,
            },
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    def update(
        self,
        load_test_id: str,
        *,
        name: Optional[str] = None,
        concurrency: Optional[int] = None,
        total_calls: Optional[int] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> LoadTest:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if concurrency is not None:
            body["concurrency"] = concurrency
        if total_calls is not None:
            body["totalCalls"] = total_calls
        raw = self._transport.request(
            "PUT",
            f"/testing/load-tests/{load_test_id}",
            json=body,
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    def delete(
        self, load_test_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> None:
        self._transport.request(
            "DELETE",
            f"/testing/load-tests/{load_test_id}",
            request_options=request_options,
        )

    def estimate(
        self,
        *,
        config_id: str,
        concurrency: int,
        total_calls: int,
        request_options: Optional[RequestOptions] = None,
    ) -> LoadTestEstimate:
        raw = self._transport.request(
            "POST",
            "/testing/load-tests/estimate",
            json={
                "configId": config_id,
                "concurrency": concurrency,
                "totalCalls": total_calls,
            },
            request_options=request_options,
        )
        return LoadTestEstimate.model_validate(raw)

    def start(
        self, load_test_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> LoadTest:
        raw = self._transport.request(
            "POST",
            f"/testing/load-tests/{load_test_id}/start",
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    def abort(
        self, load_test_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> LoadTest:
        raw = self._transport.request(
            "POST",
            f"/testing/load-tests/{load_test_id}/abort",
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    def status(
        self, load_test_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> LoadTestStatus:
        raw = self._transport.request(
            "GET",
            f"/testing/load-tests/{load_test_id}/status",
            request_options=request_options,
        )
        return LoadTestStatus.model_validate(raw)

    def list_runs(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> SyncPaginator[LoadTestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET",
                "/testing/load-tests/runs",
                params=p,
                request_options=request_options,
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=LoadTestRun)

    def wait_for_complete(
        self,
        load_test_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Optional[Callable[[LoadTestStatus], None]] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> LoadTestStatus:
        def fetch() -> LoadTestStatus:
            return self.status(load_test_id, request_options=request_options)

        return wait_for_sync(
            fetch=fetch,
            is_terminal=lambda s: s.status in TERMINAL_STATUSES,
            timeout=timeout,
            initial_interval=poll_interval,
            on_update=on_update,
        )


class AsyncLoadTestingResource(AsyncResource):
    def list(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> AsyncPaginator[LoadTest]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/testing/load-tests", params=p, request_options=request_options
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=LoadTest)

    async def list_page(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Page[LoadTest]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/testing/load-tests", params=params, request_options=request_options
        )
        items = [LoadTest.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, load_test_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> LoadTest:
        raw = await self._transport.request(
            "GET",
            f"/testing/load-tests/{load_test_id}",
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    async def create(
        self,
        *,
        name: str,
        config_id: str,
        concurrency: int,
        total_calls: int,
        request_options: Optional[RequestOptions] = None,
    ) -> LoadTest:
        raw = await self._transport.request(
            "POST",
            "/testing/load-tests",
            json={
                "name": name,
                "configId": config_id,
                "concurrency": concurrency,
                "totalCalls": total_calls,
            },
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    async def update(
        self,
        load_test_id: str,
        *,
        name: Optional[str] = None,
        concurrency: Optional[int] = None,
        total_calls: Optional[int] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> LoadTest:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if concurrency is not None:
            body["concurrency"] = concurrency
        if total_calls is not None:
            body["totalCalls"] = total_calls
        raw = await self._transport.request(
            "PUT",
            f"/testing/load-tests/{load_test_id}",
            json=body,
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    async def delete(
        self, load_test_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> None:
        await self._transport.request(
            "DELETE",
            f"/testing/load-tests/{load_test_id}",
            request_options=request_options,
        )

    async def estimate(
        self,
        *,
        config_id: str,
        concurrency: int,
        total_calls: int,
        request_options: Optional[RequestOptions] = None,
    ) -> LoadTestEstimate:
        raw = await self._transport.request(
            "POST",
            "/testing/load-tests/estimate",
            json={
                "configId": config_id,
                "concurrency": concurrency,
                "totalCalls": total_calls,
            },
            request_options=request_options,
        )
        return LoadTestEstimate.model_validate(raw)

    async def start(
        self, load_test_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> LoadTest:
        raw = await self._transport.request(
            "POST",
            f"/testing/load-tests/{load_test_id}/start",
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    async def abort(
        self, load_test_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> LoadTest:
        raw = await self._transport.request(
            "POST",
            f"/testing/load-tests/{load_test_id}/abort",
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    async def status(
        self, load_test_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> LoadTestStatus:
        raw = await self._transport.request(
            "GET",
            f"/testing/load-tests/{load_test_id}/status",
            request_options=request_options,
        )
        return LoadTestStatus.model_validate(raw)

    def list_runs(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> AsyncPaginator[LoadTestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET",
                "/testing/load-tests/runs",
                params=p,
                request_options=request_options,
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=LoadTestRun)

    async def wait_for_complete(
        self,
        load_test_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Optional[Callable[[LoadTestStatus], None]] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> LoadTestStatus:
        async def fetch() -> LoadTestStatus:
            return await self.status(load_test_id, request_options=request_options)

        return await wait_for_async(
            fetch=fetch,
            is_terminal=lambda s: s.status in TERMINAL_STATUSES,
            timeout=timeout,
            initial_interval=poll_interval,
            on_update=on_update,
        )
