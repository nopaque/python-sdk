"""Models for /mapping endpoints."""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


def _alias(name: str) -> str:
    """snake_case field name -> camelCase wire name.

    This was previously a hand-maintained dict with a silent fallback to the
    unchanged name, which meant any field missing an entry serialised as
    snake_case and was ignored by the API. `RetryConfig.max_retries` had been
    doing exactly that — it went out as `max_retries`, so retry settings never
    applied. All 59 entries in that map were plain camelisations, so the
    conversion is now computed and cannot fall out of sync.
    """
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


JobStatus = Literal[
    "idle",
    "created",
    "queued",
    "running",
    "completed",
    "failed",
    "limited",
    "cancelled",
]
StepStatus = Literal[
    "pending", "running", "completed", "failed", "retrying", "skipped"
]
MappingMode = Literal["dtmf", "dtmf-audio", "full-audio"]
Vertical = Literal["FSI", "Healthcare", "EnergyUtilities", "Telecoms", "General"]
RepeatBehavior = Literal["skip", "explore_once", "explore_n"]


class _MappingBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class MappingJobStats(_MappingBase):
    total_calls: int = 0
    completed_calls: int = 0
    failed_calls: int = 0
    loops_detected: int = 0
    retried_calls: int = 0


class RetryConfig(_MappingBase):
    enabled: bool = False
    max_retries: int = 3


class RepeatConfig(_MappingBase):
    """Repeat-detection behaviour for menus revisited via a different path."""

    behavior: RepeatBehavior = "skip"
    #: Only meaningful when ``behavior`` is ``explore_n``. Defaults to 2 server-side.
    max_explorations: Optional[int] = None


class EnrichmentConfig(_MappingBase):
    """Post-run enrichment pipeline settings."""

    enabled: bool = False
    #: Defaults to ``["quality_scoring"]`` server-side.
    types: Optional[List[str]] = None


class MappingJobConfig(_MappingBase):
    """Per-job mapping configuration.

    Every mode-related knob lives here rather than at the top of the request
    body — the API reads ``body.config.mapping_mode``, and a top-level
    ``mapping_mode`` is ignored.
    """

    max_depth: Optional[int] = None
    max_calls: Optional[int] = None
    max_duration_minutes: Optional[int] = None
    max_concurrency: Optional[int] = None
    language: Optional[str] = None
    voice_profile_id: Optional[str] = None
    data_profile_id: Optional[str] = None
    retry_config: Optional[RetryConfig] = None
    repeat_config: Optional[RepeatConfig] = None
    enrichment_config: Optional[EnrichmentConfig] = None
    mapping_mode: Optional[MappingMode] = None
    #: Required by the API when ``mapping_mode`` is ``dtmf-audio`` or ``full-audio``.
    vertical: Optional[Vertical] = None
    #: Security-probe mode. The API rejects it combined with ``mapping_mode="dtmf"``.
    probe_mode: Optional[bool] = None


class CurrentRun(_MappingBase):
    """Nested run summary surfaced on the single-job ``GET /mapping/{id}`` response.

    Unlike job-level ``status`` (which cycles idle/running and never reaches
    ``completed``), ``CurrentRun.status`` CAN reach a terminal value. Present
    when a run exists; omitted (never ``null``) when the job has no runs yet.
    """

    id: Optional[str] = None
    status: Optional[str] = None
    run_number: Optional[int] = None
    stats: Optional[MappingJobStats] = None
    in_flight_count: Optional[int] = None
    limit_reason: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class MappingJob(_MappingBase):
    id: str
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    name: str
    phone_number: Optional[str] = None
    profile_id: Optional[str] = None
    status: str
    run_id: Optional[str] = None
    run_number: Optional[int] = None
    config: Optional[MappingJobConfig] = None
    stats: Optional[MappingJobStats] = None
    in_flight_count: Optional[int] = None
    pending_paths: Optional[List[str]] = None
    current_run_id: Optional[str] = None
    current_run: Optional[CurrentRun] = None
    limit_reason: Optional[str] = None
    error: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cancelled_at: Optional[str] = None


class MappingJobListItem(_MappingBase):
    """Slim projection returned by ``GET /mapping`` (list).

    NOTE: ``status`` here is the LATEST-RUN status (post-merged from
    ``currentRun.status``), not the job-level idle/running cycle. For the
    full job shape and run detail, call ``mapping.get(id)``.
    """

    id: str
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    name: str
    phone_number: Optional[str] = None
    profile_id: Optional[str] = None
    status: str
    config: Optional[MappingJobConfig] = None
    tags: Optional[List[str]] = None
    error: Optional[str] = None
    run_number: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DTMFOption(_MappingBase):
    digit: str
    label: Optional[str] = None


