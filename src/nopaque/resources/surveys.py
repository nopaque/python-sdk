"""Surveys resource - the /testing/survey-* endpoints.

A survey test runs the other way round from a call test: nopaque does not start
the conversation, the customer's survey platform does. The flow is:

1. :meth:`SurveysResource.start` claims one of the workspace's numbers and arms a
   respondent on it. It returns ``agent_e164``, the number to send the survey to.
2. The customer's platform sends its survey to that number, from ``sender``.
3. :meth:`SurveysResource.wait_for_result` polls until the transcript is final.

Nested:

- ``surveys.configs`` - saved respondent definitions (``/testing/survey-test-configs``)
- ``surveys.results`` - what happened in each test (``/testing/survey-results``)
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional

from .._errors import NopaqueTimeoutError, NotFoundError
from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._polling import DEFAULT_INITIAL_INTERVAL, DEFAULT_INTERVAL_CAP, poll_interval_curve
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from .._transport import AsyncTransport, SyncTransport
from ..models.surveys import (
    SURVEY_CAPTURE_TERMINAL_STATUSES,
    CreateSurveyTestConfigRequest,
    ListSurveyTestConfigsResponse,
    StartSurveyTestRequest,
    SurveyResult,
    SurveyResultSummary,
    SurveyRunList,
    SurveyRunStarted,
    SurveyScenario,
    SurveyTestConfig,
    SurveyTestConfigListItem,
    UpdateSurveyTestConfigRequest,
)

__all__ = ["AsyncSurveysResource", "SurveysResource"]

DEFAULT_NOT_FOUND_GRACE = 60.0
"""Seconds a new run's result may 404 before that is treated as a real 404.

The result row is written from a table stream after the run starts, so it lags
the start response by a few seconds."""

CAPTURE_GRACE_AFTER_WINDOW = 600.0
"""Seconds past the run's window to keep waiting when no timeout is given.

A run that never engages is finalised and captured shortly after its window
closes; this covers that, with room to spare."""


def _drop_none(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in payload.items() if v is not None}


def _build_start_body(
    *,
    config_id: str,
    sender: str,
    window_secs: Optional[int],
    expected_turns: Optional[int],
    max_messages: Optional[int],
) -> dict:
    model = StartSurveyTestRequest.model_validate(
        _drop_none(
            {
                "config_id": config_id,
                "end_user_e164": sender,
                "window_secs": window_secs,
                "expected_turns": expected_turns,
                "max_messages": max_messages,
            }
        )
    )
    return model.model_dump(by_alias=True, exclude_none=True)


def _config_fields(
    *,
    name: Optional[str],
    description: Optional[str],
    sector: Optional[str],
    mission: Optional[str],
    acceptance: Optional[str],
    scenario: Optional[SurveyScenario],
    profile_id: Optional[str],
    expected_turns: Optional[int],
    tags: Optional[List[str]],
    voice_id: Optional[str],
) -> Dict[str, Any]:
    return _drop_none(
        {
            "name": name,
            "description": description,
            "sector": sector,
            "mission": mission,
            "acceptance": acceptance,
            "scenario": scenario,
            "profile_id": profile_id,
            "expected_turns": expected_turns,
            "tags": tags,
            "voice_id": voice_id,
        }
    )


def _build_create_config_body(**fields: Any) -> dict:
    model = CreateSurveyTestConfigRequest.model_validate(_config_fields(**fields))
    return model.model_dump(by_alias=True, exclude_none=True)


def _build_update_config_body(**fields: Any) -> dict:
    model = UpdateSurveyTestConfigRequest.model_validate(_config_fields(**fields))
    return model.model_dump(by_alias=True, exclude_none=True)


def _apply_cursor(params: dict) -> dict:
    """Translate the paginator's injected `nextToken` into the spec `cursor` param."""
    p = dict(params)
    if "nextToken" in p:
        p["cursor"] = p.pop("nextToken")
    return p


def _build_list_params(
    *, limit: Optional[int], cursor: Optional[str], next_token: Optional[str]
) -> dict:
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor is not None:
        params["cursor"] = cursor
    elif next_token is not None:
        params["cursor"] = next_token
    return params


