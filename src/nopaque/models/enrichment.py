"""Models for enrichment endpoints under /mapping/{jobId}/runs/{runId}/."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


_ALIAS_MAP = {
    "job_id": "jobId",
    "run_id": "runId",
    "overall_score": "overallScore",
    "ivr_analysis_tokens": "ivrAnalysisTokens",
    "quality_scoring_tokens": "qualityScoringTokens",
    "total_tokens": "totalTokens",
    "enrichment_types": "enrichmentTypes",
    "queued_at": "queuedAt",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


class _EnrichmentBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class EnrichmentResult(_EnrichmentBase):
    """Single enrichment result (shape varies by `type`)."""

    job_id: Optional[str] = None
    run_id: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


class TokenUsageDetails(_EnrichmentBase):
    ivr_analysis_tokens: Optional[int] = None
    quality_scoring_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class TokenUsage(_EnrichmentBase):
    job_id: Optional[str] = None
    run_id: Optional[str] = None
    usage: Optional[TokenUsageDetails] = None


class EnrichmentJob(_EnrichmentBase):
    job_id: Optional[str] = None
    run_id: Optional[str] = None
    status: str
    enrichment_types: Optional[List[str]] = None
    queued_at: Optional[str] = None
