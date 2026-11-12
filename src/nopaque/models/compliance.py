"""Models for /testing/compliance-* endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

_ALIAS_MAP = {
    "regulation_keys": "regulationKeys",
    "test_ids": "testIds",
    "regulation_key": "regulationKey",
    "test_id": "testId",
    "judge_rationale": "judgeRationale",
    "phone_number": "phoneNumber",
    "catalogue_version": "catalogueVersion",
    "generated_at": "generatedAt",
    "last_run_at": "lastRunAt",
    "run_ids": "runIds",
    "report_url": "reportUrl",
    "picker_limit": "pickerLimit",
    "s2stest_seconds_available": "s2stestSecondsAvailable",
    "compliance_seconds_available": "complianceSecondsAvailable",
    "probe_count": "probeCount",
    "pass_": "pass",
    "primary_for": "primaryFor",
    "last_run": "lastRun",
    "run_id": "runId",
    "ran_at": "ranAt",
    "completed_at": "completedAt",
    "pass_evidence": "passEvidence",
    "fail_evidence": "failEvidence",
    "judge_reasoning": "judgeReasoning",
    "audio_id": "audioId",
    "pass_rate": "passRate",
    "samples_judged": "samplesJudged",
    "samples_requested": "samplesRequested",
    "transport_errors": "transportErrors",
    "workspace_id": "workspaceId",
    "display_name": "displayName",
    "additional_context": "additionalContext",
    "carrier_route_id": "carrierRouteId",
    "updated_at": "updatedAt",
    "schema_version": "schemaVersion",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


class _ComplianceBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


ComplianceSeverity = Literal["critical", "major", "advisory"]
ComplianceVerdict = Literal["pass", "fail", "pending"]


class ComplianceCoversEntry(_ComplianceBase):
    """One regulation a catalogue test covers, and the clauses it tests."""

    regulation: str
    clauses: List[str] = []
    #: ``primary``, ``secondary`` or ``adjacent``; absent means primary.
    weight: Optional[str] = None
    rationale: Optional[str] = None


class ComplianceTestDeprecation(_ComplianceBase):
    since: str
    replaced_by: Optional[str] = None
    reason: Optional[str] = None


class ComplianceTest(_ComplianceBase):
    """A test in the compliance catalogue.

    The probes (what the tester says) are withheld by the API; ``probe_count``
    says how many there are, so a test with none cannot be run over chat.
    Read-side fields are plain strings so a value this SDK version does not
    know still parses (see ``ComplianceSeverity`` for the known severities).
    """

    id: str
    name: str
    summary: Optional[str] = None
    severity: str
    channels: List[str] = []
    sectors: List[str] = []
    jurisdictions: List[str] = []
    tags: Optional[List[str]] = None
    setup: Optional[str] = None
    mission: Optional[str] = None
    #: The pass conditions (``pass`` on the wire; a Python keyword).
    pass_: List[str] = []
    fail: List[str] = []
    covers: List[ComplianceCoversEntry] = []
    notes: Optional[str] = None
    deprecated: Optional[ComplianceTestDeprecation] = None
    probe_count: Optional[int] = None

    @property
    def regulation_keys(self) -> List[str]:
        """The keys of the regulations this test covers, from ``covers``."""
        return [c.regulation for c in self.covers]


class ComplianceInForcePhase(_ComplianceBase):
    date: str
    scope: str


class ComplianceRegulation(_ComplianceBase):
    """A regulation in the catalogue's ``regulations`` map (keyed by its key).

    ``full_ref``, ``in_force`` and ``in_force_phases`` are snake_case on the
    wire too: the catalogue is generated from YAML and passed through as is.
    """

    name: str
    jurisdiction: Optional[str] = None
    url: Optional[str] = None
    full_ref: Optional[str] = None
    in_force: Optional[str] = None
    in_force_phases: Optional[List[ComplianceInForcePhase]] = None
    notes: Optional[str] = None
    sectors: Optional[List[str]] = None


class ComplianceCatalogue(_ComplianceBase):
    version: int
    #: Keyed by regulation key, e.g. ``"eu-ai-act"``.
    regulations: Dict[str, ComplianceRegulation] = {}
    tests: List[ComplianceTest] = []


class ComplianceCatalogueResponse(_ComplianceBase):
    catalogue: ComplianceCatalogue
    #: Display only: the API no longer refuses a batch above it.
    picker_limit: Optional[int] = None
    #: Seconds left in the free tier's compliance allowance. ``None`` on paid
    #: tiers, which are metered rather than capped.
    compliance_seconds_available: Optional[int] = None
    #: Never sent by the API (the OpenAPI document names it, the handler sends
    #: ``compliance_seconds_available``). Kept so code reading it still runs.
    s2stest_seconds_available: Optional[int] = None
    tier: Optional[str] = None


class CreateComplianceBatchRequest(_ComplianceBase):
    phone_number: str
    sector: str
    test_ids: List[str]


class CreateComplianceBatchResponse(_ComplianceBase):
    run_ids: List[str]
    report_url: str


class ComplianceTestEvidence(_ComplianceBase):
    """Not used by any response: the report never had this shape. Kept for imports."""

    turn: Optional[int] = None
    quote: Optional[str] = None


class ComplianceTestVerdict(_ComplianceBase):
    """Not used by any response: the report never had this shape. Kept for imports."""

    test_id: Optional[str] = None
    verdict: Optional[str] = None
    evidence: Optional[List[ComplianceTestEvidence]] = None
    judge_rationale: Optional[str] = None


class CompliancePassEvidence(_ComplianceBase):
    condition: Optional[str] = None
    met: Optional[bool] = None
    quote: Optional[str] = None
    turn: Optional[int] = None


class ComplianceFailEvidence(_ComplianceBase):
    condition: Optional[str] = None
    triggered: Optional[bool] = None
    quote: Optional[str] = None
    turn: Optional[int] = None


class ComplianceLastRun(_ComplianceBase):
    """The latest run of a test against the number."""

    run_id: str
    ran_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: Optional[str] = None
    #: ``"pass"`` or ``"fail"``; absent until the run is judged.
    verdict: Optional[str] = None
    pass_evidence: Optional[List[CompliancePassEvidence]] = None
    fail_evidence: Optional[List[ComplianceFailEvidence]] = None
    judge_reasoning: Optional[str] = None
    transcript: Optional[str] = None
    audio_id: Optional[str] = None
    #: The catalogue version the run used, to spot runs from an older catalogue.
    catalogue_version: Optional[int] = None
    #: ``"voice"`` or ``"chat"``.
    channel: Optional[str] = None
    pass_rate: Optional[float] = None
    samples_judged: Optional[int] = None
    samples_requested: Optional[int] = None
    transport_errors: Optional[int] = None


class ComplianceReportTest(_ComplianceBase):
    """A catalogue test as it applies to one regulation section of a report."""

    id: str
    name: Optional[str] = None
    summary: Optional[str] = None
    severity: Optional[str] = None
    weight: Optional[str] = None
    clauses: List[str] = []
    primary_for: Optional[bool] = None
    #: ``None`` when the test has not been run against this number.
    last_run: Optional[ComplianceLastRun] = None


class ComplianceSectionSummary(_ComplianceBase):
    ran: int = 0
    passed: int = 0
    failed: int = 0


class ComplianceRegulationSection(_ComplianceBase):
    """One regulation's section of a compliance report."""

    key: str
    name: Optional[str] = None
    jurisdiction: Optional[str] = None
    url: Optional[str] = None
    summary: ComplianceSectionSummary = Field(default_factory=ComplianceSectionSummary)
    tests: List[ComplianceReportTest] = []


