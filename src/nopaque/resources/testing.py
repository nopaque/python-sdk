"""Testing resource - /testing/configs, /testing/jobs, /testing/runs,
/testing/carrier-integrations."""
from __future__ import annotations

import builtins
from typing import Any, Callable, Literal, Mapping, Sequence, Union

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._polling import wait_for_async, wait_for_sync
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from .._transport import AsyncTransport, SyncTransport
from ..models.testing import (
    CarrierCustomHeader,
    CarrierIntegration,
    CarrierRoute,
    ListVoicesResponse,
    MissionTestRunResponse,
    TestConfig,
    TestJob,
    TestRun,
    TestRunAggregateResponse,
    TestRunDetails,
    TestRunListItem,
)

RUN_TERMINAL_STATUSES: set[str] = {"completed", "failed", "cancelled"}


def _is_run_settled(run: TestRun) -> bool:
    """Has the run finished AND had its verdict written?

    A run can be marked terminal before its outcome lands. The container emits
    ``run_status_changed{status:'completed'}`` and ``run_completed{outcome}``
    as separate SQS messages, SQS gives no ordering guarantee, and the API
    skips undefined fields on write — so a status-only message sets ``status``
    terminal and leaves ``outcome`` unwritten. Polling on status alone returns
    that intermediate row: ``outcome`` None and no step results, on a run that
    passed.

    ``failed`` and ``cancelled`` settle immediately; neither is expected to
    carry a verdict.
    """
    if run.status not in RUN_TERMINAL_STATUSES:
        return False
    if run.status != "completed":
        return True
    return run.outcome is not None and run.outcome != "pending"


def _build_run_list_params(
    *,
    job_id: str | None,
    run_type: str | None,
    outcome: str | None,
    phone_number: str | None,
    config_id: str | None,
    catalogue_test_id: str | None,
    started_after: str | None,
    started_before: str | None,
    sort_by: str | None,
    sort_dir: str | None,
    limit: int | None,
    cursor: str | None,
    next_token: str | None,
) -> dict:
    params: dict = {}
    if job_id is not None:
        params["jobId"] = job_id
    if run_type is not None:
        params["runType"] = run_type
    if outcome is not None:
        params["outcome"] = outcome
    if phone_number is not None:
        params["phoneNumber"] = phone_number
    if config_id is not None:
        params["configId"] = config_id
    if catalogue_test_id is not None:
        params["catalogueTestId"] = catalogue_test_id
    if started_after is not None:
        params["startedAfter"] = started_after
    if started_before is not None:
        params["startedBefore"] = started_before
    if sort_by is not None:
        params["sortBy"] = sort_by
    if sort_dir is not None:
        params["sortDir"] = sort_dir
    if limit is not None:
        params["limit"] = limit
    if cursor is not None:
        params["cursor"] = cursor
    elif next_token is not None:
        params["cursor"] = next_token
    return params


def _apply_cursor(params: dict) -> dict:
    """Translate the paginator's injected `nextToken` into the spec `cursor` param."""
    p = dict(params)
    if "nextToken" in p:
        p["cursor"] = p.pop("nextToken")
    return p


# Sentinel for update fields where an explicit ``None`` means "remove it"
# server-side, distinct from "leave unchanged" (argument omitted).
_UNSET: Any = object()


ConfigType = Literal["standard", "parameterized"]


def _build_config_create_body(
    *,
    name: str,
    phone_number: str,
    steps: builtins.list[Any],
    description: str | None,
    type: ConfigType | None,
    profile_id: str | None,
    required_parameters: Sequence[str] | None,
    schedule_id: str | None,
    max_duration_secs: int | None,
    carrier_route_id: str | None,
) -> dict:
    body: dict = {"name": name, "phoneNumber": phone_number, "steps": steps}
    if description is not None:
        body["description"] = description
    if type is not None:
        body["type"] = type
    if profile_id is not None:
        body["profileId"] = profile_id
    if required_parameters is not None:
        body["requiredParameters"] = builtins.list(required_parameters)
    if schedule_id is not None:
        body["scheduleId"] = schedule_id
    if max_duration_secs is not None:
        body["maxDurationSecs"] = max_duration_secs
    if carrier_route_id is not None:
        body["carrierRouteId"] = carrier_route_id
    return body


