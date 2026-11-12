"""Load testing resource - /testing/load-tests, plus the run reports
(/testing/reports), exports and failure patterns that hang off a load-test run.
"""
from __future__ import annotations

from typing import Callable, List, Optional

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._polling import wait_for_async, wait_for_sync
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.load_testing import (
    FailurePatternCall,
    FailurePatternScope,
    LoadTest,
    LoadTestEstimate,
    LoadTestExport,
    LoadTestFailurePatterns,
    LoadTestRun,
    LoadTestStatus,
    ReclassifyFailurePatternsResponse,
    Report,
    ReportFileDownload,
    ReportPack,
)

TERMINAL_STATUSES: set[str] = {"completed", "aborted", "failed"}


def _cursor_params(
    *, limit: Optional[int], cursor: Optional[str], scope: Optional[str] = None
) -> dict:
    params: dict = {}
    if scope is not None:
        params["scope"] = scope
    if limit is not None:
        params["limit"] = limit
    if cursor is not None:
        params["cursor"] = cursor
    return params


def _apply_cursor(params: dict) -> dict:
    """Translate the paginator's injected `nextToken` into the api's `cursor`."""
    p = dict(params)
    if "nextToken" in p:
        p["cursor"] = p.pop("nextToken")
    return p


def _reports_page(raw: dict) -> dict:
    """`{reports, nextCursor}` -> the paginator's `{items, nextToken}`."""
    return {"items": raw.get("reports", []), "nextToken": raw.get("nextCursor")}


def _calls_page(raw: dict) -> dict:
    """`{items, cursor}` -> the paginator's `{items, nextToken}`."""
    return {"items": raw.get("items", []), "nextToken": raw.get("cursor")}


def _report_body(
    *,
    load_test_run_ids: List[str],
    name: Optional[str],
    packs: Optional[List[ReportPack]],
    include_audio: Optional[bool],
) -> dict:
    body: dict = {"loadTestRunIds": list(load_test_run_ids)}
    if name is not None:
        body["name"] = name
    if packs is not None:
        body["packs"] = list(packs)
    if include_audio is not None:
        body["includeAudio"] = include_audio
    return body


def _scope_params(scope: Optional[str]) -> Optional[dict]:
    return {"scope": scope} if scope is not None else None