class _ResultDeadline:
    """When ``wait_for_result`` gives up.

    With an explicit ``timeout`` that is the deadline. Without one, the deadline
    comes from the run itself - its window end plus :data:`CAPTURE_GRACE_AFTER_WINDOW`
    - so a 10-minute test and a 12-hour test both wait the right amount. Until the
    result has been seen at all, the deadline is the not-found grace.
    """

    def __init__(self, *, timeout: Optional[float], not_found_grace: float) -> None:
        self._start = time.time()
        self._timeout = timeout
        self._not_found_grace = not_found_grace
        self._derived_end: Optional[float] = None

    def saw(self, result: SurveyResult) -> None:
        if self._derived_end is None:
            self._derived_end = result.expires_at + CAPTURE_GRACE_AFTER_WINDOW

    def not_found_expired(self) -> bool:
        return time.time() - self._start >= self._not_found_grace

    def remaining(self) -> float:
        if self._timeout is not None:
            end = self._start + self._timeout
        elif self._derived_end is not None:
            end = self._derived_end
        else:
            end = self._start + self._not_found_grace
        return end - time.time()


def _timeout_error(run_id: str, last: Optional[SurveyResult]) -> NopaqueTimeoutError:
    status = last.capture.status if last is not None else "not recorded yet"
    return NopaqueTimeoutError(
        f"wait_for_result timed out for survey run {run_id} (capture: {status}). "
        "The test itself was not stopped."
    )


def _notify(on_update: Optional[Callable[[SurveyResult], None]], result: SurveyResult) -> None:
    if on_update:
        try:
            on_update(result)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