class StepResult(_MappingBase):
    transcript: str = ""
    dtmf_options: List[DTMFOption] = []
    is_terminal: bool = False
    audio_url: Optional[str] = None
    audio_size_bytes: Optional[int] = None
    duration: Optional[float] = None


class MappingStep(_MappingBase):
    id: Optional[str] = None
    step_id: Optional[str] = None
    job_id: Optional[str] = None
    run_id: Optional[str] = None
    workspace_id: Optional[str] = None
    parent_step_id: Optional[str] = None
    depth: int = 0
    path: List[str] = []
    path_string: Optional[str] = None
    status: str
    retry_count: int = 0
    result: Optional[StepResult] = None
    transcript_hash: Optional[str] = None
    transcript: Optional[str] = None
    dtmf_option: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class InputRequired(_MappingBase):
    """Per-step UX hint for prompts that require user input (e.g. PIN/account)."""

    type: Optional[str] = None
    description: Optional[str] = None
    format_hint: Optional[str] = None
    terminator: Optional[str] = None
    start_time_ms: Optional[int] = None


class TreeNode(_MappingBase):
    step_id: Optional[str] = None
    path: Optional[str] = None
    dtmf_option: Optional[str] = None
    digit: Optional[str] = None
    label: Optional[str] = None
    depth: Optional[int] = None
    status: Optional[str] = None
    transcript: Optional[str] = None
    is_terminal: bool = False
    children: List["TreeNode"] = []
    duration: Optional[float] = None
    audio_url: Optional[str] = None
    # v0.3.0 enrichment fields (optional, omitted when absent)
    step_type: Optional[Literal["dtmf", "voice"]] = None
    voice_prompt: Optional[str] = None
    menu_label: Optional[str] = None
    spoken_response: Optional[str] = None
    probe_category: Optional[str] = None
    probe_classification: Optional[str] = None
    probe_rationale: Optional[str] = None
    input_required: Optional[InputRequired] = None


TreeNode.model_rebuild()


class MappingTree(_MappingBase):
    job_id: Optional[str] = None
    run_id: Optional[str] = None
    run_number: Optional[int] = None
    status: Optional[str] = None
    stats: Optional[MappingJobStats] = None
    tree: Optional[TreeNode] = None
    root: Optional[TreeNode] = None
    # Flat format returns a `steps` array instead of a nested `tree`.
    steps: Optional[List[TreeNode]] = None
    # Empty-state envelope (200 OK): when the tree is empty, `tree` is null and
    # `reason` explains why. Branch on `tree is None`.
    reason: Optional[Literal["no_runs", "no_steps", "in_progress"]] = None
    message: Optional[str] = None


class MappingPath(_MappingBase):
    """A single path in a mapping job's path table."""

    job_id: Optional[str] = None
    path: str
    status: Optional[str] = None
    transcript: Optional[str] = None
    is_terminal: Optional[bool] = None
    repeat_behavior: Optional[str] = None


class MappingRun(_MappingBase):
    """A single run of a mapping job."""

    id: Optional[str] = None
    run_id: Optional[str] = None
    job_id: Optional[str] = None
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    stats: Optional[MappingJobStats] = None


class ProbeResult(_MappingBase):
    """Result of POST /mapping/{jobId}/runs/{runId}/probe.

    Triggers on-demand security-probe analysis on a completed mapping run.
    The body is the queue summary; poll the run / steps afterwards to see
    classified results land.
    """

    message: str
    probe_count: int


# ============================================================================
# Telemetry (v0.3.0) — permissive, all-optional. The wire contract carries
# `schemaVersion: 1` plus nested optional groups; emitters may ship ahead of
# consumers, so every model tolerates unknown fields (extra="allow" via the
# shared base). Nested groups are left as free-form dicts intentionally.
# ============================================================================


class TurnTelemetry(_MappingBase):
    """Per-step / per-turn telemetry (optional). All fields optional."""

    schema_version: Optional[int] = None
    timing: Optional[dict] = None
    transcript: Optional[dict] = None
    dtmf: Optional[dict] = None
    llm_extraction: Optional[dict] = None
    conversation_turn: Optional[dict] = None


class CallTelemetry(_MappingBase):
    """Call-level telemetry (optional). All fields optional."""

    schema_version: Optional[int] = None
    telephony: Optional[dict] = None
    quality: Optional[dict] = None
    audio: Optional[dict] = None
    cost: Optional[dict] = None
    timing: Optional[dict] = None
    mode: Optional[dict] = None
    turns: Optional[List[TurnTelemetry]] = None
