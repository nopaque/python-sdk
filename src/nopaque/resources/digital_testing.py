"""Digital testing resource - the /digital-testing/runs endpoints (chat channel),
plus saved connectors (/digital-testing/connectors) and connector types.

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
    ConnectorTypeDescriptor,
    CreateDigitalTestRunRequest,
    CreateDigitalTestRunResponse,
    DigitalConnector,
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


def _connector_list_params(
    *, type: Optional[str], limit: Optional[int], cursor: Optional[str]
) -> dict:
    params: dict = {}
    if type is not None:
        params["type"] = type
    if limit is not None:
        params["limit"] = limit
    if cursor is not None:
        params["cursor"] = cursor
    return params


def _connector_create_body(
    *,
    name: str,
    type: str,
    target_ref: str,
    config: Dict[str, Any],
    description: Optional[str],
) -> dict:
    body: dict = {"name": name, "type": type, "targetRef": target_ref, "config": config}
    if description is not None:
        body["description"] = description
    return body


def _connector_update_body(
    *,
    name: Optional[str],
    description: Optional[str],
    config: Optional[Dict[str, Any]],
) -> dict:
    body: dict = {}
    if name is not None:
        body["name"] = name
    if description is not None:
        body["description"] = description
    if config is not None:
        body["config"] = config
    return body


def _connectors_page(raw: dict) -> dict:
    return {"connectors": raw.get("connectors", []), "nextToken": raw.get("nextCursor")}


class DigitalTestingResource(SyncResource):
    """Synchronous /digital-testing/runs endpoints, plus saved connectors
    (/digital-testing/connectors) and connector types."""

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

    def list_connectors(
        self,
        *,
        type: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[DigitalConnector]:
        """The workspace's saved connectors, most recently updated first.

        Beta. Access is limited to beta workspaces during the beta period.

        Iterates every page. ``type`` filters to one connector type; an
        unknown type is a ``ValidationError``, not an empty list.
        """
        params = _connector_list_params(type=type, limit=limit, cursor=cursor)

        def fetch(p: dict) -> dict:
            raw = self._transport.request(
                "GET",
                "/digital-testing/connectors",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return _connectors_page(raw)

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=DigitalConnector, items_key="connectors"
        )

    def list_connectors_page(
        self,
        *,
        type: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[DigitalConnector]:
        """One page of connectors. Pass ``next_token`` back as ``cursor``."""
        raw = self._transport.request(
            "GET",
            "/digital-testing/connectors",
            params=_connector_list_params(type=type, limit=limit, cursor=cursor),
            request_options=request_options,
        )
        items = [DigitalConnector.model_validate(c) for c in raw.get("connectors", [])]
        return Page(items=items, next_token=raw.get("nextCursor"))

    def get_connector(
        self, connector_id: str, *, request_options: RequestOptions | None = None
    ) -> DigitalConnector:
        raw = self._transport.request(
            "GET",
            f"/digital-testing/connectors/{connector_id}",
            request_options=request_options,
        )
        return DigitalConnector.model_validate(raw)

    def create_connector(
        self,
        *,
        name: str,
        type: str,
        target_ref: str,
        config: Dict[str, Any],
        description: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> DigitalConnector:
        """Save a reusable connection definition.

        Beta. Access is limited to beta workspaces during the beta period.

        ``type`` (for example ``web-widget``, ``connect-chat``, ``http-json``)
        and ``target_ref`` cannot be changed later. ``config`` is the target
        object minus ``transport``, validated against ``type``: see
        ``list_connector_types()`` for the fields each type accepts.
        """
        raw = self._transport.request(
            "POST",
            "/digital-testing/connectors",
            json=_connector_create_body(
                name=name,
                type=type,
                target_ref=target_ref,
                config=config,
                description=description,
            ),
            request_options=request_options,
        )
        return DigitalConnector.model_validate(raw)

    def update_connector(
        self,
        connector_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        config: Dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> DigitalConnector:
        """Change a connector's ``name``, ``description`` or ``config``.

        Only what you pass is sent. The merged config is validated server-side.
        """
        raw = self._transport.request(
            "PATCH",
            f"/digital-testing/connectors/{connector_id}",
            json=_connector_update_body(name=name, description=description, config=config),
            request_options=request_options,
        )
        return DigitalConnector.model_validate(raw)

    def delete_connector(
        self, connector_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        """Delete a connector.

        Refused with ``ConflictError`` while any saved config still references
        it; the error names those configs.
        """
        self._transport.request(
            "DELETE",
            f"/digital-testing/connectors/{connector_id}",
            request_options=request_options,
        )

    def list_connector_types(
        self, *, request_options: RequestOptions | None = None
    ) -> List[ConnectorTypeDescriptor]:
        """Every connector type with the form fields its ``config`` takes.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        raw = self._transport.request(
            "GET", "/digital-testing/connector-types", request_options=request_options
        )
        return [ConnectorTypeDescriptor.model_validate(t) for t in raw.get("types", [])]