class _SyncSurveyConfigs:
    """Synchronous /testing/survey-test-configs endpoints."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        name: str,
        sector: str,
        mission: str,
        acceptance: str,
        scenario: SurveyScenario,
        description: str | None = None,
        profile_id: str | None = None,
        expected_turns: int | None = None,
        tags: List[str] | None = None,
        voice_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SurveyTestConfig:
        """Save a survey test config: who the respondent is and how it behaves.

        ``mission`` is what the respondent is trying to say (for example "had an
        engineer visit, happy with it, would score 9"). ``acceptance`` is what a
        good survey looks like. ``expected_turns`` is how many answers the
        respondent gives before it goes quiet.
        """
        body = _build_create_config_body(
            name=name,
            description=description,
            sector=sector,
            mission=mission,
            acceptance=acceptance,
            scenario=scenario,
            profile_id=profile_id,
            expected_turns=expected_turns,
            tags=tags,
            voice_id=voice_id,
        )
        raw = self._transport.request(
            "POST", "/testing/survey-test-configs", json=body, request_options=request_options
        )
        return SurveyTestConfig.model_validate(raw)

    def list(
        self, *, request_options: RequestOptions | None = None
    ) -> List[SurveyTestConfigListItem]:
        """List saved survey test configs.

        Not paginated. List items leave out ``mission`` and ``acceptance``; use
        :meth:`get` for the full config.
        """
        raw = self._transport.request(
            "GET", "/testing/survey-test-configs", request_options=request_options
        )
        return ListSurveyTestConfigsResponse.model_validate(raw).configs

    def get(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> SurveyTestConfig:
        """Get one saved survey test config."""
        raw = self._transport.request(
            "GET", f"/testing/survey-test-configs/{config_id}", request_options=request_options
        )
        return SurveyTestConfig.model_validate(raw)

    def update(
        self,
        config_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sector: str | None = None,
        mission: str | None = None,
        acceptance: str | None = None,
        scenario: SurveyScenario | None = None,
        profile_id: str | None = None,
        expected_turns: int | None = None,
        tags: List[str] | None = None,
        voice_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SurveyTestConfig:
        """Partially update a saved survey test config. Only the fields you pass are sent."""
        body = _build_update_config_body(
            name=name,
            description=description,
            sector=sector,
            mission=mission,
            acceptance=acceptance,
            scenario=scenario,
            profile_id=profile_id,
            expected_turns=expected_turns,
            tags=tags,
            voice_id=voice_id,
        )
        raw = self._transport.request(
            "PATCH",
            f"/testing/survey-test-configs/{config_id}",
            json=body,
            request_options=request_options,
        )
        return SurveyTestConfig.model_validate(raw)

    def delete(self, config_id: str, *, request_options: RequestOptions | None = None) -> None:
        """Delete a saved survey test config. Results already recorded are kept."""
        self._transport.request(
            "DELETE", f"/testing/survey-test-configs/{config_id}", request_options=request_options
        )


class _SyncSurveyResults:
    """Synchronous /testing/survey-results endpoints."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[SurveyResultSummary]:
        """Iterate survey results, newest first. Summaries only - no turns."""
        params = _build_list_params(limit=limit, cursor=cursor, next_token=next_token)

        def fetch(p: dict) -> dict:
            raw = self._transport.request(
                "GET",
                "/testing/survey-results",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return {"results": raw.get("results", []), "nextToken": raw.get("nextCursor")}

        return SyncPaginator(
            fetch_page=fetch,
            params=params,
            model_cls=SurveyResultSummary,
            items_key="results",
        )

    def list_page(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[SurveyResultSummary]:
        """Fetch one page of survey results."""
        params = _build_list_params(limit=limit, cursor=cursor, next_token=next_token)
        raw = self._transport.request(
            "GET", "/testing/survey-results", params=params, request_options=request_options
        )
        items = [SurveyResultSummary.model_validate(r) for r in raw.get("results", [])]
        return Page(items=items, next_token=raw.get("nextCursor"))

    def get(self, run_id: str, *, request_options: RequestOptions | None = None) -> SurveyResult:
        """Get one survey result and its conversation.

        Raises :class:`~nopaque.NotFoundError` for a few seconds after
        :meth:`SurveysResource.start`, until the result is first recorded.
        :meth:`SurveysResource.wait_for_result` allows for that.
        """
        raw = self._transport.request(
            "GET", f"/testing/survey-results/{run_id}", request_options=request_options
        )
        return SurveyResult.model_validate(raw)


class SurveysResource(SyncResource):
    """Synchronous survey testing endpoints. Nested: configs, results."""

    def __init__(self, transport: SyncTransport) -> None:
        super().__init__(transport)
        self.configs = _SyncSurveyConfigs(transport)
        self.results = _SyncSurveyResults(transport)

    def start(
        self,
        *,
        config_id: str,
        sender: str,
        window_secs: int | None = None,
        expected_turns: int | None = None,
        max_messages: int | None = None,
        request_options: RequestOptions | None = None,
    ) -> SurveyRunStarted:
        """Start a survey test: claim a number and arm the respondent on it.

        ``sender`` is the E.164 number the survey platform sends FROM (the API
        calls it ``endUserE164``). Send the survey to the returned ``agent_e164``
        before ``expires_at`` (epoch seconds). ``window_secs`` is how long the
        survey has to arrive (API default 300). ``expected_turns`` overrides the
        config's answer count.

        Raises :class:`~nopaque.ConflictError` when the workspace has no survey
        numbers, or all of them are already running a test against ``sender``;
        the message says which. A 503 means the number could not be put into
        service and nothing was reserved - it is safe to call again.
        """
        body = _build_start_body(
            config_id=config_id,
            sender=sender,
            window_secs=window_secs,
            expected_turns=expected_turns,
            max_messages=max_messages,
        )
        raw = self._transport.request(
            "POST", "/testing/survey-runs", json=body, request_options=request_options
        )
        return SurveyRunStarted.model_validate(raw)

    def stop(self, run_id: str, *, request_options: RequestOptions | None = None) -> None:
        """Stop a survey test and free its number. Its transcript is captured straight away."""
        self._transport.request(
            "DELETE", f"/testing/survey-runs/{run_id}", request_options=request_options
        )

    def list(self, *, request_options: RequestOptions | None = None) -> SurveyRunList:
        """List live survey tests, with how many survey numbers are free. Not paginated."""
        raw = self._transport.request(
            "GET", "/testing/survey-runs", request_options=request_options
        )
        return SurveyRunList.model_validate(raw)

    def wait_for_result(
        self,
        run_id: str,
        *,
        timeout: float | None = None,
        poll_interval: float = DEFAULT_INITIAL_INTERVAL,
        interval_cap: float = DEFAULT_INTERVAL_CAP,
        not_found_grace: float = DEFAULT_NOT_FOUND_GRACE,
        on_update: Callable[[SurveyResult], None] | None = None,
        request_options: RequestOptions | None = None,
    ) -> SurveyResult:
        """Poll a survey test's result until its transcript is settled.

        Returns once ``capture.status`` is ``final`` or ``failed``. A failed
        capture is returned, not raised: inspect ``capture.error``. Check
        ``outcome`` and ``turns`` on what you get back.

        With no ``timeout``, waits until 10 minutes past the test's window end,
        which covers a survey that never arrives. On timeout raises
        :class:`~nopaque.NopaqueTimeoutError`; the test itself is not stopped.
        """
        deadline = _ResultDeadline(timeout=timeout, not_found_grace=not_found_grace)
        last: Optional[SurveyResult] = None
        step = 0
        while True:
            try:
                last = self.results.get(run_id, request_options=request_options)
            except NotFoundError:
                if deadline.not_found_expired():
                    raise
            else:
                deadline.saw(last)
                _notify(on_update, last)
                if last.capture.status in SURVEY_CAPTURE_TERMINAL_STATUSES:
                    return last
            remaining = deadline.remaining()
            if remaining <= 0:
                raise _timeout_error(run_id, last)
            time.sleep(
                min(poll_interval_curve(step, base=poll_interval, cap=interval_cap), remaining)
            )
            step += 1


# ---------------------------------------------------------------------------
# Async
# ---------------------------------------------------------------------------


class _AsyncSurveyConfigs:
    """Asynchronous /testing/survey-test-configs endpoints."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        name: str,
        sector: str,
        mission: str,
        acceptance: str,
        scenario: SurveyScenario,
        description: str | None = None,
        profile_id: str | None = None,
        expected_turns: int | None = None,
        tags: List[str] | None = None,
        voice_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SurveyTestConfig:
        """Save a survey test config. See :meth:`_SyncSurveyConfigs.create`."""
        body = _build_create_config_body(
            name=name,
            description=description,
            sector=sector,
            mission=mission,
            acceptance=acceptance,
            scenario=scenario,
            profile_id=profile_id,
            expected_turns=expected_turns,
            tags=tags,
            voice_id=voice_id,
        )
        raw = await self._transport.request(
            "POST", "/testing/survey-test-configs", json=body, request_options=request_options
        )
        return SurveyTestConfig.model_validate(raw)

    async def list(
        self, *, request_options: RequestOptions | None = None
    ) -> List[SurveyTestConfigListItem]:
        """List saved survey test configs. Not paginated."""
        raw = await self._transport.request(
            "GET", "/testing/survey-test-configs", request_options=request_options
        )
        return ListSurveyTestConfigsResponse.model_validate(raw).configs

    async def get(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> SurveyTestConfig:
        """Get one saved survey test config."""
        raw = await self._transport.request(
            "GET", f"/testing/survey-test-configs/{config_id}", request_options=request_options
        )
        return SurveyTestConfig.model_validate(raw)

    async def update(
        self,
        config_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sector: str | None = None,
        mission: str | None = None,
        acceptance: str | None = None,
        scenario: SurveyScenario | None = None,
        profile_id: str | None = None,
        expected_turns: int | None = None,
        tags: List[str] | None = None,
        voice_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SurveyTestConfig:
        """Partially update a saved survey test config. Only the fields you pass are sent."""
        body = _build_update_config_body(
            name=name,
            description=description,
            sector=sector,
            mission=mission,
            acceptance=acceptance,
            scenario=scenario,
            profile_id=profile_id,
            expected_turns=expected_turns,
            tags=tags,
            voice_id=voice_id,
        )
        raw = await self._transport.request(
            "PATCH",
            f"/testing/survey-test-configs/{config_id}",
            json=body,
            request_options=request_options,
        )
        return SurveyTestConfig.model_validate(raw)

    async def delete(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        """Delete a saved survey test config. Results already recorded are kept."""
        await self._transport.request(
            "DELETE", f"/testing/survey-test-configs/{config_id}", request_options=request_options
        )


class _AsyncSurveyResults:
    """Asynchronous /testing/survey-results endpoints."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[SurveyResultSummary]:
        """Iterate survey results, newest first. Summaries only - no turns."""
        params = _build_list_params(limit=limit, cursor=cursor, next_token=next_token)

        async def fetch(p: dict) -> dict:
            raw = await self._transport.request(
                "GET",
                "/testing/survey-results",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return {"results": raw.get("results", []), "nextToken": raw.get("nextCursor")}

        return AsyncPaginator(
            fetch_page=fetch,
            params=params,
            model_cls=SurveyResultSummary,
            items_key="results",
        )

    async def list_page(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[SurveyResultSummary]:
        """Fetch one page of survey results."""
        params = _build_list_params(limit=limit, cursor=cursor, next_token=next_token)
        raw = await self._transport.request(
            "GET", "/testing/survey-results", params=params, request_options=request_options
        )
        items = [SurveyResultSummary.model_validate(r) for r in raw.get("results", [])]
        return Page(items=items, next_token=raw.get("nextCursor"))

    async def get(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> SurveyResult:
        """Get one survey result and its conversation. May 404 just after start."""
        raw = await self._transport.request(
            "GET", f"/testing/survey-results/{run_id}", request_options=request_options
        )
        return SurveyResult.model_validate(raw)


class AsyncSurveysResource(AsyncResource):
    """Asynchronous survey testing endpoints. Nested: configs, results."""

    def __init__(self, transport: AsyncTransport) -> None:
        super().__init__(transport)
        self.configs = _AsyncSurveyConfigs(transport)
        self.results = _AsyncSurveyResults(transport)

    async def start(
        self,
        *,
        config_id: str,
        sender: str,
        window_secs: int | None = None,
        expected_turns: int | None = None,
        max_messages: int | None = None,
        request_options: RequestOptions | None = None,
    ) -> SurveyRunStarted:
        """Start a survey test. See :meth:`SurveysResource.start`."""
        body = _build_start_body(
            config_id=config_id,
            sender=sender,
            window_secs=window_secs,
            expected_turns=expected_turns,
            max_messages=max_messages,
        )
        raw = await self._transport.request(
            "POST", "/testing/survey-runs", json=body, request_options=request_options
        )
        return SurveyRunStarted.model_validate(raw)

    async def stop(self, run_id: str, *, request_options: RequestOptions | None = None) -> None:
        """Stop a survey test and free its number."""
        await self._transport.request(
            "DELETE", f"/testing/survey-runs/{run_id}", request_options=request_options
        )

    async def list(self, *, request_options: RequestOptions | None = None) -> SurveyRunList:
        """List live survey tests, with how many survey numbers are free."""
        raw = await self._transport.request(
            "GET", "/testing/survey-runs", request_options=request_options
        )
        return SurveyRunList.model_validate(raw)

    async def wait_for_result(
        self,
        run_id: str,
        *,
        timeout: float | None = None,
        poll_interval: float = DEFAULT_INITIAL_INTERVAL,
        interval_cap: float = DEFAULT_INTERVAL_CAP,
        not_found_grace: float = DEFAULT_NOT_FOUND_GRACE,
        on_update: Callable[[SurveyResult], None] | None = None,
        request_options: RequestOptions | None = None,
    ) -> SurveyResult:
        """Poll a survey test's result until its transcript is settled.

        See :meth:`SurveysResource.wait_for_result`.
        """
        deadline = _ResultDeadline(timeout=timeout, not_found_grace=not_found_grace)
        last: Optional[SurveyResult] = None
        step = 0
        while True:
            try:
                last = await self.results.get(run_id, request_options=request_options)
            except NotFoundError:
                if deadline.not_found_expired():
                    raise
            else:
                deadline.saw(last)
                _notify(on_update, last)
                if last.capture.status in SURVEY_CAPTURE_TERMINAL_STATUSES:
                    return last
            remaining = deadline.remaining()
            if remaining <= 0:
                raise _timeout_error(run_id, last)
            await asyncio.sleep(
                min(poll_interval_curve(step, base=poll_interval, cap=interval_cap), remaining)
            )
            step += 1
