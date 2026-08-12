"""Models for /testing endpoints."""
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict

_ALIAS_MAP = {
    "phone_number": "phoneNumber",
    "config_id": "configId",
    "test_config_id": "testConfigId",
    "job_id": "jobId",
    "workspace_id": "workspaceId",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "started_at": "startedAt",
    "completed_at": "completedAt",
    "launch_deadline": "launchDeadline",
    "total_steps": "totalSteps",
    "passed_steps": "passedSteps",
    "failed_steps": "failedSteps",
    # v0.3.0 additive
    "run_type": "runType",
    "catalogue_test_id": "catalogueTestId",
    "call_duration_secs": "callDurationSecs",
    "next_cursor": "nextCursor",
    "total_groups": "totalGroups",
    "pass_reasoning": "passReasoning",
    "pass_evidence": "passEvidence",
    "compliance_fail_evidence": "complianceFailEvidence",
    "compliance_pass_evidence": "compliancePassEvidence",
    "judge_reasoning": "judgeReasoning",
    "call_control_id": "callControlId",
    "audio_id": "audioId",
    "error_message": "errorMessage",
    # voices (GET /testing/voices)
    "voice_id": "voiceId",
    "is_default": "isDefault",
    "default_voice_id": "defaultVoiceId",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


class _TestingBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class TestConfig(_TestingBase):
    id: str
    name: str
    phone_number: Optional[str] = None
    steps: List[Any] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TestJob(_TestingBase):
    id: str
    config_id: Optional[str] = None
    name: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class TestRun(_TestingBase):
    """A single execution of a test.

    The primary identifier is `id` (matches what the server sends in the
    entity). Pass this to `wait_for_run()` and `get()`.
    """

    id: str
    job_id: Optional[str] = None
    test_config_id: Optional[str] = None
    workspace_id: Optional[str] = None
    status: Optional[str] = None
    result: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    launch_deadline: Optional[str] = None
    total_steps: Optional[int] = None
    passed_steps: Optional[int] = None
    failed_steps: Optional[int] = None


class TestRunListItem(_TestingBase):
    """Slim summary returned by ``GET /testing/runs`` (filtered list).

    No transcript/evidence — call ``testing.runs.get(id)`` (or, for mission
    runs, ``testing.get_mission_test_run(id)``) for the full row.
    """

    id: str
    workspace_id: Optional[str] = None
    run_type: Optional[str] = None
    config_id: Optional[str] = None
    catalogue_test_id: Optional[str] = None
    status: Optional[str] = None
    outcome: Optional[str] = None
    phone_number: Optional[str] = None
    mission: Optional[str] = None
    passed_steps: Optional[int] = None
    failed_steps: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    call_duration_secs: Optional[float] = None


class MissionTestRunResponse(_TestingBase):
    """Response for ``GET /testing/mission-test-runs/{id}``.

    Mission-strict shape — no ``stepResults`` (mission tests have no steps).
    """

    id: str
    workspace_id: Optional[str] = None
    config_id: Optional[str] = None
    status: Optional[str] = None
    outcome: Optional[str] = None
    sector: Optional[str] = None
    mission: Optional[str] = None
    acceptance: Optional[str] = None
    passed: Optional[bool] = None
    pass_reasoning: Optional[str] = None
    pass_evidence: Optional[Any] = None
    verdict: Optional[str] = None
    compliance_fail_evidence: Optional[List[Any]] = None
    compliance_pass_evidence: Optional[List[Any]] = None
    judge_reasoning: Optional[str] = None
    transcript: Optional[Any] = None
    phone_number: Optional[str] = None
    audio_id: Optional[str] = None
    call_control_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class AggregateGroup(_TestingBase):
    key: str
    count: int


class AggregateBucket(_TestingBase):
    bucket: str
    groups: List[AggregateGroup] = []


class TestRunAggregateResponse(_TestingBase):
    """Response for ``GET /testing/runs/aggregate``.

    Either ``groups`` (flat) or ``buckets`` (time-bucketed) is populated,
    depending on whether ``time_bucket`` was requested.
    """

    groups: Optional[List[AggregateGroup]] = None
    buckets: Optional[List[AggregateBucket]] = None
    truncated: Optional[bool] = None
    total_groups: Optional[int] = None


class Voice(_TestingBase):
    """An operator-enabled Telnyx text-to-speech voice.

    Customers choose from this curated set rather than the full Telnyx
    catalogue. ``GET /testing/voices``.
    """

    voice_id: str
    name: str
    language: Optional[str] = None
    accent: Optional[str] = None
    gender: Optional[Literal["male", "female", "neutral"]] = None
    provider: Optional[str] = None
    label: Optional[str] = None
    is_default: Optional[bool] = None


class ListVoicesResponse(_TestingBase):
    """Response for ``GET /testing/voices``.

    ``default_voice_id`` is absent only if no voice is flagged default.
    """

    voices: List[Voice]
    default_voice_id: Optional[str] = None