class AsyncDigitalTestingResource(AsyncResource):
    """Asynchronous /digital-testing/runs endpoints, plus saved connectors
    (/digital-testing/connectors) and connector types."""

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

    def list_connectors(
        self,
        *,
        type: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[DigitalConnector]:
        """The workspace's connectors, most recently updated first."""
        params = _connector_list_params(type=type, limit=limit, cursor=cursor)

        async def fetch(p: dict) -> dict:
            raw = await self._transport.request(
                "GET",
                "/digital-testing/connectors",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return _connectors_page(raw)

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=DigitalConnector, items_key="connectors"
        )

    async def list_connectors_page(
        self,
        *,
        type: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[DigitalConnector]:
        raw = await self._transport.request(
            "GET",
            "/digital-testing/connectors",
            params=_connector_list_params(type=type, limit=limit, cursor=cursor),
            request_options=request_options,
        )
        items = [DigitalConnector.model_validate(c) for c in raw.get("connectors", [])]
        return Page(items=items, next_token=raw.get("nextCursor"))

    async def get_connector(
        self, connector_id: str, *, request_options: RequestOptions | None = None
    ) -> DigitalConnector:
        raw = await self._transport.request(
            "GET",
            f"/digital-testing/connectors/{connector_id}",
            request_options=request_options,
        )
        return DigitalConnector.model_validate(raw)

    async def create_connector(
        self,
        *,
        name: str,
        type: str,
        target_ref: str,
        config: Dict[str, Any],
        description: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> DigitalConnector:
        """Save a reusable connection definition. ``type`` and ``target_ref``
        cannot be changed later."""
        raw = await self._transport.request(
            "POST",
            "/digital-testing/connectors",
            json=_connector_create_body(
                name=name,
                type=type,
                target_ref=target_ref,
                config=config,
                description=description,
            ),
            request_options=request_options,
        )
        return DigitalConnector.model_validate(raw)

    async def update_connector(
        self,
        connector_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        config: Dict[str, Any] | None = None,
        request_options: RequestOptions | None = None,
    ) -> DigitalConnector:
        """Change a connector's ``name``, ``description`` or ``config``."""
        raw = await self._transport.request(
            "PATCH",
            f"/digital-testing/connectors/{connector_id}",
            json=_connector_update_body(name=name, description=description, config=config),
            request_options=request_options,
        )
        return DigitalConnector.model_validate(raw)

    async def delete_connector(
        self, connector_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        """Delete a connector. ``ConflictError`` while a config references it."""
        await self._transport.request(
            "DELETE",
            f"/digital-testing/connectors/{connector_id}",
            request_options=request_options,
        )

    async def list_connector_types(
        self, *, request_options: RequestOptions | None = None
    ) -> List[ConnectorTypeDescriptor]:
        raw = await self._transport.request(
            "GET", "/digital-testing/connector-types", request_options=request_options
        )
        return [ConnectorTypeDescriptor.model_validate(t) for t in raw.get("types", [])]