class ComplianceReportSummary(_ComplianceBase):
    """Totals over the latest run of each applicable test.

    ``total`` is the number of applicable tests, run or not.
    """

    ran: int = 0
    passed: int = 0
    failed: int = 0
    total: int = 0


class ComplianceReportMetadata(_ComplianceBase):
    display_name: Optional[str] = None
    additional_context: Optional[str] = None
    carrier_route_id: Optional[str] = None
    updated_at: Optional[str] = None


class ComplianceReport(_ComplianceBase):
    """Response from GET /testing/compliance-reports/{phoneNumber}."""

    workspace_id: Optional[str] = None
    phone_number: Optional[str] = None
    catalogue_version: Optional[int] = None
    summary: ComplianceReportSummary
    regulations: List[ComplianceRegulationSection] = []
    metadata: Optional[ComplianceReportMetadata] = None


class ComplianceRerunResponse(_ComplianceBase):
    """Response from POST /testing/compliance-runs/{runId}/rerun: the new run's id."""

    run_id: str


class ComplianceReportListItem(_ComplianceBase):
    """One audited number from GET /testing/compliance-reports.

    The api nests the counts (`summary: {ran, passed, failed}`, openapi
    ComplianceAuditSummary); they are flattened here so `passed`, `failed` and
    `total` stay the SDK's interface. `total` is `summary.ran`.
    """

    phone_number: str
    passed: int
    failed: int
    total: int
    last_run_at: str

    @model_validator(mode="before")
    @classmethod
    def _flatten_summary(cls, data: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("summary"), dict):
            summary = data["summary"]
            data = {k: v for k, v in data.items() if k != "summary"}
            data.setdefault("passed", summary.get("passed"))
            data.setdefault("failed", summary.get("failed"))
            data.setdefault("total", summary.get("ran"))
        return data


class GeneratePdfRequest(_ComplianceBase):
    regulation_key: Optional[str] = None


class GeneratePdfResponse(_ComplianceBase):
    """Response from POST /testing/compliance-reports/{phone}/pdf.

    The presigned URL has a 1-hour expiry baked into the signed query string;
    the response body is ``{ url }`` only.
    """

    url: str
