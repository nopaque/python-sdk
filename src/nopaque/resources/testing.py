"""Testing resource - /testing/configs, /testing/jobs, /testing/runs."""
from __future__ import annotations

from typing import Any, Callable, List, Optional, Set

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._polling import wait_for_async, wait_for_sync
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from .._transport import AsyncTransport, SyncTransport
from ..models.testing import TestConfig, TestJob, TestRun

RUN_TERMINAL_STATUSES: Set[str] = {"completed", "failed", "cancelled"}


# ==== Sync sub-namespaces =====================================================


class _SyncConfigs:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> SyncPaginator[TestConfig]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/testing/configs", params=p, request_options=request_options
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=TestConfig)

    def list_page(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Page[TestConfig]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/testing/configs", params=params, request_options=request_options
        )
        items = [TestConfig.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, config_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> TestConfig:
        raw = self._transport.request(
            "GET", f"/testing/configs/{config_id}", request_options=request_options
        )
        return TestConfig.model_validate(raw)

    def create(
        self,
        *,
        name: str,
        phone_number: str,
        steps: List[Any],
        request_options: Optional[RequestOptions] = None,
    ) -> TestConfig:
        raw = self._transport.request(
            "POST",
            "/testing/configs",
            json={"name": name, "phoneNumber": phone_number, "steps": steps},
            request_options=request_options,
        )
        return TestConfig.model_validate(raw)

    def update(
        self,
        config_id: str,
        *,
        name: Optional[str] = None,
        phone_number: Optional[str] = None,
        steps: Optional[List[Any]] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> TestConfig:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if phone_number is not None:
            body["phoneNumber"] = phone_number
        if steps is not None:
            body["steps"] = steps
        raw = self._transport.request(
            "PUT",
            f"/testing/configs/{config_id}",
            json=body,
            request_options=request_options,
        )
        return TestConfig.model_validate(raw)

    def delete(
        self, config_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> None:
        self._transport.request(
            "DELETE", f"/testing/configs/{config_id}", request_options=request_options
        )


class _SyncJobs:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> SyncPaginator[TestJob]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/testing/jobs", params=p, request_options=request_options
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=TestJob)

    def list_page(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Page[TestJob]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/testing/jobs", params=params, request_options=request_options
        )
        items = [TestJob.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> TestJob:
        raw = self._transport.request(
            "GET", f"/testing/jobs/{job_id}", request_options=request_options
        )
        return TestJob.model_validate(raw)

    def create(
        self,
        *,
        config_id: str,
        name: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> TestJob:
        body: dict = {"configId": config_id}
        if name is not None:
            body["name"] = name
        raw = self._transport.request(
            "POST", "/testing/jobs", json=body, request_options=request_options
        )
        return TestJob.model_validate(raw)

    def delete(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> None:
        self._transport.request(
            "DELETE", f"/testing/jobs/{job_id}", request_options=request_options
        )


class _SyncRuns:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> SyncPaginator[TestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/testing/runs", params=p, request_options=request_options
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=TestRun)

    def list_page(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Page[TestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/testing/runs", params=params, request_options=request_options
        )
        items = [TestRun.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, run_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> TestRun:
        raw = self._transport.request(
            "GET", f"/testing/runs/{run_id}", request_options=request_options
        )
        return TestRun.model_validate(raw)

    def create(
        self,
        *,
        job_id: str,
        request_options: Optional[RequestOptions] = None,
    ) -> TestRun:
        raw = self._transport.request(
            "POST",
            "/testing/runs",
            json={"jobId": job_id},
            request_options=request_options,
        )
        return TestRun.model_validate(raw)

    def wait_for_run(
        self,
        run_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Optional[Callable[[TestRun], None]] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> TestRun:
        def fetch() -> TestRun:
            return self.get(run_id, request_options=request_options)

        return wait_for_sync(
            fetch=fetch,
            is_terminal=lambda r: r.status in RUN_TERMINAL_STATUSES,
            timeout=timeout,
            initial_interval=poll_interval,
            on_update=on_update,
        )


class TestingResource(SyncResource):
    """Synchronous /testing/* endpoints. Nested: configs, jobs, runs."""

    def __init__(self, transport: SyncTransport) -> None:
        super().__init__(transport)
        self.configs = _SyncConfigs(transport)
        self.jobs = _SyncJobs(transport)
        self.runs = _SyncRuns(transport)


# ==== Async sub-namespaces ====================================================


class _AsyncConfigs:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> AsyncPaginator[TestConfig]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/testing/configs", params=p, request_options=request_options
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=TestConfig)

    async def list_page(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Page[TestConfig]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/testing/configs", params=params, request_options=request_options
        )
        items = [TestConfig.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, config_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> TestConfig:
        raw = await self._transport.request(
            "GET", f"/testing/configs/{config_id}", request_options=request_options
        )
        return TestConfig.model_validate(raw)

    async def create(
        self,
        *,
        name: str,
        phone_number: str,
        steps: List[Any],
        request_options: Optional[RequestOptions] = None,
    ) -> TestConfig:
        raw = await self._transport.request(
            "POST",
            "/testing/configs",
            json={"name": name, "phoneNumber": phone_number, "steps": steps},
            request_options=request_options,
        )
        return TestConfig.model_validate(raw)

    async def update(
        self,
        config_id: str,
        *,
        name: Optional[str] = None,
        phone_number: Optional[str] = None,
        steps: Optional[List[Any]] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> TestConfig:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if phone_number is not None:
            body["phoneNumber"] = phone_number
        if steps is not None:
            body["steps"] = steps
        raw = await self._transport.request(
            "PUT",
            f"/testing/configs/{config_id}",
            json=body,
            request_options=request_options,
        )
        return TestConfig.model_validate(raw)

    async def delete(
        self, config_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> None:
        await self._transport.request(
            "DELETE", f"/testing/configs/{config_id}", request_options=request_options
        )


class _AsyncJobs:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> AsyncPaginator[TestJob]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/testing/jobs", params=p, request_options=request_options
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=TestJob)

    async def list_page(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Page[TestJob]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/testing/jobs", params=params, request_options=request_options
        )
        items = [TestJob.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> TestJob:
        raw = await self._transport.request(
            "GET", f"/testing/jobs/{job_id}", request_options=request_options
        )
        return TestJob.model_validate(raw)

    async def create(
        self,
        *,
        config_id: str,
        name: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> TestJob:
        body: dict = {"configId": config_id}
        if name is not None:
            body["name"] = name
        raw = await self._transport.request(
            "POST", "/testing/jobs", json=body, request_options=request_options
        )
        return TestJob.model_validate(raw)

    async def delete(
        self, job_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> None:
        await self._transport.request(
            "DELETE", f"/testing/jobs/{job_id}", request_options=request_options
        )


class _AsyncRuns:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> AsyncPaginator[TestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/testing/runs", params=p, request_options=request_options
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=TestRun)

    async def list_page(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Page[TestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/testing/runs", params=params, request_options=request_options
        )
        items = [TestRun.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, run_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> TestRun:
        raw = await self._transport.request(
            "GET", f"/testing/runs/{run_id}", request_options=request_options
        )
        return TestRun.model_validate(raw)

    async def create(
        self,
        *,
        job_id: str,
        request_options: Optional[RequestOptions] = None,
    ) -> TestRun:
        raw = await self._transport.request(
            "POST",
            "/testing/runs",
            json={"jobId": job_id},
            request_options=request_options,
        )
        return TestRun.model_validate(raw)

    async def wait_for_run(
        self,
        run_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Optional[Callable[[TestRun], None]] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> TestRun:
        async def fetch() -> TestRun:
            return await self.get(run_id, request_options=request_options)

        return await wait_for_async(
            fetch=fetch,
            is_terminal=lambda r: r.status in RUN_TERMINAL_STATUSES,
            timeout=timeout,
            initial_interval=poll_interval,
            on_update=on_update,
        )


class AsyncTestingResource(AsyncResource):
    """Asynchronous /testing/* endpoints. Nested: configs, jobs, runs."""

    def __init__(self, transport: AsyncTransport) -> None:
        super().__init__(transport)
        self.configs = _AsyncConfigs(transport)
        self.jobs = _AsyncJobs(transport)
        self.runs = _AsyncRuns(transport)
