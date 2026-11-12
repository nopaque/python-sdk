"""Models for enrichment endpoints under /mapping/{jobId}/runs/{runId}/."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, model_validator

_ALIAS_MAP = {
    "job_id": "jobId",
    "run_id": "runId",
    "overall_score": "overallScore",
    "ivr_analysis_tokens": "ivrAnalysisTokens",
    "quality_scoring_tokens": "qualityScoringTokens",
    "total_tokens": "totalTokens",
    "input_tokens": "inputTokens",
    "output_tokens": "outputTokens",
    "event_count": "eventCount",
    "enrichment_types": "enrichmentTypes",
    "enrichment_id": "enrichmentId",
    "enrichment_type": "enrichmentType",
    "completed_at": "completedAt",
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
    """One enrichment of a mapping run.

    The API returns a **completed** enrichment as its result alone, unwrapped
    (for ``quality_scoring``: ``overallScore``, ``sentiment``, ``dimensions``
    and so on), and anything else (queued, running, failed) as the stored
    record with ``status``, ``data`` and ``error``. Both are read into this
    model: ``results`` holds the result in either case (``None`` until there
    is one), ``status`` is ``"completed"`` for an unwrapped result, and
    ``job_id``, ``run_id`` and ``type`` are filled from the request. The
    unwrapped fields also stay readable as extras, e.g.
    ``model_dump()["overallScore"]``.
    """

    job_id: Optional[str] = None
    run_id: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    enrichment_id: Optional[str] = None
    enrichment_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    completed_at: Optional[str] = None


def _normalise_enrichment(
    raw: Any, job_id: str, run_id: str, enrichment_type: str
) -> Any:
    """Bring both response forms of GET .../enrichments/{type} to one shape."""
    if not isinstance(raw, dict):
        return raw
    is_record = "enrichmentType" in raw or "enrichmentId" in raw
    if is_record:
        out: Dict[str, Any] = dict(raw)
        out.setdefault("results", raw.get("data"))
        out.setdefault("type", raw.get("enrichmentType") or enrichment_type)
    else:
        out = {**raw, "status": "completed", "results": dict(raw), "type": enrichment_type}
    out.setdefault("jobId", job_id)
    out.setdefault("runId", run_id)
    return out


class TokenUsageTotals(_EnrichmentBase):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ServiceTokenUsage(TokenUsageTotals):
    """Token totals for one service, and how many usage events made them up."""

    event_count: int = 0


class TokenUsageDetails(_EnrichmentBase):
    """The 0.14.0 summary, now filled from ``services`` and ``total``.

    Each value is that service's ``total_tokens``.
    """

    ivr_analysis_tokens: Optional[int] = None
    quality_scoring_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class TokenUsage(_EnrichmentBase):
    """Response from GET /mapping/{jobId}/runs/{runId}/token-usage.

    ``services`` is keyed by service (``ivr_analysis``, ``quality_scoring``);
    ``total`` sums them. ``job_id`` is filled from the request.
    """

    job_id: Optional[str] = None
    run_id: Optional[str] = None
    services: Dict[str, ServiceTokenUsage] = {}
    total: Optional[TokenUsageTotals] = None
    usage: Optional[TokenUsageDetails] = None

    @model_validator(mode="before")
    @classmethod
    def _fill_usage(cls, data: Any) -> Any:
        if not isinstance(data, dict) or data.get("usage") is not None:
            return data
        services = data.get("services")
        total = data.get("total")
        if not isinstance(services, dict) and not isinstance(total, dict):
            return data

        def tokens(block: Any) -> Optional[int]:
            return block.get("totalTokens") if isinstance(block, dict) else None

        services = services if isinstance(services, dict) else {}
        return {
            **data,
            "usage": {
                "ivrAnalysisTokens": tokens(services.get("ivr_analysis")),
                "qualityScoringTokens": tokens(services.get("quality_scoring")),
                "totalTokens": tokens(total),
            },
        }


class EnrichmentJob(_EnrichmentBase):
    job_id: Optional[str] = None
    run_id: Optional[str] = None
    status: str
    enrichment_types: Optional[List[str]] = None
    queued_at: Optional[str] = None
