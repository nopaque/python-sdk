"""Digital testing resource - the /digital-testing/runs endpoints (chat channel).

Beta. Access is limited to beta workspaces during the beta period.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._polling import (
    DEFAULT_INITIAL_INTERVAL,
    DEFAULT_INTERVAL_CAP,
    DEFAULT_TIMEOUT,
    wait_for_async,
    wait_for_sync,
)
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.digital_testing import (
    ConnectChatTarget,
    CreateDigitalTestRunRequest,
    CreateDigitalTestRunResponse,
    DigitalProfile,
    DigitalTestKind,
    DigitalTestRun,
    EndChatStep,
    ExpectChatStep,
    HttpJsonTarget,
    SendChatStep,
    WaitChatStep,
    WebWidgetTarget,
)

__all__ = ["AsyncDigitalTestingResource", "DigitalTestingResource"]

# A run is terminal on all three of these. `completed` with `outcome="fail"` is a
# badly-behaved bot - a RESULT, not an error - so wait_for_run returns it rather
# than raising. `failed` separately means the test could not be DELIVERED.
RUN_TERMINAL_STATUSES: set[str] = {"completed", "failed", "cancelled"}

# Callers may hand us a model or the plain dict the wire shape describes; the
# request model validates either into the discriminated union.
DigitalTargetInput = Union[
    ConnectChatTarget, HttpJsonTarget, WebWidgetTarget, Dict[str, Any]
]
ChatStepInput = Union[
    SendChatStep, ExpectChatStep, WaitChatStep, EndChatStep, Dict[str, Any]
]
DigitalProfileInput = Union[DigitalProfile, Dict[str, Any]]


def _apply_cursor(params: dict) -> dict:
    """Translate the paginator's injected `nextToken` into the spec `cursor` param."""
    p = dict(params)
    if "nextToken" in p:
        p["cursor"] = p.pop("nextToken")
    return p


def _build_run_list_params(
    *,
    target_ref: Optional[str],
    limit: Optional[int],
    cursor: Optional[str],
    next_token: Optional[str],
) -> dict:
    params: dict = {}
    if target_ref is not None:
        params["targetRef"] = target_ref
    if limit is not None:
        params["limit"] = limit
    if cursor is not None:
        params["cursor"] = cursor
    elif next_token is not None:
        params["cursor"] = next_token
    return params


def _build_create_body(
    *,
    target_ref: str,
    target: DigitalTargetInput,
    sector: str,
    mission: str,
    kind: Optional[DigitalTestKind],
    acceptance: Optional[str],
    catalogue_test_id: Optional[str],
    pass_conditions: Optional[List[str]],
    fail_conditions: Optional[List[str]],
    setup: Optional[str],
    additional_context: Optional[str],
    profile_id: Optional[str],
    profile: Optional[DigitalProfileInput],
    profile_snapshot: Optional[Dict[str, Any]],
    probes: Optional[List[str]],
    steps: Optional[List[ChatStepInput]],
    samples: Optional[int],
    max_turns: Optional[int],
) -> dict:
    # Validated through `model_validate` rather than the constructor so callers
    # may pass plain dicts for `target`, `profile` and `steps` as well as the
    # models; the model's `populate_by_name` accepts these snake_case keys.
    payload: Dict[str, Any] = {
        "target_ref": target_ref,
        "target": target,
        "sector": sector,
        "mission": mission,
        "kind": kind,
        "acceptance": acceptance,
        "catalogue_test_id": catalogue_test_id,
        "pass_conditions": pass_conditions,
        "fail_conditions": fail_conditions,
        "setup": setup,
        "additional_context": additional_context,
        "profile_id": profile_id,
        "profile": profile,
        "profile_snapshot": profile_snapshot,
        "probes": probes,
        "steps": steps,
        "samples": samples,
        "max_turns": max_turns,
    }
    model = CreateDigitalTestRunRequest.model_validate(
        {k: v for k, v in payload.items() if v is not None}
    )
    return model.model_dump(by_alias=True, exclude_none=True)


