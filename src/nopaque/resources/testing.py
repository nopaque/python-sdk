"""Testing resource - /testing/configs, /testing/jobs, /testing/runs."""
from __future__ import annotations

import builtins
from typing import Any, Callable

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._polling import wait_for_async, wait_for_sync
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from .._transport import AsyncTransport, SyncTransport
from ..models.testing import TestConfig, TestJob, TestRun

RUN_TERMINAL_STATUSES: set[str] = {"completed", "failed", "cancelled"}


# ==== Sync sub-namespaces =====================================================


class _SyncConfigs:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[TestConfig]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            # Server returns { configs: [...] } rather than { items, nextToken }.
            # Normalize to the paginator's expected shape.
            raw = self._transport.request(
                "GET", "/testing/configs", params=p, request_options=request_options
            )
            return {"items": raw.get("configs", raw.get("items", [])), "nextToken": None}

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=TestConfig)

    def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[TestConfig]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/testing/configs", params=params, request_options=request_options
        )
        items = [TestConfig.model_validate(i) for i in raw.get("configs", raw.get("items", []))]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, config_id: str, *, request_options: RequestOptions | None = None
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
        steps: builtins.list[Any],
        request_options: RequestOptions | None = None,
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
        name: str | None = None,
        phone_number: str | None = None,
        steps: builtins.list[Any] | None = None,
        request_options: RequestOptions | None = None,
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
        self, config_id: str, *, request_options: RequestOptions | None = None
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
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[TestJob]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            # Server returns { jobs: [...] } rather than { items, nextToken }.
            raw = self._transport.request(
                "GET", "/testing/jobs", params=p, request_options=request_options
            )
            return {"items": raw.get("jobs", raw.get("items", [])), "nextToken": None}

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=TestJob)

    def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[TestJob]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/testing/jobs", params=params, request_options=request_options
        )
        items = [TestJob.model_validate(i) for i in raw.get("jobs", raw.get("items", []))]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, job_id: str, *, request_options: RequestOptions | None = None
    ) -> TestJob:
        raw = self._transport.request(
            "GET", f"/testing/jobs/{job_id}", request_options=request_options
        )
        return TestJob.model_validate(raw)

    def create(
        self,
        *,
        config_id: str,
        name: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> TestJob:
        body: dict = {"configId": config_id}
        if name is not None:
            body["name"] = name
        raw = self._transport.request(
            "POST", "/testing/jobs", json=body, request_options=request_options
        )
        return TestJob.model_validate(raw)

    def delete(
        self, job_id: str, *, request_options: RequestOptions | None = None
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
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[TestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            # Server returns { runs: [...] } rather than { items, nextToken }.
            raw = self._transport.request(
                "GET", "/testing/runs", params=p, request_options=request_options
            )
            return {"items": raw.get("runs", raw.get("items", [])), "nextToken": None}

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=TestRun)

    def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[TestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/testing/runs", params=params, request_options=request_options
        )
        items = [TestRun.model_validate(i) for i in raw.get("runs", raw.get("items", []))]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> TestRun:
        raw = self._transport.request(
            "GET", f"/testing/runs/{run_id}", request_options=request_options
        )
        return TestRun.model_validate(raw)

    def create(
        self,
        *,
        job_id: str | None = None,
        test_config_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> TestRun:
        """Start a test run from an existing test job OR directly from a test config.

        Pass exactly one of `job_id` or `test_config_id`.
        """
        if bool(job_id) == bool(test_config_id):
            raise ValueError(
                "Pass exactly one of job_id or test_config_id"
            )
        body: dict = {"jobId": job_id} if job_id else {"testConfigId": test_config_id}
        raw = self._transport.request(
            "POST",
            "/testing/runs",
            json=body,
            request_options=request_options,
        )
        # POST returns { message, run } — unwrap the run object.
        return TestRun.model_validate(raw.get("run", raw))

    def wait_for_run(
        self,
        run_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Callable[[TestRun], None] | None = None,
        request_options: RequestOptions | None = None,
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
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[TestConfig]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            raw = await self._transport.request(
                "GET", "/testing/configs", params=p, request_options=request_options
            )
            return {"items": raw.get("configs", raw.get("items", [])), "nextToken": None}

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=TestConfig)

    async def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[TestConfig]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/testing/configs", params=params, request_options=request_options
        )
        items = [TestConfig.model_validate(i) for i in raw.get("configs", raw.get("items", []))]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, config_id: str, *, request_options: RequestOptions | None = None
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
        steps: builtins.list[Any],
        request_options: RequestOptions | None = None,
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
        name: str | None = None,
        phone_number: str | None = None,
        steps: builtins.list[Any] | None = None,
        request_options: RequestOptions | None = None,
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
        self, config_id: str, *, request_options: RequestOptions | None = None
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
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[TestJob]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            raw = await self._transport.request(
                "GET", "/testing/jobs", params=p, request_options=request_options
            )
            return {"items": raw.get("jobs", raw.get("items", [])), "nextToken": None}

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=TestJob)

    async def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[TestJob]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/testing/jobs", params=params, request_options=request_options
        )
        items = [TestJob.model_validate(i) for i in raw.get("jobs", raw.get("items", []))]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, job_id: str, *, request_options: RequestOptions | None = None
    ) -> TestJob:
        raw = await self._transport.request(
            "GET", f"/testing/jobs/{job_id}", request_options=request_options
        )
        return TestJob.model_validate(raw)

    async def create(
        self,
        *,
        config_id: str,
        name: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> TestJob:
        body: dict = {"configId": config_id}
        if name is not None:
            body["name"] = name
        raw = await self._transport.request(
            "POST", "/testing/jobs", json=body, request_options=request_options
        )
        return TestJob.model_validate(raw)

    async def delete(
        self, job_id: str, *, request_options: RequestOptions | None = None
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
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[TestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            raw = await self._transport.request(
                "GET", "/testing/runs", params=p, request_options=request_options
            )
            return {"items": raw.get("runs", raw.get("items", [])), "nextToken": None}

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=TestRun)

    async def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[TestRun]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/testing/runs", params=params, request_options=request_options
        )
        items = [TestRun.model_validate(i) for i in raw.get("runs", raw.get("items", []))]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> TestRun:
        raw = await self._transport.request(
            "GET", f"/testing/runs/{run_id}", request_options=request_options
        )
        return TestRun.model_validate(raw)

    async def create(
        self,
        *,
        job_id: str | None = None,
        test_config_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> TestRun:
        """Start a test run from an existing test job OR directly from a test config.

        Pass exactly one of `job_id` or `test_config_id`.
        """
        if bool(job_id) == bool(test_config_id):
            raise ValueError(
                "Pass exactly one of job_id or test_config_id"
            )
        body: dict = {"jobId": job_id} if job_id else {"testConfigId": test_config_id}
        raw = await self._transport.request(
            "POST",
            "/testing/runs",
            json=body,
            request_options=request_options,
        )
        # POST returns { message, run } — unwrap the run object.
        return TestRun.model_validate(raw.get("run", raw))

    async def wait_for_run(
        self,
        run_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Callable[[TestRun], None] | None = None,
        request_options: RequestOptions | None = None,
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
