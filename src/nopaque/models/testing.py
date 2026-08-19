"""Models for /testing endpoints."""
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict


def _alias(name: str) -> str:
    """snake_case field name -> camelCase wire name.

    Computed rather than listed. The previous hand-maintained dict fell back to
    the unchanged name on a miss, so a field with no entry silently failed to
    bind from the camelCase response and leaked through as a raw extra. All 29
    entries were plain camelisations, so nothing changes for existing fields.
    """
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


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
    #: Terminal verdict. The API never sends a ``result`` field — a model
    #: declaring one read as None on every run, including passing ones.
    #: Values are uppercase: PASS | FAIL | ERROR | INCONCLUSIVE | pending.
    outcome: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    launch_deadline: Optional[str] = None
    total_steps: Optional[int] = None
    passed_steps: Optional[int] = None
    failed_steps: Optional[int] = None


class TestStepResult(_TestingBase):
    """A single scripted step's result.

    Named ``TestStepResult``, not ``StepResult`` — the latter is already
    exported for mapping and is an unrelated shape.
    """

    id: str
    run_id: Optional[str] = None
    step_index: Optional[int] = None
    step_id: Optional[str] = None
    step_name: Optional[str] = None
    outcome: Optional[Literal["PASS", "FAIL", "TIMEOUT", "ERROR"]] = None
    expected_transcript: Optional[str] = None
    actual_transcript: Optional[str] = None
    similarity: Optional[float] = None
    threshold: Optional[float] = None
    action_type: Optional[str] = None
    action_value: Optional[str] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    matcher_scores: Optional[dict] = None
    turn_telemetry: Optional[dict] = None
    created_at: Optional[str] = None


class TestRunDetails(TestRun):
    """What ``testing.runs.get()`` returns: the run row enriched with its step
    results, the joined transcript, and a snapshot of the parent config.

    Mission and compliance runs have no scripted steps, so ``step_results`` is
    empty and ``config`` absent for those.
    """

    step_results: List[TestStepResult] = []
    full_transcript: Optional[str] = None
    config: Optional[Any] = None


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
