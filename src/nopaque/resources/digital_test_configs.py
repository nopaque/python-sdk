"""Digital test configs resource - the /digital-testing/configs endpoints.

Beta. Access is limited to beta workspaces during the beta period.

Saved, reusable digital test definitions. A config is launched into a run with
:meth:`DigitalTestConfigsResource.launch`, which goes through the same code path
as ``POST /digital-testing/runs``.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.digital_testing import (
    CreateDigitalTestConfigRequest,
    CreateDigitalTestRunResponse,
    DigitalTestConfig,
    DigitalTestKind,
    DigitalTestRun,
    LaunchDigitalTestConfigRequest,
    UpdateDigitalTestConfigRequest,
)
from .digital_testing import ChatStepInput, DigitalProfileInput, DigitalTargetInput

__all__ = ["AsyncDigitalTestConfigsResource", "DigitalTestConfigsResource"]


def _apply_cursor(params: dict) -> dict:
    """Translate the paginator's injected `nextToken` into the spec `cursor` param."""
    p = dict(params)
    if "nextToken" in p:
        p["cursor"] = p.pop("nextToken")
    return p


def _build_list_params(
    *,
    limit: Optional[int],
    cursor: Optional[str],
    next_token: Optional[str],
) -> dict:
    params: dict = {}
    if limit is not None:
        params["limit"] = limit
    if cursor is not None:
        params["cursor"] = cursor
    elif next_token is not None:
        params["cursor"] = next_token
    return params