def _build_config_update_body(
    *,
    name: str | None,
    description: str | None,
    phone_number: str | None,
    type: ConfigType | None,
    profile_id: str | None,
    required_parameters: Sequence[str] | None,
    steps: builtins.list[Any] | None,
    schedule_id: Any,
    max_duration_secs: Any,
    carrier_route_id: Any,
) -> dict:
    body: dict = {}
    if name is not None:
        body["name"] = name
    if description is not None:
        body["description"] = description
    if phone_number is not None:
        body["phoneNumber"] = phone_number
    if type is not None:
        body["type"] = type
    if profile_id is not None:
        body["profileId"] = profile_id
    if required_parameters is not None:
        body["requiredParameters"] = builtins.list(required_parameters)
    if steps is not None:
        body["steps"] = steps
    # Nullable on the wire: None clears, omitted (_UNSET) leaves unchanged.
    if schedule_id is not _UNSET:
        body["scheduleId"] = schedule_id
    if max_duration_secs is not _UNSET:
        body["maxDurationSecs"] = max_duration_secs
    if carrier_route_id is not _UNSET:
        body["carrierRouteId"] = carrier_route_id
    return body

CustomHeaders = Sequence[Union[CarrierCustomHeader, Mapping[str, str]]]


def _custom_headers_body(headers: CustomHeaders) -> builtins.list[dict]:
    """Accept ``CarrierCustomHeader`` models or plain ``{name, value}`` dicts."""
    out: builtins.list[dict] = []
    for h in headers:
        if isinstance(h, CarrierCustomHeader):
            out.append({"name": h.name, "value": h.value})
        else:
            out.append({"name": h["name"], "value": h["value"]})
    return out


def _build_route_create_body(
    *,
    name: str,
    tech_prefix: str | None,
    custom_headers: CustomHeaders | None,
    enabled: bool | None,
) -> dict:
    body: dict = {"name": name}
    if tech_prefix is not None:
        body["techPrefix"] = tech_prefix
    if custom_headers is not None:
        body["customHeaders"] = _custom_headers_body(custom_headers)
    if enabled is not None:
        body["enabled"] = enabled
    return body