class DigitalTestingResource(SyncResource):
    """Synchronous /digital-testing/runs endpoints."""

    def create(
        self,
        *,
        target_ref: str,
        target: DigitalTargetInput,
        sector: str,
        mission: str,
        kind: DigitalTestKind | None = None,
        acceptance: str | None = None,
        catalogue_test_id: str | None = None,
        pass_conditions: List[str] | None = None,
        fail_conditions: List[str] | None = None,
        setup: str | None = None,
        additional_context: str | None = None,
        profile_id: str | None = None,
        profile: DigitalProfileInput | None = None,
        profile_snapshot: Dict[str, Any] | None = None,
        probes: List[str] | None = None,
        steps: List[ChatStepInput] | None = None,
        samples: int | None = None,
        max_turns: int | None = None,
        request_options: RequestOptions | None = None,
    ) -> DigitalTestRun:
        """Queue a digital (chat) test run.

        Beta. Access is limited to beta workspaces during the beta period.

        ``sector`` and ``mission`` are required by the API - omitting either is
        a 400, so they are required here too. Returns the queued run; poll it
        with :meth:`get` or :meth:`wait_for_run`.
        """
        body = _build_create_body(
            target_ref=target_ref,
            target=target,
            sector=sector,
            mission=mission,
            kind=kind,
            acceptance=acceptance,
            catalogue_test_id=catalogue_test_id,
            pass_conditions=pass_conditions,
            fail_conditions=fail_conditions,
            setup=setup,
            additional_context=additional_context,
            profile_id=profile_id,
            profile=profile,
            profile_snapshot=profile_snapshot,
            probes=probes,
            steps=steps,
            samples=samples,
            max_turns=max_turns,
        )
        raw = self._transport.request(
            "POST",
            "/digital-testing/runs",
            json=body,
            request_options=request_options,
        )
        return CreateDigitalTestRunResponse.model_validate(raw).run

    def list(
        self,
        *,
        target_ref: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[DigitalTestRun]:
        """List digital test runs, newest first.

        Beta. Access is limited to beta workspaces during the beta period.

        Pass ``target_ref`` to scope to a single target - that is served by a
        dedicated index rather than a filter.
        """
        params = _build_run_list_params(
            target_ref=target_ref, limit=limit, cursor=cursor, next_token=next_token
        )

        def fetch(p: dict) -> dict:
            raw = self._transport.request(
                "GET",
                "/digital-testing/runs",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return {
                "runs": raw.get("runs", []),
                "nextToken": raw.get("nextCursor", raw.get("nextToken")),
            }

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=DigitalTestRun, items_key="runs"
        )

    def list_page(
        self,
        *,
        target_ref: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[DigitalTestRun]:
        """Fetch one page of digital test runs.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        params = _build_run_list_params(
            target_ref=target_ref, limit=limit, cursor=cursor, next_token=next_token
        )
        raw = self._transport.request(
            "GET",
            "/digital-testing/runs",
            params=params,
            request_options=request_options,
        )
        items = [DigitalTestRun.model_validate(r) for r in raw.get("runs", [])]
        return Page(items=items, next_token=raw.get("nextCursor", raw.get("nextToken")))

    def get(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> DigitalTestRun:
        """Get one digital test run.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        raw = self._transport.request(
            "GET", f"/digital-testing/runs/{run_id}", request_options=request_options
        )
        return DigitalTestRun.model_validate(raw)

    def cancel(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> DigitalTestRun:
        """Cancel an in-flight digital test run.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        raw = self._transport.request(
            "POST",
            f"/digital-testing/runs/{run_id}/cancel",
            request_options=request_options,
        )
        return DigitalTestRun.model_validate(raw)

    def wait_for_run(
        self,
        run_id: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        poll_interval: float = DEFAULT_INITIAL_INTERVAL,
        interval_cap: float = DEFAULT_INTERVAL_CAP,
        on_update: Callable[[DigitalTestRun], None] | None = None,
        request_options: RequestOptions | None = None,
    ) -> DigitalTestRun:
        """Poll a digital test run until it reaches a terminal state.

        Beta. Access is limited to beta workspaces during the beta period.

        Resolves on ``completed``, ``failed`` and ``cancelled``, and returns the
        run in every case. A ``completed`` run with ``outcome="fail"`` is a
        badly-behaved bot, which is a result to inspect and not an error;
        ``failed`` means the test could not be delivered. Inspect ``status``,
        ``outcome`` and ``failure_reason`` on what you get back.
        """

        def fetch() -> DigitalTestRun:
            return self.get(run_id, request_options=request_options)

        return wait_for_sync(
            fetch=fetch,
            is_terminal=lambda r: r.status in RUN_TERMINAL_STATUSES,
            timeout=timeout,
            initial_interval=poll_interval,
            interval_cap=interval_cap,
            on_update=on_update,
        )


class AsyncDigitalTestingResource(AsyncResource):
    """Asynchronous /digital-testing/runs endpoints."""

    async def create(
        self,
        *,
        target_ref: str,
        target: DigitalTargetInput,
        sector: str,
        mission: str,
        kind: DigitalTestKind | None = None,
        acceptance: str | None = None,
        catalogue_test_id: str | None = None,
        pass_conditions: List[str] | None = None,
        fail_conditions: List[str] | None = None,
        setup: str | None = None,
        additional_context: str | None = None,
        profile_id: str | None = None,
        profile: DigitalProfileInput | None = None,
        profile_snapshot: Dict[str, Any] | None = None,
        probes: List[str] | None = None,
        steps: List[ChatStepInput] | None = None,
        samples: int | None = None,
        max_turns: int | None = None,
        request_options: RequestOptions | None = None,
    ) -> DigitalTestRun:
        """Queue a digital (chat) test run.

        Beta. Access is limited to beta workspaces during the beta period.

        ``sector`` and ``mission`` are required by the API - omitting either is
        a 400, so they are required here too. Returns the queued run; poll it
        with :meth:`get` or :meth:`wait_for_run`.
        """
        body = _build_create_body(
            target_ref=target_ref,
            target=target,
            sector=sector,
            mission=mission,
            kind=kind,
            acceptance=acceptance,
            catalogue_test_id=catalogue_test_id,
            pass_conditions=pass_conditions,
            fail_conditions=fail_conditions,
            setup=setup,
            additional_context=additional_context,
            profile_id=profile_id,
            profile=profile,
            profile_snapshot=profile_snapshot,
            probes=probes,
            steps=steps,
            samples=samples,
            max_turns=max_turns,
        )
        raw = await self._transport.request(
            "POST",
            "/digital-testing/runs",
            json=body,
            request_options=request_options,
        )
        return CreateDigitalTestRunResponse.model_validate(raw).run

    def list(
        self,
        *,
        target_ref: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[DigitalTestRun]:
        """List digital test runs, newest first.

        Beta. Access is limited to beta workspaces during the beta period.

        Pass ``target_ref`` to scope to a single target - that is served by a
        dedicated index rather than a filter.
        """
        params = _build_run_list_params(
            target_ref=target_ref, limit=limit, cursor=cursor, next_token=next_token
        )

        async def fetch(p: dict) -> dict:
            raw = await self._transport.request(
                "GET",
                "/digital-testing/runs",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return {
                "runs": raw.get("runs", []),
                "nextToken": raw.get("nextCursor", raw.get("nextToken")),
            }

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=DigitalTestRun, items_key="runs"
        )

    async def list_page(
        self,
        *,
        target_ref: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[DigitalTestRun]:
        """Fetch one page of digital test runs.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        params = _build_run_list_params(
            target_ref=target_ref, limit=limit, cursor=cursor, next_token=next_token
        )
        raw = await self._transport.request(
            "GET",
            "/digital-testing/runs",
            params=params,
            request_options=request_options,
        )
        items = [DigitalTestRun.model_validate(r) for r in raw.get("runs", [])]
        return Page(items=items, next_token=raw.get("nextCursor", raw.get("nextToken")))

    async def get(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> DigitalTestRun:
        """Get one digital test run.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        raw = await self._transport.request(
            "GET", f"/digital-testing/runs/{run_id}", request_options=request_options
        )
        return DigitalTestRun.model_validate(raw)

    async def cancel(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> DigitalTestRun:
        """Cancel an in-flight digital test run.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        raw = await self._transport.request(
            "POST",
            f"/digital-testing/runs/{run_id}/cancel",
            request_options=request_options,
        )
        return DigitalTestRun.model_validate(raw)

    async def wait_for_run(
        self,
        run_id: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        poll_interval: float = DEFAULT_INITIAL_INTERVAL,
        interval_cap: float = DEFAULT_INTERVAL_CAP,
        on_update: Callable[[DigitalTestRun], None] | None = None,
        request_options: RequestOptions | None = None,
    ) -> DigitalTestRun:
        """Poll a digital test run until it reaches a terminal state.

        Beta. Access is limited to beta workspaces during the beta period.

        Resolves on ``completed``, ``failed`` and ``cancelled``, and returns the
        run in every case. A ``completed`` run with ``outcome="fail"`` is a
        badly-behaved bot, which is a result to inspect and not an error;
        ``failed`` means the test could not be delivered. Inspect ``status``,
        ``outcome`` and ``failure_reason`` on what you get back.
        """

        async def fetch() -> DigitalTestRun:
            return await self.get(run_id, request_options=request_options)

        return await wait_for_async(
            fetch=fetch,
            is_terminal=lambda r: r.status in RUN_TERMINAL_STATUSES,
            timeout=timeout,
            initial_interval=poll_interval,
            interval_cap=interval_cap,
            on_update=on_update,
        )
