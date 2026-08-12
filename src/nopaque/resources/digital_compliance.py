"""Digital compliance resource - the /digital-testing/compliance-audits endpoints.

Beta. Access is limited to beta workspaces during the beta period.
"""
from __future__ import annotations

from typing import Any, List, Optional

from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.digital_testing import DigitalComplianceAuditSummary

__all__ = ["AsyncDigitalComplianceResource", "DigitalComplianceResource"]


def _build_report_params(*, target_ref: str, sector: Optional[str]) -> dict:
    params: dict = {"targetRef": target_ref}
    if sector is not None:
        params["sector"] = sector
    return params


class DigitalComplianceResource(SyncResource):
    """Synchronous /digital-testing/compliance-audits endpoints."""

    def list_audits(
        self, *, request_options: RequestOptions | None = None
    ) -> List[DigitalComplianceAuditSummary]:
        """List every digital target with at least one compliance run.

        Beta. Access is limited to beta workspaces during the beta period.

        Not paginated - returns the whole set in one call.
        """
        raw = self._transport.request(
            "GET",
            "/digital-testing/compliance-audits",
            request_options=request_options,
        )
        return [
            DigitalComplianceAuditSummary.model_validate(a)
            for a in raw.get("audits", [])
        ]

    def get_report(
        self,
        *,
        target_ref: str,
        sector: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Any:
        """Get the full catalogue-driven compliance report for one digital target.

        Beta. Access is limited to beta workspaces during the beta period.

        ``target_ref`` is sent as a query parameter, never a path segment - a
        targetRef such as ``acme/billing-bot`` contains a slash, and a single
        URL path segment cannot hold one. The response body is not a named
        schema in the OpenAPI document (``additionalProperties: true``), so it
        is returned as-is rather than parsed into a model that could drift
        from the server.
        """
        params = _build_report_params(target_ref=target_ref, sector=sector)
        return self._transport.request(
            "GET",
            "/digital-testing/compliance-audits/report",
            params=params,
            request_options=request_options,
        )


class AsyncDigitalComplianceResource(AsyncResource):
    """Asynchronous /digital-testing/compliance-audits endpoints."""

    async def list_audits(
        self, *, request_options: RequestOptions | None = None
    ) -> List[DigitalComplianceAuditSummary]:
        """List every digital target with at least one compliance run.

        Beta. Access is limited to beta workspaces during the beta period.

        Not paginated - returns the whole set in one call.
        """
        raw = await self._transport.request(
            "GET",
            "/digital-testing/compliance-audits",
            request_options=request_options,
        )
        return [
            DigitalComplianceAuditSummary.model_validate(a)
            for a in raw.get("audits", [])
        ]

    async def get_report(
        self,
        *,
        target_ref: str,
        sector: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Any:
        """Get the full catalogue-driven compliance report for one digital target.

        Beta. Access is limited to beta workspaces during the beta period.

        ``target_ref`` is sent as a query parameter, never a path segment - a
        targetRef such as ``acme/billing-bot`` contains a slash, and a single
        URL path segment cannot hold one. The response body is not a named
        schema in the OpenAPI document (``additionalProperties: true``), so it
        is returned as-is rather than parsed into a model that could drift
        from the server.
        """
        params = _build_report_params(target_ref=target_ref, sector=sector)
        return await self._transport.request(
            "GET",
            "/digital-testing/compliance-audits/report",
            params=params,
            request_options=request_options,
        )
