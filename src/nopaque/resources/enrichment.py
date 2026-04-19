"""Enrichment resource.

Note: URL paths are nested under /mapping/{jobId}/runs/{runId}/, but per the
spec enrichment lives on client.enrichment (not client.mapping). This matches
the functional grouping and leaves room to move the server routes later.
"""
from __future__ import annotations

from typing import Optional

from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.enrichment import EnrichmentJob, EnrichmentResult, TokenUsage


class EnrichmentResource(SyncResource):
    def get(
        self,
        job_id: str,
        run_id: str,
        type: str,
        *,
        request_options: Optional[RequestOptions] = None,
    ) -> EnrichmentResult:
        raw = self._transport.request(
            "GET",
            f"/mapping/{job_id}/runs/{run_id}/enrichments/{type}",
            request_options=request_options,
        )
        return EnrichmentResult.model_validate(raw)

    def token_usage(
        self,
        job_id: str,
        run_id: str,
        *,
        request_options: Optional[RequestOptions] = None,
    ) -> TokenUsage:
        raw = self._transport.request(
            "GET",
            f"/mapping/{job_id}/runs/{run_id}/token-usage",
            request_options=request_options,
        )
        return TokenUsage.model_validate(raw)

    def enrich(
        self,
        job_id: str,
        run_id: str,
        *,
        request_options: Optional[RequestOptions] = None,
    ) -> EnrichmentJob:
        raw = self._transport.request(
            "POST",
            f"/mapping/{job_id}/runs/{run_id}/enrich",
            request_options=request_options,
        )
        return EnrichmentJob.model_validate(raw)


class AsyncEnrichmentResource(AsyncResource):
    async def get(
        self,
        job_id: str,
        run_id: str,
        type: str,
        *,
        request_options: Optional[RequestOptions] = None,
    ) -> EnrichmentResult:
        raw = await self._transport.request(
            "GET",
            f"/mapping/{job_id}/runs/{run_id}/enrichments/{type}",
            request_options=request_options,
        )
        return EnrichmentResult.model_validate(raw)

    async def token_usage(
        self,
        job_id: str,
        run_id: str,
        *,
        request_options: Optional[RequestOptions] = None,
    ) -> TokenUsage:
        raw = await self._transport.request(
            "GET",
            f"/mapping/{job_id}/runs/{run_id}/token-usage",
            request_options=request_options,
        )
        return TokenUsage.model_validate(raw)

    async def enrich(
        self,
        job_id: str,
        run_id: str,
        *,
        request_options: Optional[RequestOptions] = None,
    ) -> EnrichmentJob:
        raw = await self._transport.request(
            "POST",
            f"/mapping/{job_id}/runs/{run_id}/enrich",
            request_options=request_options,
        )
        return EnrichmentJob.model_validate(raw)
