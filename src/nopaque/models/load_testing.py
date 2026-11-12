"""Models for /testing/load-tests and /testing/reports endpoints."""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict

_ALIAS_MAP = {
    "config_id": "configId",
    "load_test_id": "loadTestId",
    "run_id": "runId",
    "total_calls": "totalCalls",
    "completed_calls": "completedCalls",
    "pass_rate": "passRate",
    "estimated_minutes": "estimatedMinutes",
    "estimated_cost": "estimatedCost",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "started_at": "startedAt",
    "completed_at": "completedAt",
    "aborted_at": "abortedAt",
}


def _alias(name: str) -> str:
    """snake_case field name -> camelCase wire name.

    The listed names win; anything else is camelised, so a new field binds
    from the camelCase response rather than leaking through as a raw extra.
    """
    if name in _ALIAS_MAP:
        return _ALIAS_MAP[name]
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


class _LoadTestingBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class LoadTest(_LoadTestingBase):
    id: str
    name: str
    config_id: Optional[str] = None
    concurrency: Optional[int] = None
    total_calls: Optional[int] = None
    status: Optional[str] = None
    run_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    aborted_at: Optional[str] = None


class LoadTestEstimate(_LoadTestingBase):
    estimated_minutes: Optional[float] = None
    estimated_cost: Optional[str] = None
    concurrency: Optional[int] = None
    total_calls: Optional[int] = None


class LoadTestProgress(_LoadTestingBase):
    completed_calls: Optional[int] = None
    total_calls: Optional[int] = None
    pass_rate: Optional[float] = None


class LoadTestPercentiles(_LoadTestingBase):
    p50: Optional[float] = None
    p5: Optional[float] = None
    p95: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None


class LoadTestQualitySummary(_LoadTestingBase):
    """Call quality across the run. ``estimated_mos`` carries p50, p5 and min;
    the others p50, p95 and max."""

    calls: int = 0
    poor_calls: int = 0
    estimated_mos: Optional[LoadTestPercentiles] = None
    packet_loss_pct: Optional[LoadTestPercentiles] = None
    jitter_ms: Optional[LoadTestPercentiles] = None
    answer_secs: Optional[LoadTestPercentiles] = None


class LoadTestRunStats(_LoadTestingBase):
    """Running totals for a load-test run. Percentiles are call durations in seconds."""

    started: int = 0
    completed: int = 0
    failed: int = 0
    errors: int = 0
    p50: Optional[float] = None
    p95: Optional[float] = None
    p99: Optional[float] = None
    offered: Optional[int] = None
    dropped: Optional[int] = None
    caller_id_pool: Optional[int] = None
    caller_id_workspace_default: Optional[int] = None
    caller_id_platform_default: Optional[int] = None
    quality_calls: Optional[int] = None
    poor_quality_calls: Optional[int] = None
    quality: Optional[LoadTestQualitySummary] = None
    #: Failed calls per failure-pattern id.
    patterns: Optional[Dict[str, int]] = None
    late_starts: Optional[int] = None
    late_starts_passed: Optional[int] = None


class LoadTestStatus(_LoadTestingBase):
    """Response from GET /testing/load-tests/{id}/status.

    Progress is ``current_second`` of ``total_seconds`` (``progress_percent``
    rounds it); ``stats`` holds the call counts so far. ``status`` is one of
    ``pending``, ``running``, ``completed``, ``aborted`` or ``failed``.
    """

    id: Optional[str] = None
    name: Optional[str] = None
    test_config_id: Optional[str] = None
    load_test_config_id: Optional[str] = None
    group_id: Optional[str] = None
    lane_index: Optional[int] = None
    group_size: Optional[int] = None
    status: str
    current_second: Optional[int] = None
    total_seconds: Optional[int] = None
    progress_percent: Optional[float] = None
    stats: Optional[LoadTestRunStats] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    aborted_at: Optional[str] = None
    abort_reason: Optional[str] = None
    error_message: Optional[str] = None
    #: The load-test config as this run sees it (a grouped run's own lane).
    config: Optional[Dict[str, Any]] = None
    #: Never sent by the API; always ``None``. Use ``current_second``,
    #: ``total_seconds`` and ``stats``.
    progress: Optional[LoadTestProgress] = None


class LoadTestRun(_LoadTestingBase):
    run_id: Optional[str] = None
    id: Optional[str] = None
    load_test_id: Optional[str] = None
    status: str
    pass_rate: Optional[float] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# ==== Reports - /testing/reports =============================================