def _build_route_update_body(
    *,
    name: str | None,
    tech_prefix: str | None,
    custom_headers: CustomHeaders | None,
    enabled: bool | None,
) -> dict:
    body: dict = {}
    if name is not None:
        body["name"] = name
    if tech_prefix is not None:
        body["techPrefix"] = tech_prefix
    if custom_headers is not None:
        body["customHeaders"] = _custom_headers_body(custom_headers)
    if enabled is not None:
        body["enabled"] = enabled
    if not body:
        raise ValueError(
            "Pass at least one of name, tech_prefix, custom_headers or enabled"
        )
    return body


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
        description: str | None = None,
        type: ConfigType | None = None,
        profile_id: str | None = None,
        required_parameters: Sequence[str] | None = None,
        schedule_id: str | None = None,
        max_duration_secs: int | None = None,
        carrier_route_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> TestConfig:
        """Create a test config.

        Only the arguments you pass are sent. ``type`` is ``"standard"`` (the
        server default) or ``"parameterized"``; a parameterized config lists the
        labels it needs filled at run time in ``required_parameters``, while
        ``profile_id`` applies to standard configs. ``schedule_id`` attaches a
        schedule (``"template:<template-id>"`` creates one from a recurring
        template). ``max_duration_secs`` (30-1800) is the whole-call ceiling;
        the tester defaults to 300, and every ``hold`` step must fit inside it.

        ``carrier_route_id`` is bring-your-own-carrier (invite-only): dial this
        config's calls through one of the workspace's carrier routes, over the
        workspace's own SIP trunk, instead of nopaque's network. The route is
        checked on save (400 if it cannot be dialled), and a run whose route
        cannot be dialled is refused rather than placed normally.
        """
        body = _build_config_create_body(
            name=name,
            phone_number=phone_number,
            steps=steps,
            description=description,
            type=type,
            profile_id=profile_id,
            required_parameters=required_parameters,
            schedule_id=schedule_id,
            max_duration_secs=max_duration_secs,
            carrier_route_id=carrier_route_id,
        )
        raw = self._transport.request(
            "POST",
            "/testing/configs",
            json=body,
            request_options=request_options,
        )
        return TestConfig.model_validate(raw)

    def update(
        self,
        config_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        phone_number: str | None = None,
        type: ConfigType | None = None,
        profile_id: str | None = None,
        required_parameters: Sequence[str] | None = None,
        steps: builtins.list[Any] | None = None,
        schedule_id: Any = _UNSET,
        max_duration_secs: Any = _UNSET,
        carrier_route_id: Any = _UNSET,
        request_options: RequestOptions | None = None,
    ) -> TestConfig:
        """Update a test config. Only supplied fields change.

        ``name``, ``description``, ``phone_number``, ``type``, ``profile_id``,
        ``required_parameters`` and ``steps`` are sent only when not ``None``.

        ``schedule_id``, ``max_duration_secs`` and ``carrier_route_id`` can be
        cleared: pass ``None`` to clear, omit to leave unchanged.
        ``schedule_id=None`` unlinks the schedule. ``max_duration_secs=None``
        resets the ceiling to the tester default of 300; hold steps are
        re-checked against the new ceiling, so lowering or clearing it below a
        saved hold returns 400. ``carrier_route_id`` (bring-your-own-carrier,
        invite-only) sets the carrier route to dial through; ``None`` removes
        it, so the number is dialled normally again.
        """
        body = _build_config_update_body(
            name=name,
            description=description,
            phone_number=phone_number,
            type=type,
            profile_id=profile_id,
            required_parameters=required_parameters,
            steps=steps,
            schedule_id=schedule_id,
            max_duration_secs=max_duration_secs,
            carrier_route_id=carrier_route_id,
        )
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
        job_id: str | None = None,
        run_type: str | None = None,
        outcome: str | None = None,
        phone_number: str | None = None,
        config_id: str | None = None,
        catalogue_test_id: str | None = None,
        started_after: str | None = None,
        started_before: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[TestRunListItem]:
        params = _build_run_list_params(
            job_id=job_id,
            run_type=run_type,
            outcome=outcome,
            phone_number=phone_number,
            config_id=config_id,
            catalogue_test_id=catalogue_test_id,
            started_after=started_after,
            started_before=started_before,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            cursor=cursor,
            next_token=next_token,
        )

        def fetch(p: dict) -> dict:
            # Server returns { runs: [...], nextCursor? } — normalize.
            raw = self._transport.request(
                "GET", "/testing/runs", params=_apply_cursor(p), request_options=request_options
            )
            return {
                "items": raw.get("runs", raw.get("items", [])),
                "nextToken": raw.get("nextCursor", raw.get("nextToken")),
            }

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=TestRunListItem)

    def list_page(
        self,
        *,
        job_id: str | None = None,
        run_type: str | None = None,
        outcome: str | None = None,
        phone_number: str | None = None,
        config_id: str | None = None,
        catalogue_test_id: str | None = None,
        started_after: str | None = None,
        started_before: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[TestRunListItem]:
        params = _build_run_list_params(
            job_id=job_id,
            run_type=run_type,
            outcome=outcome,
            phone_number=phone_number,
            config_id=config_id,
            catalogue_test_id=catalogue_test_id,
            started_after=started_after,
            started_before=started_before,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            cursor=cursor,
            next_token=next_token,
        )
        raw = self._transport.request(
            "GET", "/testing/runs", params=params, request_options=request_options
        )
        items = [
            TestRunListItem.model_validate(i) for i in raw.get("runs", raw.get("items", []))
        ]
        return Page(items=items, next_token=raw.get("nextCursor", raw.get("nextToken")))

    def get(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> TestRunDetails:
        raw = self._transport.request(
            "GET", f"/testing/runs/{run_id}", request_options=request_options
        )
        return TestRunDetails.model_validate(raw)

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
    ) -> TestRunDetails:
        def fetch() -> TestRunDetails:
            return self.get(run_id, request_options=request_options)

        return wait_for_sync(
            fetch=fetch,
            is_terminal=_is_run_settled,
            timeout=timeout,
            initial_interval=poll_interval,
            on_update=on_update,
        )


class _SyncCarrierRoutes:
    """Routes on a carrier integration — /testing/carrier-integrations/{id}/routes."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(
        self, integration_id: str, *, request_options: RequestOptions | None = None
    ) -> builtins.list[CarrierRoute]:
        """All routes on an integration, sorted by name. Not paginated."""
        raw = self._transport.request(
            "GET",
            f"/testing/carrier-integrations/{integration_id}/routes",
            request_options=request_options,
        )
        return [CarrierRoute.model_validate(r) for r in raw.get("routes", [])]

    def get(
        self,
        integration_id: str,
        route_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> CarrierRoute:
        raw = self._transport.request(
            "GET",
            f"/testing/carrier-integrations/{integration_id}/routes/{route_id}",
            request_options=request_options,
        )
        return CarrierRoute.model_validate(raw.get("route", raw))

    def create(
        self,
        integration_id: str,
        *,
        name: str,
        tech_prefix: str | None = None,
        custom_headers: CustomHeaders | None = None,
        enabled: bool | None = None,
        request_options: RequestOptions | None = None,
    ) -> CarrierRoute:
        """Add a route to an integration.

        ``tech_prefix`` (up to 16 of ``0-9A-Za-z#*``) is dialled in front of the
        destination number; empty or omitted means the trunk's default route.
        ``custom_headers`` are ``X-`` headers sent on the INVITE, as
        ``CarrierCustomHeader`` models or ``{"name": ..., "value": ...}`` dicts
        (at most 10). Use the returned ``route_id`` as a test config's
        ``carrier_route_id``.
        """
        raw = self._transport.request(
            "POST",
            f"/testing/carrier-integrations/{integration_id}/routes",
            json=_build_route_create_body(
                name=name,
                tech_prefix=tech_prefix,
                custom_headers=custom_headers,
                enabled=enabled,
            ),
            request_options=request_options,
        )
        return CarrierRoute.model_validate(raw.get("route", raw))

    def update(
        self,
        integration_id: str,
        route_id: str,
        *,
        name: str | None = None,
        tech_prefix: str | None = None,
        custom_headers: CustomHeaders | None = None,
        enabled: bool | None = None,
        request_options: RequestOptions | None = None,
    ) -> CarrierRoute:
        """Change a route. Send only what changes; at least one field.

        ``tech_prefix=""`` switches to the trunk's default route and
        ``custom_headers=[]`` removes all headers. ``enabled=False`` turns the
        route off: runs that name it are refused, never dialled another way.
        """
        body = _build_route_update_body(
            name=name,
            tech_prefix=tech_prefix,
            custom_headers=custom_headers,
            enabled=enabled,
        )
        raw = self._transport.request(
            "PATCH",
            f"/testing/carrier-integrations/{integration_id}/routes/{route_id}",
            json=body,
            request_options=request_options,
        )
        return CarrierRoute.model_validate(raw.get("route", raw))


class _SyncCarrierIntegrations:
    """Bring-your-own-carrier (invite-only): the workspace's own SIP trunks —
    /testing/carrier-integrations. Trunks are set up by nopaque and read-only
    here; their routes are managed under ``.routes``.
    """

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport
        self.routes = _SyncCarrierRoutes(transport)

    def list(
        self, *, request_options: RequestOptions | None = None
    ) -> builtins.list[CarrierIntegration]:
        """All of the workspace's carrier integrations, each with its routes,
        sorted by name. Not paginated; empty when the workspace has none.
        """
        raw = self._transport.request(
            "GET", "/testing/carrier-integrations", request_options=request_options
        )
        return [CarrierIntegration.model_validate(i) for i in raw.get("integrations", [])]

    def get(
        self, integration_id: str, *, request_options: RequestOptions | None = None
    ) -> CarrierIntegration:
        raw = self._transport.request(
            "GET",
            f"/testing/carrier-integrations/{integration_id}",
            request_options=request_options,
        )
        return CarrierIntegration.model_validate(raw.get("integration", raw))


class TestingResource(SyncResource):
    """Synchronous /testing/* endpoints. Nested: configs, jobs, runs,
    carrier_integrations."""

    def __init__(self, transport: SyncTransport) -> None:
        super().__init__(transport)
        self.configs = _SyncConfigs(transport)
        self.jobs = _SyncJobs(transport)
        self.runs = _SyncRuns(transport)
        self.carrier_integrations = _SyncCarrierIntegrations(transport)

    def aggregate_runs(
        self,
        *,
        group_by: str,
        run_type: str | None = None,
        outcome: str | None = None,
        phone_number: str | None = None,
        config_id: str | None = None,
        catalogue_test_id: str | None = None,
        started_after: str | None = None,
        started_before: str | None = None,
        time_bucket: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> TestRunAggregateResponse:
        """Aggregate test runs — GET /testing/runs/aggregate.

        ``group_by`` is required (one of ``outcome``, ``runType``, ``configId``,
        ``catalogueTestId``, ``phoneNumber``). Pass ``time_bucket`` (``day`` |
        ``week`` | ``month``) to get time-bucketed groups instead of flat groups.
        """
        params: dict = {"groupBy": group_by}
        if run_type is not None:
            params["runType"] = run_type
        if outcome is not None:
            params["outcome"] = outcome
        if phone_number is not None:
            params["phoneNumber"] = phone_number
        if config_id is not None:
            params["configId"] = config_id
        if catalogue_test_id is not None:
            params["catalogueTestId"] = catalogue_test_id
        if started_after is not None:
            params["startedAfter"] = started_after
        if started_before is not None:
            params["startedBefore"] = started_before
        if time_bucket is not None:
            params["timeBucket"] = time_bucket
        raw = self._transport.request(
            "GET", "/testing/runs/aggregate", params=params, request_options=request_options
        )
        return TestRunAggregateResponse.model_validate(raw)

    def get_mission_test_run(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> MissionTestRunResponse:
        """Get a mission test run — GET /testing/mission-test-runs/{id}.

        Mission-strict shape (no ``stepResults`` — mission tests have no steps).
        """
        raw = self._transport.request(
            "GET",
            f"/testing/mission-test-runs/{run_id}",
            request_options=request_options,
        )
        return MissionTestRunResponse.model_validate(raw)

    def list_voices(
        self,
        *,
        request_options: RequestOptions | None = None,
    ) -> ListVoicesResponse:
        """Operator-enabled voices a mission test may use, and which is default."""
        raw = self._transport.request(
            "GET", "/testing/voices", request_options=request_options
        )
        return ListVoicesResponse.model_validate(raw)


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
        description: str | None = None,
        type: ConfigType | None = None,
        profile_id: str | None = None,
        required_parameters: Sequence[str] | None = None,
        schedule_id: str | None = None,
        max_duration_secs: int | None = None,
        carrier_route_id: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> TestConfig:
        """Create a test config.

        Only the arguments you pass are sent. ``type`` is ``"standard"`` (the
        server default) or ``"parameterized"``; a parameterized config lists the
        labels it needs filled at run time in ``required_parameters``, while
        ``profile_id`` applies to standard configs. ``schedule_id`` attaches a
        schedule (``"template:<template-id>"`` creates one from a recurring
        template). ``max_duration_secs`` (30-1800) is the whole-call ceiling;
        the tester defaults to 300, and every ``hold`` step must fit inside it.

        ``carrier_route_id`` is bring-your-own-carrier (invite-only): dial this
        config's calls through one of the workspace's carrier routes, over the
        workspace's own SIP trunk, instead of nopaque's network. The route is
        checked on save (400 if it cannot be dialled), and a run whose route
        cannot be dialled is refused rather than placed normally.
        """
        body = _build_config_create_body(
            name=name,
            phone_number=phone_number,
            steps=steps,
            description=description,
            type=type,
            profile_id=profile_id,
            required_parameters=required_parameters,
            schedule_id=schedule_id,
            max_duration_secs=max_duration_secs,
            carrier_route_id=carrier_route_id,
        )
        raw = await self._transport.request(
            "POST",
            "/testing/configs",
            json=body,
            request_options=request_options,
        )
        return TestConfig.model_validate(raw)

    async def update(
        self,
        config_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        phone_number: str | None = None,
        type: ConfigType | None = None,
        profile_id: str | None = None,
        required_parameters: Sequence[str] | None = None,
        steps: builtins.list[Any] | None = None,
        schedule_id: Any = _UNSET,
        max_duration_secs: Any = _UNSET,
        carrier_route_id: Any = _UNSET,
        request_options: RequestOptions | None = None,
    ) -> TestConfig:
        """Update a test config. Only supplied fields change.

        ``name``, ``description``, ``phone_number``, ``type``, ``profile_id``,
        ``required_parameters`` and ``steps`` are sent only when not ``None``.

        ``schedule_id``, ``max_duration_secs`` and ``carrier_route_id`` can be
        cleared: pass ``None`` to clear, omit to leave unchanged.
        ``schedule_id=None`` unlinks the schedule. ``max_duration_secs=None``
        resets the ceiling to the tester default of 300; hold steps are
        re-checked against the new ceiling, so lowering or clearing it below a
        saved hold returns 400. ``carrier_route_id`` (bring-your-own-carrier,
        invite-only) sets the carrier route to dial through; ``None`` removes
        it, so the number is dialled normally again.
        """
        body = _build_config_update_body(
            name=name,
            description=description,
            phone_number=phone_number,
            type=type,
            profile_id=profile_id,
            required_parameters=required_parameters,
            steps=steps,
            schedule_id=schedule_id,
            max_duration_secs=max_duration_secs,
            carrier_route_id=carrier_route_id,
        )
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
        job_id: str | None = None,
        run_type: str | None = None,
        outcome: str | None = None,
        phone_number: str | None = None,
        config_id: str | None = None,
        catalogue_test_id: str | None = None,
        started_after: str | None = None,
        started_before: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[TestRunListItem]:
        params = _build_run_list_params(
            job_id=job_id,
            run_type=run_type,
            outcome=outcome,
            phone_number=phone_number,
            config_id=config_id,
            catalogue_test_id=catalogue_test_id,
            started_after=started_after,
            started_before=started_before,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            cursor=cursor,
            next_token=next_token,
        )

        async def fetch(p: dict) -> dict:
            raw = await self._transport.request(
                "GET", "/testing/runs", params=_apply_cursor(p), request_options=request_options
            )
            return {
                "items": raw.get("runs", raw.get("items", [])),
                "nextToken": raw.get("nextCursor", raw.get("nextToken")),
            }

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=TestRunListItem)

    async def list_page(
        self,
        *,
        job_id: str | None = None,
        run_type: str | None = None,
        outcome: str | None = None,
        phone_number: str | None = None,
        config_id: str | None = None,
        catalogue_test_id: str | None = None,
        started_after: str | None = None,
        started_before: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[TestRunListItem]:
        params = _build_run_list_params(
            job_id=job_id,
            run_type=run_type,
            outcome=outcome,
            phone_number=phone_number,
            config_id=config_id,
            catalogue_test_id=catalogue_test_id,
            started_after=started_after,
            started_before=started_before,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            cursor=cursor,
            next_token=next_token,
        )
        raw = await self._transport.request(
            "GET", "/testing/runs", params=params, request_options=request_options
        )
        items = [
            TestRunListItem.model_validate(i) for i in raw.get("runs", raw.get("items", []))
        ]
        return Page(items=items, next_token=raw.get("nextCursor", raw.get("nextToken")))

    async def get(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> TestRunDetails:
        raw = await self._transport.request(
            "GET", f"/testing/runs/{run_id}", request_options=request_options
        )
        return TestRunDetails.model_validate(raw)

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
            is_terminal=_is_run_settled,
            timeout=timeout,
            initial_interval=poll_interval,
            on_update=on_update,
        )


class _AsyncCarrierRoutes:
    """Routes on a carrier integration — /testing/carrier-integrations/{id}/routes."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list(
        self, integration_id: str, *, request_options: RequestOptions | None = None
    ) -> builtins.list[CarrierRoute]:
        """All routes on an integration, sorted by name. Not paginated."""
        raw = await self._transport.request(
            "GET",
            f"/testing/carrier-integrations/{integration_id}/routes",
            request_options=request_options,
        )
        return [CarrierRoute.model_validate(r) for r in raw.get("routes", [])]

    async def get(
        self,
        integration_id: str,
        route_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> CarrierRoute:
        raw = await self._transport.request(
            "GET",
            f"/testing/carrier-integrations/{integration_id}/routes/{route_id}",
            request_options=request_options,
        )
        return CarrierRoute.model_validate(raw.get("route", raw))

    async def create(
        self,
        integration_id: str,
        *,
        name: str,
        tech_prefix: str | None = None,
        custom_headers: CustomHeaders | None = None,
        enabled: bool | None = None,
        request_options: RequestOptions | None = None,
    ) -> CarrierRoute:
        """Add a route to an integration.

        ``tech_prefix`` (up to 16 of ``0-9A-Za-z#*``) is dialled in front of the
        destination number; empty or omitted means the trunk's default route.
        ``custom_headers`` are ``X-`` headers sent on the INVITE, as
        ``CarrierCustomHeader`` models or ``{"name": ..., "value": ...}`` dicts
        (at most 10). Use the returned ``route_id`` as a test config's
        ``carrier_route_id``.
        """
        raw = await self._transport.request(
            "POST",
            f"/testing/carrier-integrations/{integration_id}/routes",
            json=_build_route_create_body(
                name=name,
                tech_prefix=tech_prefix,
                custom_headers=custom_headers,
                enabled=enabled,
            ),
            request_options=request_options,
        )
        return CarrierRoute.model_validate(raw.get("route", raw))

    async def update(
        self,
        integration_id: str,
        route_id: str,
        *,
        name: str | None = None,
        tech_prefix: str | None = None,
        custom_headers: CustomHeaders | None = None,
        enabled: bool | None = None,
        request_options: RequestOptions | None = None,
    ) -> CarrierRoute:
        """Change a route. Send only what changes; at least one field.

        ``tech_prefix=""`` switches to the trunk's default route and
        ``custom_headers=[]`` removes all headers. ``enabled=False`` turns the
        route off: runs that name it are refused, never dialled another way.
        """
        body = _build_route_update_body(
            name=name,
            tech_prefix=tech_prefix,
            custom_headers=custom_headers,
            enabled=enabled,
        )
        raw = await self._transport.request(
            "PATCH",
            f"/testing/carrier-integrations/{integration_id}/routes/{route_id}",
            json=body,
            request_options=request_options,
        )
        return CarrierRoute.model_validate(raw.get("route", raw))


class _AsyncCarrierIntegrations:
    """Bring-your-own-carrier (invite-only): the workspace's own SIP trunks —
    /testing/carrier-integrations. Trunks are set up by nopaque and read-only
    here; their routes are managed under ``.routes``.
    """

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport
        self.routes = _AsyncCarrierRoutes(transport)

    async def list(
        self, *, request_options: RequestOptions | None = None
    ) -> builtins.list[CarrierIntegration]:
        """All of the workspace's carrier integrations, each with its routes,
        sorted by name. Not paginated; empty when the workspace has none.
        """
        raw = await self._transport.request(
            "GET", "/testing/carrier-integrations", request_options=request_options
        )
        return [CarrierIntegration.model_validate(i) for i in raw.get("integrations", [])]

    async def get(
        self, integration_id: str, *, request_options: RequestOptions | None = None
    ) -> CarrierIntegration:
        raw = await self._transport.request(
            "GET",
            f"/testing/carrier-integrations/{integration_id}",
            request_options=request_options,
        )
        return CarrierIntegration.model_validate(raw.get("integration", raw))


class AsyncTestingResource(AsyncResource):
    """Asynchronous /testing/* endpoints. Nested: configs, jobs, runs,
    carrier_integrations."""

    def __init__(self, transport: AsyncTransport) -> None:
        super().__init__(transport)
        self.configs = _AsyncConfigs(transport)
        self.jobs = _AsyncJobs(transport)
        self.runs = _AsyncRuns(transport)
        self.carrier_integrations = _AsyncCarrierIntegrations(transport)

    async def aggregate_runs(
        self,
        *,
        group_by: str,
        run_type: str | None = None,
        outcome: str | None = None,
        phone_number: str | None = None,
        config_id: str | None = None,
        catalogue_test_id: str | None = None,
        started_after: str | None = None,
        started_before: str | None = None,
        time_bucket: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> TestRunAggregateResponse:
        """Aggregate test runs — GET /testing/runs/aggregate.

        ``group_by`` is required (one of ``outcome``, ``runType``, ``configId``,
        ``catalogueTestId``, ``phoneNumber``). Pass ``time_bucket`` (``day`` |
        ``week`` | ``month``) to get time-bucketed groups instead of flat groups.
        """
        params: dict = {"groupBy": group_by}
        if run_type is not None:
            params["runType"] = run_type
        if outcome is not None:
            params["outcome"] = outcome
        if phone_number is not None:
            params["phoneNumber"] = phone_number
        if config_id is not None:
            params["configId"] = config_id
        if catalogue_test_id is not None:
            params["catalogueTestId"] = catalogue_test_id
        if started_after is not None:
            params["startedAfter"] = started_after
        if started_before is not None:
            params["startedBefore"] = started_before
        if time_bucket is not None:
            params["timeBucket"] = time_bucket
        raw = await self._transport.request(
            "GET", "/testing/runs/aggregate", params=params, request_options=request_options
        )
        return TestRunAggregateResponse.model_validate(raw)

    async def get_mission_test_run(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> MissionTestRunResponse:
        """Get a mission test run — GET /testing/mission-test-runs/{id}.

        Mission-strict shape (no ``stepResults`` — mission tests have no steps).
        """
        raw = await self._transport.request(
            "GET",
            f"/testing/mission-test-runs/{run_id}",
            request_options=request_options,
        )
        return MissionTestRunResponse.model_validate(raw)

    async def list_voices(
        self,
        *,
        request_options: RequestOptions | None = None,
    ) -> ListVoicesResponse:
        """Operator-enabled voices a mission test may use, and which is default."""
        raw = await self._transport.request(
            "GET", "/testing/voices", request_options=request_options
        )
        return ListVoicesResponse.model_validate(raw)