def _config_fields(
    *,
    name: Optional[str],
    description: Optional[str],
    target_ref: Optional[str],
    target: Optional[DigitalTargetInput],
    sector: Optional[str],
    mission: Optional[str],
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
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "name": name,
        "description": description,
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
    return {k: v for k, v in payload.items() if v is not None}


def _build_create_config_body(**fields: Any) -> dict:
    # Validated through `model_validate` rather than the constructor so callers
    # may pass plain dicts for `target`, `profile` and `steps` as well as the
    # models; the model's `populate_by_name` accepts these snake_case keys.
    model = CreateDigitalTestConfigRequest.model_validate(_config_fields(**fields))
    return model.model_dump(by_alias=True, exclude_none=True)


def _build_update_config_body(**fields: Any) -> dict:
    model = UpdateDigitalTestConfigRequest.model_validate(_config_fields(**fields))
    return model.model_dump(by_alias=True, exclude_none=True)


def _build_launch_body(
    *,
    target_ref: Optional[str],
    target: Optional[DigitalTargetInput],
    samples: Optional[int],
) -> dict:
    payload: Dict[str, Any] = {
        "target_ref": target_ref,
        "target": target,
        "samples": samples,
    }
    model = LaunchDigitalTestConfigRequest.model_validate(
        {k: v for k, v in payload.items() if v is not None}
    )
    return model.model_dump(by_alias=True, exclude_none=True)


class DigitalTestConfigsResource(SyncResource):
    """Synchronous /digital-testing/configs endpoints."""

    def create(
        self,
        *,
        name: str,
        target_ref: str,
        target: DigitalTargetInput,
        sector: str,
        mission: str,
        description: str | None = None,
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
    ) -> DigitalTestConfig:
        """Save a reusable digital test config.

        Beta. Access is limited to beta workspaces during the beta period.

        ``name``, ``target_ref``, ``target``, ``sector`` and ``mission`` are
        required by the API, so they are required here too. The per-kind rules
        are enforced at save time as well as at launch - ``standard`` needs
        ``steps``, the judged kinds need at least 3 ``samples``, ``freeform``
        needs ``acceptance`` and ``compliance`` needs ``catalogue_test_id`` - so
        a config that could never run is rejected with a 400 rather than stored.
        """
        body = _build_create_config_body(
            name=name,
            description=description,
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
            "/digital-testing/configs",
            json=body,
            request_options=request_options,
        )
        return DigitalTestConfig.model_validate(raw)

    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[DigitalTestConfig]:
        """List saved digital test configs, most recently updated first.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        params = _build_list_params(limit=limit, cursor=cursor, next_token=next_token)

        def fetch(p: dict) -> dict:
            raw = self._transport.request(
                "GET",
                "/digital-testing/configs",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return {
                "configs": raw.get("configs", []),
                "nextToken": raw.get("nextCursor", raw.get("nextToken")),
            }

        return SyncPaginator(
            fetch_page=fetch,
            params=params,
            model_cls=DigitalTestConfig,
            items_key="configs",
        )

    def list_page(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[DigitalTestConfig]:
        """Fetch one page of saved digital test configs.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        params = _build_list_params(limit=limit, cursor=cursor, next_token=next_token)
        raw = self._transport.request(
            "GET",
            "/digital-testing/configs",
            params=params,
            request_options=request_options,
        )
        items = [DigitalTestConfig.model_validate(c) for c in raw.get("configs", [])]
        return Page(items=items, next_token=raw.get("nextCursor", raw.get("nextToken")))

    def get(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> DigitalTestConfig:
        """Get one saved digital test config, including its steps or probes.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        raw = self._transport.request(
            "GET",
            f"/digital-testing/configs/{config_id}",
            request_options=request_options,
        )
        return DigitalTestConfig.model_validate(raw)

    def update(
        self,
        config_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        target_ref: str | None = None,
        target: DigitalTargetInput | None = None,
        sector: str | None = None,
        mission: str | None = None,
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
    ) -> DigitalTestConfig:
        """Partially update a saved digital test config.

        Beta. Access is limited to beta workspaces during the beta period.

        This is a PATCH, unlike the voice config resource, which uses PUT. Only
        the fields you pass are sent. The API validates the MERGED result rather
        than the patch alone, so an individually harmless edit that would leave
        a config unable to run is rejected with a 400.
        """
        body = _build_update_config_body(
            name=name,
            description=description,
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
            "PATCH",
            f"/digital-testing/configs/{config_id}",
            json=body,
            request_options=request_options,
        )
        return DigitalTestConfig.model_validate(raw)

    def delete(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        """Delete a saved digital test config.

        Beta. Access is limited to beta workspaces during the beta period.

        Runs already launched from it keep their ``config_id`` and their
        evidence - deleting a config does not erase the audit trail.
        """
        self._transport.request(
            "DELETE",
            f"/digital-testing/configs/{config_id}",
            request_options=request_options,
        )

    def launch(
        self,
        config_id: str,
        *,
        target_ref: str | None = None,
        target: DigitalTargetInput | None = None,
        samples: int | None = None,
        request_options: RequestOptions | None = None,
    ) -> DigitalTestRun:
        """Launch a run from a saved config.

        Beta. Access is limited to beta workspaces during the beta period.

        Everything not overridden comes from the saved config. ``target_ref``
        and ``target`` must be overridden TOGETHER - a run filed under the wrong
        ``target_ref`` would corrupt that target's report, so the API rejects a
        half-override with a 400. That is not enforced here.

        Returns the queued run, which carries ``config_id`` so it can be traced
        back to the definition that produced it. Poll it with
        :meth:`~nopaque.resources.digital_testing.DigitalTestingResource.wait_for_run`.
        """
        body = _build_launch_body(
            target_ref=target_ref, target=target, samples=samples
        )
        raw = self._transport.request(
            "POST",
            f"/digital-testing/configs/{config_id}/runs",
            json=body,
            request_options=request_options,
        )
        return CreateDigitalTestRunResponse.model_validate(raw).run


class AsyncDigitalTestConfigsResource(AsyncResource):
    """Asynchronous /digital-testing/configs endpoints."""

    async def create(
        self,
        *,
        name: str,
        target_ref: str,
        target: DigitalTargetInput,
        sector: str,
        mission: str,
        description: str | None = None,
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
    ) -> DigitalTestConfig:
        """Save a reusable digital test config.

        Beta. Access is limited to beta workspaces during the beta period.

        ``name``, ``target_ref``, ``target``, ``sector`` and ``mission`` are
        required by the API, so they are required here too. The per-kind rules
        are enforced at save time as well as at launch - ``standard`` needs
        ``steps``, the judged kinds need at least 3 ``samples``, ``freeform``
        needs ``acceptance`` and ``compliance`` needs ``catalogue_test_id`` - so
        a config that could never run is rejected with a 400 rather than stored.
        """
        body = _build_create_config_body(
            name=name,
            description=description,
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
            "/digital-testing/configs",
            json=body,
            request_options=request_options,
        )
        return DigitalTestConfig.model_validate(raw)

    def list(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[DigitalTestConfig]:
        """List saved digital test configs, most recently updated first.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        params = _build_list_params(limit=limit, cursor=cursor, next_token=next_token)

        async def fetch(p: dict) -> dict:
            raw = await self._transport.request(
                "GET",
                "/digital-testing/configs",
                params=_apply_cursor(p),
                request_options=request_options,
            )
            return {
                "configs": raw.get("configs", []),
                "nextToken": raw.get("nextCursor", raw.get("nextToken")),
            }

        return AsyncPaginator(
            fetch_page=fetch,
            params=params,
            model_cls=DigitalTestConfig,
            items_key="configs",
        )

    async def list_page(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[DigitalTestConfig]:
        """Fetch one page of saved digital test configs.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        params = _build_list_params(limit=limit, cursor=cursor, next_token=next_token)
        raw = await self._transport.request(
            "GET",
            "/digital-testing/configs",
            params=params,
            request_options=request_options,
        )
        items = [DigitalTestConfig.model_validate(c) for c in raw.get("configs", [])]
        return Page(items=items, next_token=raw.get("nextCursor", raw.get("nextToken")))

    async def get(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> DigitalTestConfig:
        """Get one saved digital test config, including its steps or probes.

        Beta. Access is limited to beta workspaces during the beta period.
        """
        raw = await self._transport.request(
            "GET",
            f"/digital-testing/configs/{config_id}",
            request_options=request_options,
        )
        return DigitalTestConfig.model_validate(raw)

    async def update(
        self,
        config_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        target_ref: str | None = None,
        target: DigitalTargetInput | None = None,
        sector: str | None = None,
        mission: str | None = None,
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
    ) -> DigitalTestConfig:
        """Partially update a saved digital test config.

        Beta. Access is limited to beta workspaces during the beta period.

        This is a PATCH, unlike the voice config resource, which uses PUT. Only
        the fields you pass are sent. The API validates the MERGED result rather
        than the patch alone, so an individually harmless edit that would leave
        a config unable to run is rejected with a 400.
        """
        body = _build_update_config_body(
            name=name,
            description=description,
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
            "PATCH",
            f"/digital-testing/configs/{config_id}",
            json=body,
            request_options=request_options,
        )
        return DigitalTestConfig.model_validate(raw)

    async def delete(
        self, config_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        """Delete a saved digital test config.

        Beta. Access is limited to beta workspaces during the beta period.

        Runs already launched from it keep their ``config_id`` and their
        evidence - deleting a config does not erase the audit trail.
        """
        await self._transport.request(
            "DELETE",
            f"/digital-testing/configs/{config_id}",
            request_options=request_options,
        )

    async def launch(
        self,
        config_id: str,
        *,
        target_ref: str | None = None,
        target: DigitalTargetInput | None = None,
        samples: int | None = None,
        request_options: RequestOptions | None = None,
    ) -> DigitalTestRun:
        """Launch a run from a saved config.

        Beta. Access is limited to beta workspaces during the beta period.

        Everything not overridden comes from the saved config. ``target_ref``
        and ``target`` must be overridden TOGETHER - a run filed under the wrong
        ``target_ref`` would corrupt that target's report, so the API rejects a
        half-override with a 400. That is not enforced here.

        Returns the queued run, which carries ``config_id`` so it can be traced
        back to the definition that produced it. Poll it with
        :meth:`~nopaque.resources.digital_testing.AsyncDigitalTestingResource.wait_for_run`.
        """
        body = _build_launch_body(
            target_ref=target_ref, target=target, samples=samples
        )
        raw = await self._transport.request(
            "POST",
            f"/digital-testing/configs/{config_id}/runs",
            json=body,
            request_options=request_options,
        )
        return CreateDigitalTestRunResponse.model_validate(raw).run
