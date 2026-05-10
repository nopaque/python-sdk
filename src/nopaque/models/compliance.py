"""Models for /testing/compliance-* endpoints."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict

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


class ComplianceTest(_ComplianceBase):
    id: str
    title: str
    severity: ComplianceSeverity
    regulation_keys: List[str]


class ComplianceRegulation(_ComplianceBase):
    key: str
    label: str
    test_ids: List[str]


class ComplianceCatalogue(_ComplianceBase):
    version: str
    regulations: List[ComplianceRegulation]
    tests: List[ComplianceTest]


class ComplianceCatalogueResponse(_ComplianceBase):
    catalogue: ComplianceCatalogue
    picker_limit: int
    s2stest_seconds_available: int
    tier: str


class CreateComplianceBatchRequest(_ComplianceBase):
    phone_number: str
    sector: str
    test_ids: List[str]


class CreateComplianceBatchResponse(_ComplianceBase):
    run_ids: List[str]
    report_url: str


class ComplianceTestEvidence(_ComplianceBase):
    turn: int
    quote: str


class ComplianceTestVerdict(_ComplianceBase):
    test_id: str
    verdict: ComplianceVerdict
    evidence: Optional[List[ComplianceTestEvidence]] = None
    judge_rationale: Optional[str] = None


class ComplianceRegulationSection(_ComplianceBase):
    regulation_key: str
    label: str
    passed: int
    failed: int
    pending: int
    verdicts: List[ComplianceTestVerdict]


class ComplianceReportSummary(_ComplianceBase):
    phone_number: str
    catalogue_version: str
    passed: int
    failed: int
    pending: int
    generated_at: str


class ComplianceReport(_ComplianceBase):
    summary: ComplianceReportSummary
    sections: List[ComplianceRegulationSection]


class ComplianceReportListItem(_ComplianceBase):
    phone_number: str
    passed: int
    failed: int
    total: int
    last_run_at: str


class GeneratePdfRequest(_ComplianceBase):
    regulation_key: Optional[str] = None


class GeneratePdfResponse(_ComplianceBase):
    """Response from POST /testing/compliance-reports/{phone}/pdf.

    The presigned URL has a 1-hour expiry baked into the signed query string;
    the response body is ``{ url }`` only.
    """

    url: str
