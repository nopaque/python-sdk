"""Compliance resource - all /testing/compliance-* endpoints."""
from __future__ import annotations

from typing import Optional
from urllib.parse import quote

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.compliance import (
    ComplianceCatalogueResponse,
    ComplianceReport,
    ComplianceReportListItem,
    CreateComplianceBatchRequest,
    CreateComplianceBatchResponse,
    GeneratePdfRequest,
    GeneratePdfResponse,
)
from ..models.mission_tests import MissionTestRun


def _encode_phone(phone_number: str) -> str:
    """URL-encode E.164 phone numbers so the leading + becomes %2B.

    The API gateway treats a literal + as a space; resources that put a phone
    number in the path must encode it before interpolation.
    """
    return quote(phone_number, safe="")


class ComplianceResource(SyncResource):
    """Synchronous /testing/compliance-* endpoints."""

    def get_catalogue(
        self,
        *,
        sector: Optional[str] = None,
        request_options: RequestOptions | None = None,
    ) -> ComplianceCatalogueResponse:
        params: dict = {}
        if sector is not None:
            params["sector"] = sector
        raw = self._transport.request(
            "GET",
            "/testing/compliance-catalogue",
            params=params,
            request_options=request_options,
        )
        return ComplianceCatalogueResponse.model_validate(raw)

    def run(
        self,
        *,
        phone_number: str,
        sector: str,
        test_ids: list[str],
        request_options: RequestOptions | None = None,
    ) -> CreateComplianceBatchResponse:
        """Atomic batch dispatch.

        Server enforces ``compliancePickerLimits[tier]`` on ``test_ids`` length
        and returns 402 with ``code='BATCH_SIZE_EXCEEDS_TIER'`` on overflow.
        Surfaces as a typed ``NopaqueAPIError`` with ``.code`` preserved.
        """
        body = CreateComplianceBatchRequest(
            phone_number=phone_number,
            sector=sector,
            test_ids=test_ids,
        ).model_dump(by_alias=True, exclude_none=True)
        raw = self._transport.request(
            "POST",
            "/testing/compliance-runs",
            json=body,
            request_options=request_options,
        )
        return CreateComplianceBatchResponse.model_validate(raw)

    def list_reports(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[ComplianceReportListItem]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET",
                "/testing/compliance-reports",
                params=p,
                request_options=request_options,
            )

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=ComplianceReportListItem
        )

    def list_reports_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[ComplianceReportListItem]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET",
            "/testing/compliance-reports",
            params=params,
            request_options=request_options,
        )
        items = [ComplianceReportListItem.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get_report(
        self, phone_number: str, *, request_options: RequestOptions | None = None
    ) -> ComplianceReport:
        raw = self._transport.request(
            "GET",
            f"/testing/compliance-reports/{_encode_phone(phone_number)}",
            request_options=request_options,
        )
        return ComplianceReport.model_validate(raw)

    def generate_pdf_url(
        self,
        phone_number: str,
        *,
        regulation_key: Optional[str] = None,
        request_options: RequestOptions | None = None,
    ) -> GeneratePdfResponse:
        """Return the presigned S3 URL the platform uploaded the PDF to.

        The 1 hour expiry is baked into the URL itself; the response body is
        ``{ url }`` only.
        """
        body = GeneratePdfRequest(regulation_key=regulation_key).model_dump(
            by_alias=True, exclude_none=True
        )
        raw = self._transport.request(
            "POST",
            f"/testing/compliance-reports/{_encode_phone(phone_number)}/pdf",
            json=body,
            request_options=request_options,
        )
        return GeneratePdfResponse.model_validate(raw)

    def download_report_pdf(
        self,
        phone_number: str,
        *,
        regulation_key: Optional[str] = None,
        request_options: RequestOptions | None = None,
    ) -> bytes:
        """Convenience: get the presigned URL, then fetch the bytes.

        For applications that already have an HTTP client, prefer
        ``generate_pdf_url(...)`` and fetch the URL with that client instead.
        Reuses the transport's underlying httpx client so test mocks and
        connection pooling apply to the S3 download too.
        """
        info = self.generate_pdf_url(
            phone_number,
            regulation_key=regulation_key,
            request_options=request_options,
        )
        response = self._transport._client.get(info.url)
        response.raise_for_status()
        return response.content

    def rerun(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> MissionTestRun:
        raw = self._transport.request(
            "POST",
            f"/testing/compliance-runs/{run_id}/rerun",
            request_options=request_options,
        )
        return MissionTestRun.model_validate(raw)


class AsyncComplianceResource(AsyncResource):
    """Asynchronous /testing/compliance-* endpoints."""

    async def get_catalogue(
        self,
        *,
        sector: Optional[str] = None,
        request_options: RequestOptions | None = None,
    ) -> ComplianceCatalogueResponse:
        params: dict = {}
        if sector is not None:
            params["sector"] = sector
        raw = await self._transport.request(
            "GET",
            "/testing/compliance-catalogue",
            params=params,
            request_options=request_options,
        )
        return ComplianceCatalogueResponse.model_validate(raw)

    async def run(
        self,
        *,
        phone_number: str,
        sector: str,
        test_ids: list[str],
        request_options: RequestOptions | None = None,
    ) -> CreateComplianceBatchResponse:
        body = CreateComplianceBatchRequest(
            phone_number=phone_number,
            sector=sector,
            test_ids=test_ids,
        ).model_dump(by_alias=True, exclude_none=True)
        raw = await self._transport.request(
            "POST",
            "/testing/compliance-runs",
            json=body,
            request_options=request_options,
        )
        return CreateComplianceBatchResponse.model_validate(raw)

    def list_reports(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[ComplianceReportListItem]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET",
                "/testing/compliance-reports",
                params=p,
                request_options=request_options,
            )

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=ComplianceReportListItem
        )

    async def list_reports_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[ComplianceReportListItem]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET",
            "/testing/compliance-reports",
            params=params,
            request_options=request_options,
        )
        items = [ComplianceReportListItem.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get_report(
        self, phone_number: str, *, request_options: RequestOptions | None = None
    ) -> ComplianceReport:
        raw = await self._transport.request(
            "GET",
            f"/testing/compliance-reports/{_encode_phone(phone_number)}",
            request_options=request_options,
        )
        return ComplianceReport.model_validate(raw)

    async def generate_pdf_url(
        self,
        phone_number: str,
        *,
        regulation_key: Optional[str] = None,
        request_options: RequestOptions | None = None,
    ) -> GeneratePdfResponse:
        body = GeneratePdfRequest(regulation_key=regulation_key).model_dump(
            by_alias=True, exclude_none=True
        )
        raw = await self._transport.request(
            "POST",
            f"/testing/compliance-reports/{_encode_phone(phone_number)}/pdf",
            json=body,
            request_options=request_options,
        )
        return GeneratePdfResponse.model_validate(raw)

    async def download_report_pdf(
        self,
        phone_number: str,
        *,
        regulation_key: Optional[str] = None,
        request_options: RequestOptions | None = None,
    ) -> bytes:
        info = await self.generate_pdf_url(
            phone_number,
            regulation_key=regulation_key,
            request_options=request_options,
        )
        response = await self._transport._client.get(info.url)
        response.raise_for_status()
        return response.content

    async def rerun(
        self, run_id: str, *, request_options: RequestOptions | None = None
    ) -> MissionTestRun:
        raw = await self._transport.request(
            "POST",
            f"/testing/compliance-runs/{run_id}/rerun",
            request_options=request_options,
        )
        return MissionTestRun.model_validate(raw)