class LoadTestingResource(SyncResource):
    """Synchronous /testing/load-tests endpoints, plus the reports, exports and
    failure patterns of load-test runs."""

    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
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

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=LoadTest, items_key="configs"
        )

    def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[LoadTest]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/testing/load-tests", params=params, request_options=request_options
        )
        raw_items = raw.get("configs", raw.get("items", []))
        items = [LoadTest.model_validate(i) for i in raw_items]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, load_test_id: str, *, request_options: RequestOptions | None = None
    ) -> LoadTest:
        raw = self._transport.request(
            "GET",
            f"/testing/load-tests/{load_test_id}",
            request_options=request_options,
        )
        # GET /testing/load-tests/{id} returns the config fields flat with a
        # `testConfig` sibling — not wrapped in `{config: ...}`.
        return LoadTest.model_validate(raw)

    def create(
        self,
        *,
        name: str,
        config_id: str,
        concurrency: int,
        total_calls: int,
        request_options: RequestOptions | None = None,
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
        # POST returns {config: {...}} — unwrap.
        return LoadTest.model_validate(raw.get("config", raw))

    def update(
        self,
        load_test_id: str,
        *,
        name: str | None = None,
        concurrency: int | None = None,
        total_calls: int | None = None,
        request_options: RequestOptions | None = None,
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
        # PUT returns {config: updated} — unwrap.
        return LoadTest.model_validate(raw.get("config", raw))

    def delete(
        self, load_test_id: str, *, request_options: RequestOptions | None = None
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
        request_options: RequestOptions | None = None,
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
        self, load_test_id: str, *, request_options: RequestOptions | None = None
    ) -> LoadTest:
        raw = self._transport.request(
            "POST",
            f"/testing/load-tests/{load_test_id}/start",
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    def abort(
        self, load_test_id: str, *, request_options: RequestOptions | None = None
    ) -> LoadTest:
        raw = self._transport.request(
            "POST",
            f"/testing/load-tests/{load_test_id}/abort",
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    def status(
        self, load_test_id: str, *, request_options: RequestOptions | None = None
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
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
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

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=LoadTestRun, items_key="runs"
        )

    def wait_for_complete(
        self,
        load_test_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Callable[[LoadTestStatus], None] | None = None,
        request_options: RequestOptions | None = None,
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

    def create_report(
        self,
        *,
        load_test_run_ids: List[str],
        name: str | None = None,
        packs: List[ReportPack] | None = None,
        include_audio: bool | None = None,
        request_options: RequestOptions | None = None,
    ) -> Report:
        """Start building a report over 1-20 finished load-test runs.

        ``packs`` picks the files to build (``data``, ``excel``, ``pdf``;
        default all three). ``include_audio`` puts call recordings in the data
        pack (server default True). The build runs in the background: poll
        :meth:`get_report` until ``status`` is ``ready`` or ``failed``, then
        fetch each file with :meth:`get_report_file_url`.
        """
        raw = self._transport.request(
            "POST",
            "/testing/reports",
            json=_report_body(
                load_test_run_ids=load_test_run_ids,
                name=name,
                packs=packs,
                include_audio=include_audio,
            ),
            request_options=request_options,
        )
        return Report.model_validate(raw.get("report", raw))

    def list_reports(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[Report]:
        """The workspace's reports, newest first. Iterates every page."""
        params = _cursor_params(limit=limit, cursor=cursor)

        def fetch(p: dict) -> dict:
            raw = self._transport.request(
                "GET",
                "/testing/reports",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return _reports_page(raw)

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=Report)

    def list_reports_page(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[Report]:
        """One page of reports. Pass ``next_token`` back as ``cursor``."""
        raw = self._transport.request(
            "GET",
            "/testing/reports",
            params=_cursor_params(limit=limit, cursor=cursor),
            request_options=request_options,
        )
        items = [Report.model_validate(r) for r in raw.get("reports", [])]
        return Page(items=items, next_token=raw.get("nextCursor"))

    def get_report(
        self, report_id: str, *, request_options: RequestOptions | None = None
    ) -> Report:
        raw = self._transport.request(
            "GET", f"/testing/reports/{report_id}", request_options=request_options
        )
        return Report.model_validate(raw.get("report", raw))

    def delete_report(
        self, report_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        """Permanently delete a finished report and its files.

        A report still ``pending`` or ``running`` cannot be deleted
        (``ConflictError``). The load-test runs it covered are not touched.
        """
        self._transport.request(
            "DELETE", f"/testing/reports/{report_id}", request_options=request_options
        )

    def get_report_file_url(
        self,
        report_id: str,
        pack: ReportPack,
        *,
        request_options: RequestOptions | None = None,
    ) -> ReportFileDownload:
        """A pre-signed link to one of the report's files, valid for 1 hour.

        Call again for a fresh link.
        """
        raw = self._transport.request(
            "GET",
            f"/testing/reports/{report_id}/files/{pack}",
            request_options=request_options,
        )
        return ReportFileDownload.model_validate(raw)

    def create_export(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> LoadTestExport:
        """Start building a zip of every call and step in the run.

        If an export of the run is already in progress it is returned instead
        of starting another. Poll :meth:`get_export` until ``status`` is ``ready``,
        then download from ``download_url``.
        """
        raw = self._transport.request(
            "POST",
            f"/testing/load-tests/{run_id}/exports",
            request_options=request_options,
        )
        return LoadTestExport.model_validate(raw.get("export", raw))

    def list_exports(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> List[LoadTestExport]:
        """The run's exports, newest first (at most 20). Not paginated."""
        raw = self._transport.request(
            "GET",
            f"/testing/load-tests/{run_id}/exports",
            request_options=request_options,
        )
        return [LoadTestExport.model_validate(e) for e in raw.get("exports", [])]

    def get_export(
        self,
        run_id: str,
        export_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> LoadTestExport:
        """One export. When ``ready``, ``download_url`` is valid for 1 hour;
        call again for a fresh one."""
        raw = self._transport.request(
            "GET",
            f"/testing/load-tests/{run_id}/exports/{export_id}",
            request_options=request_options,
        )
        return LoadTestExport.model_validate(raw.get("export", raw))

    def get_failure_patterns(
        self,
        run_id: str,
        *,
        scope: FailurePatternScope | None = None,
        request_options: RequestOptions | None = None,
    ) -> LoadTestFailurePatterns:
        """A load-test run's failed calls grouped into named patterns.

        ``run_id`` is the load-test RUN id, not the config id, as for every
        report, export and failure-pattern method. ``scope`` is ``group`` (the
        server default: every lane started with the run) or ``lane`` (this run
        only).
        """
        raw = self._transport.request(
            "GET",
            f"/testing/load-tests/{run_id}/failure-patterns",
            params=_scope_params(scope),
            request_options=request_options,
        )
        return LoadTestFailurePatterns.model_validate(raw)

    def reclassify_failure_patterns(
        self,
        run_id: str,
        *,
        scope: FailurePatternScope | None = None,
        request_options: RequestOptions | None = None,
    ) -> ReclassifyFailurePatternsResponse:
        """Rerun the current rules over every call of the run, in the background.

        Use for runs from before failure patterns, or after a rule change.
        Returns at once with a ``job_id``.
        """
        raw = self._transport.request(
            "POST",
            f"/testing/load-tests/{run_id}/failure-patterns/reclassify",
            params=_scope_params(scope),
            request_options=request_options,
        )
        return ReclassifyFailurePatternsResponse.model_validate(raw)

    def list_failure_pattern_calls(
        self,
        run_id: str,
        pattern_id: str,
        *,
        scope: FailurePatternScope | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[FailurePatternCall]:
        """The calls in one pattern, oldest first. Iterates every page.

        ``pattern_id`` is a pattern's ``id`` (``P1``, ``P2a``, ...,
        ``UNCLASSIFIED``) or ``LATE_START`` for the calls that started late.
        """
        params = _cursor_params(limit=limit, cursor=cursor, scope=scope)

        def fetch(p: dict) -> dict:
            raw = self._transport.request(
                "GET",
                f"/testing/load-tests/{run_id}/failure-patterns/{pattern_id}/calls",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return _calls_page(raw)

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=FailurePatternCall)

    def list_failure_pattern_calls_page(
        self,
        run_id: str,
        pattern_id: str,
        *,
        scope: FailurePatternScope | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[FailurePatternCall]:
        """One page of a pattern's calls. Pass ``next_token`` back as ``cursor``."""
        raw = self._transport.request(
            "GET",
            f"/testing/load-tests/{run_id}/failure-patterns/{pattern_id}/calls",
            params=_cursor_params(limit=limit, cursor=cursor, scope=scope),
            request_options=request_options,
        )
        items = [FailurePatternCall.model_validate(c) for c in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("cursor"))


class AsyncLoadTestingResource(AsyncResource):
    """Asynchronous /testing/load-tests endpoints, plus the reports, exports and
    failure patterns of load-test runs."""

    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
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

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=LoadTest, items_key="configs"
        )

    async def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[LoadTest]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/testing/load-tests", params=params, request_options=request_options
        )
        raw_items = raw.get("configs", raw.get("items", []))
        items = [LoadTest.model_validate(i) for i in raw_items]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, load_test_id: str, *, request_options: RequestOptions | None = None
    ) -> LoadTest:
        raw = await self._transport.request(
            "GET",
            f"/testing/load-tests/{load_test_id}",
            request_options=request_options,
        )
        # GET /testing/load-tests/{id} returns the config fields flat with a
        # `testConfig` sibling — not wrapped in `{config: ...}`.
        return LoadTest.model_validate(raw)

    async def create(
        self,
        *,
        name: str,
        config_id: str,
        concurrency: int,
        total_calls: int,
        request_options: RequestOptions | None = None,
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
        # POST returns {config: {...}} — unwrap.
        return LoadTest.model_validate(raw.get("config", raw))

    async def update(
        self,
        load_test_id: str,
        *,
        name: str | None = None,
        concurrency: int | None = None,
        total_calls: int | None = None,
        request_options: RequestOptions | None = None,
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
        # PUT returns {config: updated} — unwrap.
        return LoadTest.model_validate(raw.get("config", raw))

    async def delete(
        self, load_test_id: str, *, request_options: RequestOptions | None = None
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
        request_options: RequestOptions | None = None,
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
        self, load_test_id: str, *, request_options: RequestOptions | None = None
    ) -> LoadTest:
        raw = await self._transport.request(
            "POST",
            f"/testing/load-tests/{load_test_id}/start",
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    async def abort(
        self, load_test_id: str, *, request_options: RequestOptions | None = None
    ) -> LoadTest:
        raw = await self._transport.request(
            "POST",
            f"/testing/load-tests/{load_test_id}/abort",
            request_options=request_options,
        )
        return LoadTest.model_validate(raw)

    async def status(
        self, load_test_id: str, *, request_options: RequestOptions | None = None
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
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
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

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=LoadTestRun, items_key="runs"
        )

    async def wait_for_complete(
        self,
        load_test_id: str,
        *,
        timeout: float = 600.0,
        poll_interval: float = 5.0,
        on_update: Callable[[LoadTestStatus], None] | None = None,
        request_options: RequestOptions | None = None,
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

    async def create_report(
        self,
        *,
        load_test_run_ids: List[str],
        name: str | None = None,
        packs: List[ReportPack] | None = None,
        include_audio: bool | None = None,
        request_options: RequestOptions | None = None,
    ) -> Report:
        """Start building a report over 1-20 finished load-test runs.

        See :meth:`LoadTestingResource.create_report`.
        """
        raw = await self._transport.request(
            "POST",
            "/testing/reports",
            json=_report_body(
                load_test_run_ids=load_test_run_ids,
                name=name,
                packs=packs,
                include_audio=include_audio,
            ),
            request_options=request_options,
        )
        return Report.model_validate(raw.get("report", raw))

    def list_reports(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[Report]:
        """The workspace's reports, newest first. Iterates every page."""
        params = _cursor_params(limit=limit, cursor=cursor)

        async def fetch(p: dict) -> dict:
            raw = await self._transport.request(
                "GET",
                "/testing/reports",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return _reports_page(raw)

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=Report)

    async def list_reports_page(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[Report]:
        raw = await self._transport.request(
            "GET",
            "/testing/reports",
            params=_cursor_params(limit=limit, cursor=cursor),
            request_options=request_options,
        )
        items = [Report.model_validate(r) for r in raw.get("reports", [])]
        return Page(items=items, next_token=raw.get("nextCursor"))

    async def get_report(
        self, report_id: str, *, request_options: RequestOptions | None = None
    ) -> Report:
        raw = await self._transport.request(
            "GET", f"/testing/reports/{report_id}", request_options=request_options
        )
        return Report.model_validate(raw.get("report", raw))

    async def delete_report(
        self, report_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        """Permanently delete a finished report and its files."""
        await self._transport.request(
            "DELETE", f"/testing/reports/{report_id}", request_options=request_options
        )

    async def get_report_file_url(
        self,
        report_id: str,
        pack: ReportPack,
        *,
        request_options: RequestOptions | None = None,
    ) -> ReportFileDownload:
        """A pre-signed link to one of the report's files, valid for 1 hour."""
        raw = await self._transport.request(
            "GET",
            f"/testing/reports/{report_id}/files/{pack}",
            request_options=request_options,
        )
        return ReportFileDownload.model_validate(raw)

    async def create_export(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> LoadTestExport:
        raw = await self._transport.request(
            "POST",
            f"/testing/load-tests/{run_id}/exports",
            request_options=request_options,
        )
        return LoadTestExport.model_validate(raw.get("export", raw))

    async def list_exports(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> List[LoadTestExport]:
        raw = await self._transport.request(
            "GET",
            f"/testing/load-tests/{run_id}/exports",
            request_options=request_options,
        )
        return [LoadTestExport.model_validate(e) for e in raw.get("exports", [])]

    async def get_export(
        self,
        run_id: str,
        export_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> LoadTestExport:
        raw = await self._transport.request(
            "GET",
            f"/testing/load-tests/{run_id}/exports/{export_id}",
            request_options=request_options,
        )
        return LoadTestExport.model_validate(raw.get("export", raw))

    async def get_failure_patterns(
        self,
        run_id: str,
        *,
        scope: FailurePatternScope | None = None,
        request_options: RequestOptions | None = None,
    ) -> LoadTestFailurePatterns:
        raw = await self._transport.request(
            "GET",
            f"/testing/load-tests/{run_id}/failure-patterns",
            params=_scope_params(scope),
            request_options=request_options,
        )
        return LoadTestFailurePatterns.model_validate(raw)

    async def reclassify_failure_patterns(
        self,
        run_id: str,
        *,
        scope: FailurePatternScope | None = None,
        request_options: RequestOptions | None = None,
    ) -> ReclassifyFailurePatternsResponse:
        raw = await self._transport.request(
            "POST",
            f"/testing/load-tests/{run_id}/failure-patterns/reclassify",
            params=_scope_params(scope),
            request_options=request_options,
        )
        return ReclassifyFailurePatternsResponse.model_validate(raw)

    def list_failure_pattern_calls(
        self,
        run_id: str,
        pattern_id: str,
        *,
        scope: FailurePatternScope | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[FailurePatternCall]:
        params = _cursor_params(limit=limit, cursor=cursor, scope=scope)

        async def fetch(p: dict) -> dict:
            raw = await self._transport.request(
                "GET",
                f"/testing/load-tests/{run_id}/failure-patterns/{pattern_id}/calls",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return _calls_page(raw)

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=FailurePatternCall)

    async def list_failure_pattern_calls_page(
        self,
        run_id: str,
        pattern_id: str,
        *,
        scope: FailurePatternScope | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[FailurePatternCall]:
        """One page of a pattern's calls. Pass ``next_token`` back as ``cursor``."""
        raw = await self._transport.request(
            "GET",
            f"/testing/load-tests/{run_id}/failure-patterns/{pattern_id}/calls",
            params=_cursor_params(limit=limit, cursor=cursor, scope=scope),
            request_options=request_options,
        )
        items = [FailurePatternCall.model_validate(c) for c in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("cursor"))