#: A report file. ``data`` is a zip of every record, CSVs, recordings and a
#: manual; ``excel`` a workbook; ``pdf`` a written report.
ReportPack = Literal["data", "excel", "pdf"]
#: ``group`` (default) covers every lane started with the run; ``lane`` the run only.
FailurePatternScope = Literal["group", "lane"]


class ReportFile(_LoadTestingBase):
    """One built file of a report. ``pack`` is ``data``, ``excel`` or ``pdf``."""

    pack: str
    file_name: str
    size_bytes: int
    content_type: str


class ReportCounts(_LoadTestingBase):
    runs: Optional[int] = None
    calls: Optional[int] = None
    steps: Optional[int] = None
    recordings: Optional[int] = None


class Report(_LoadTestingBase):
    """A detailed report over one or more finished load-test runs.

    ``status`` moves ``pending`` -> ``running`` -> ``ready`` (or ``failed``).
    ``files`` is empty until the report is ``ready``.
    """

    report_id: str
    name: str
    kind: Optional[str] = None
    load_test_run_ids: List[str] = []
    packs: List[str] = []
    include_audio: Optional[bool] = None
    #: ``pending``, ``running``, ``ready`` or ``failed``. Typed ``str`` so a new
    #: server status never makes a read raise.
    status: str
    progress: Optional[str] = None
    requested_by: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    counts: Optional[ReportCounts] = None
    files: List[ReportFile] = []
    error: Optional[str] = None


class ReportFileDownload(_LoadTestingBase):
    """A pre-signed link to one report file, valid for 1 hour."""

    url: str
    file_name: str
    size_bytes: int
    expires_at: str


# ==== Exports - /testing/load-tests/{id}/exports ==============================


class LoadTestExportCounts(_LoadTestingBase):
    calls: Optional[int] = None
    steps: Optional[int] = None


class LoadTestExport(_LoadTestingBase):
    """A zip of every call and step in a load-test run.

    ``status`` moves ``pending`` -> ``running`` -> ``ready`` (or ``failed``).
    ``download_url`` is present only when ``ready`` and is valid for 1 hour;
    fetch the export again for a fresh one. Files are kept for 30 days.
    """

    export_id: str
    run_id: str
    status: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    file_name: Optional[str] = None
    size_bytes: Optional[int] = None
    counts: Optional[LoadTestExportCounts] = None
    error: Optional[str] = None
    expires_at: Optional[str] = None
    download_url: Optional[str] = None


# ==== Failure patterns - /testing/load-tests/{id}/failure-patterns ============


class FailurePattern(_LoadTestingBase):
    """One failure pattern in a run, with its count and where it was seen.

    ``owner`` is ``platform``, ``carrier``, ``system-under-test``,
    ``test-definition`` or ``unknown``. ``share`` is the fraction of failed
    calls. ``by_lane`` counts calls per lane run id.
    """

    id: str
    label: Optional[str] = None
    owner: Optional[str] = None
    description: Optional[str] = None
    count: int
    share: Optional[float] = None
    by_lane: Dict[str, int] = {}
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    examples: List[Any] = []


class FailurePatternTimelineBucket(_LoadTestingBase):
    #: The bucket's start.
    t: str
    #: Calls in progress at any point in the bucket.
    in_flight: int
    #: Failed calls started in the bucket, per pattern id.
    counts: Dict[str, int] = {}


class FailurePatternTimeline(_LoadTestingBase):
    bucket_secs: int
    buckets: List[FailurePatternTimelineBucket] = []


class FailurePatternLane(_LoadTestingBase):
    run_id: str
    name: str


class LoadTestFailurePatterns(_LoadTestingBase):
    """A load-test run's failures grouped by pattern."""

    run_id: str
    group_id: Optional[str] = None
    scope: Optional[str] = None
    rules_version: Optional[int] = None
    total_calls: Optional[int] = None
    failed_calls: Optional[int] = None
    unclassified: Optional[int] = None
    late_starts: Optional[int] = None
    late_starts_passed: Optional[int] = None
    patterns: List[FailurePattern] = []
    timeline: Optional[FailurePatternTimeline] = None
    lanes: List[FailurePatternLane] = []


class FailurePatternCall(_LoadTestingBase):
    """One call in a failure pattern, with the evidence that put it there."""

    call_id: str
    #: The lane (load-test run) the call belongs to.
    run_id: str
    lane_name: Optional[str] = None
    started_at: Optional[str] = None
    failed_step_index: Optional[int] = None
    failed_step_name: Optional[str] = None
    evidence: Dict[str, Any] = {}
    recording_available: Optional[bool] = None


class ReclassifyFailurePatternsResponse(_LoadTestingBase):
    """Returned at once; the reclassification runs in the background."""

    job_id: str
