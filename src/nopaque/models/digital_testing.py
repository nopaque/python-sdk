"""Models for /digital-testing endpoints (chat channel).

Transcribed field-by-field from ``openapi/openapi.yaml`` — the ``Digital Testing
(chat channel)`` schema block plus the two inline compliance-audit schemas.
"""
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

_ALIAS_MAP = {
    # targets
    "instance_id": "instanceId",
    "contact_flow_id": "contactFlowId",
    "assume_role_arn": "assumeRoleArn",
    "openai_compatible": "openaiCompatible",
    "auth_ref": "authRef",
    "selector_profile": "selectorProfile",
    # steps
    "profile_item_id": "profileItemId",
    "timeout_secs": "timeoutSecs",
    # profile
    "data_items": "dataItems",
    # requests / configs
    "target_ref": "targetRef",
    "catalogue_test_id": "catalogueTestId",
    "pass_conditions": "passConditions",
    "fail_conditions": "failConditions",
    "additional_context": "additionalContext",
    "profile_id": "profileId",
    "profile_snapshot": "profileSnapshot",
    "max_turns": "maxTurns",
    # step results
    "step_id": "stepId",
    "action_type": "actionType",
    "action_value": "actionValue",
    "expected_transcript": "expectedTranscript",
    "actual_transcript": "actualTranscript",
    # samples
    "step_results": "stepResults",
    "steps_run": "stepsRun",
    "steps_total": "stepsTotal",
    "failure_reason": "failureReason",
    # runs
    "workspace_id": "workspaceId",
    "config_id": "configId",
    "user_id": "userId",
    "samples_requested": "samplesRequested",
    "samples_judged": "samplesJudged",
    "transport_errors": "transportErrors",
    "pass_rate": "passRate",
    "sample_outcomes": "sampleOutcomes",
    "payload_s3_bucket": "payloadS3Bucket",
    "payload_s3_key": "payloadS3Key",
    "payload_bytes": "payloadBytes",
    "started_at": "startedAt",
    "completed_at": "completedAt",
    "launch_deadline": "launchDeadline",
    # envelopes / config metadata
    "next_cursor": "nextCursor",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    # compliance audits
    "last_run_at": "lastRunAt",
    "run_count": "runCount",
    "catalogue_test_ids": "catalogueTestIds",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


DigitalTransport = Literal["connect-chat", "http-json", "web-widget"]
DigitalTestKind = Literal["freeform", "compliance", "standard"]
DigitalRunStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
DigitalOutcome = Literal["pass", "fail", "inconclusive"]
ChatMatcher = Literal["exact", "contains", "regex", "similarity"]


class _DigitalBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


class ConnectChatTarget(_DigitalBase):
    """Amazon Connect chat via StartChatContact plus the participant websocket."""

    transport: Literal["connect-chat"] = "connect-chat"
    instance_id: str
    contact_flow_id: str
    # Server default is ``us-east-1``; left unset so an omitted value stays omitted.
    region: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None
    assume_role_arn: Optional[str] = None


class HttpJsonTarget(_DigitalBase):
    """Generic REST chat endpoint, including OpenAI-compatible shapes."""

    transport: Literal["http-json"] = "http-json"
    endpoint: str
    openai_compatible: Optional[bool] = None
    auth_ref: Optional[str] = None


class WebWidgetTarget(_DigitalBase):
    """Browser-automated embedded chat widget, for targets with no API at all."""

    transport: Literal["web-widget"] = "web-widget"
    url: str
    selector_profile: Optional[str] = None


DigitalTarget = Annotated[
    Union[ConnectChatTarget, HttpJsonTarget, WebWidgetTarget],
    Field(discriminator="transport"),
]
"""What ``phoneNumber`` becomes on a text channel. Discriminated on ``transport``."""


# ---------------------------------------------------------------------------
# Chat steps
# ---------------------------------------------------------------------------


class ChatStepBase(_DigitalBase):
    """Fields every chat step carries."""

    id: Optional[str] = None
    name: Optional[str] = None


class SendChatStep(ChatStepBase):
    """Send a customer message.

    Supply EXACTLY ONE of ``text`` or ``profile_item_id`` — both, or neither, is
    a 400. ``profile_item_id`` is a key into ``profile.dataItems``.

    The check below mirrors the server rule exactly, which is a TRUTHINESS test
    (``Boolean(text) !== Boolean(profileItemId)``) and not a null test. An empty
    string therefore does not count as a supplied source, so a body carrying
    ``text: ""`` alongside a ``profileItemId`` is accepted here just as the
    server accepts it.
    """

    type: Literal["send"] = "send"
    text: Optional[str] = None
    profile_item_id: Optional[str] = None

    @model_validator(mode="after")
    def _exactly_one_source(self) -> "SendChatStep":
        if bool(self.text) == bool(self.profile_item_id):
            raise ValueError("send step needs exactly one of text or profile_item_id")
        return self


class ExpectChatStep(ChatStepBase):
    """Assert the bot's next message.

    ``exact`` is the server default matcher. Matching trims and collapses
    whitespace but is case-SENSITIVE.
    """

    type: Literal["expect"] = "expect"
    expected: str
    # Server defaults: matcher=exact, threshold=100 (0-100), timeoutSecs=20 (>0, <=120).
    matcher: Optional[ChatMatcher] = None
    threshold: Optional[int] = None
    timeout_secs: Optional[float] = None


class WaitChatStep(ChatStepBase):
    """Pause. For targets that rate-limit, or to let an async handoff settle."""

    type: Literal["wait"] = "wait"
    # Server default 1; must be >0 and <=60.
    seconds: Optional[float] = None


class EndChatStep(ChatStepBase):
    """Close the conversation explicitly. Optional — the runner closes the transport anyway."""

    type: Literal["end"] = "end"


ChatStep = Annotated[
    Union[SendChatStep, ExpectChatStep, WaitChatStep, EndChatStep],
    Field(discriminator="type"),
]
"""One step of a ``kind: standard`` test, discriminated on ``type``."""


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


class DigitalProfileItem(_DigitalBase):
    """One named piece of test data a ``standard`` run's steps draw on."""

    label: Optional[str] = None
    value: Optional[str] = None


class DigitalProfile(_DigitalBase):
    """Test data a ``standard`` run's steps draw on. The voice profile shape minus
    ``voiceItems``."""

    data_items: Optional[Dict[str, DigitalProfileItem]] = None


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


class DigitalStepResult(_DigitalBase):
    """Shaped like the voice ``TestStepResult``."""

    step_id: Optional[str] = None
    name: Optional[str] = None
    action_type: Optional[str] = None
    action_value: Optional[str] = None
    expected_transcript: Optional[str] = None
    actual_transcript: Optional[str] = None
    similarity: Optional[float] = None
    threshold: Optional[float] = None
    outcome: Optional[str] = None
    duration: Optional[float] = None


class DigitalSample(_DigitalBase):
    """One conversation, with its own verdict and evidence."""

    outcome: Optional[DigitalOutcome] = None
    step_results: Optional[List[DigitalStepResult]] = None
    steps_run: Optional[int] = None
    steps_total: Optional[int] = None
    transcript: Optional[str] = None
    reasoning: Optional[str] = None
    evidence: Optional[List[str]] = None
    failure_reason: Optional[str] = None


class DigitalTestRun(_DigitalBase):
    """A digital (chat) test run.

    ``status: failed`` means the test could not be DELIVERED (an infrastructure
    failure, with ``failure_reason`` set). A bot that behaved badly produces
    ``completed`` with ``outcome: fail``.
    """

    id: str
    workspace_id: str
    user_id: Optional[str] = None
    target_ref: str
    channel: Literal["chat"]
    target: Optional[DigitalTarget] = None
    kind: DigitalTestKind
    sector: Optional[str] = None
    mission: Optional[str] = None
    acceptance: Optional[str] = None
    catalogue_test_id: Optional[str] = None
    # Deliberate, documented exception to strict OpenAPI transcription: the
    # ``DigitalTestRun`` schema omits ``configId``, but the
    # ``launchDigitalTestConfig`` prose promises the run carries it, the server
    # does send it, and the voice analogue ``TestRun`` already exposes it. Do
    # not delete this as an invention when transcribing from the schema.
    config_id: Optional[str] = None
    status: DigitalRunStatus
    outcome: Optional[DigitalOutcome] = None
    samples_requested: Optional[int] = None
    samples_judged: Optional[int] = None
    passed: Optional[int] = None
    failed: Optional[int] = None
    transport_errors: Optional[int] = None
    pass_rate: Optional[float] = None
    sample_outcomes: Optional[List[str]] = None
    samples: Optional[List[DigitalSample]] = None
    payload_s3_bucket: Optional[str] = None
    payload_s3_key: Optional[str] = None
    payload_bytes: Optional[int] = None
    failure_reason: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    launch_deadline: Optional[str] = None


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class CreateDigitalTestRunRequest(_DigitalBase):
    """Body for ``POST /digital-testing/runs``.

    A standalone schema in the document — it does NOT compose
    ``DigitalTestConfigBase``, and carries no ``name``/``description``.
    """

    target_ref: str
    target: DigitalTarget
    sector: str
    mission: str
    # Server default `freeform`.
    kind: Optional[DigitalTestKind] = None
    acceptance: Optional[str] = None
    catalogue_test_id: Optional[str] = None
    pass_conditions: Optional[List[str]] = None
    fail_conditions: Optional[List[str]] = None
    setup: Optional[str] = None
    additional_context: Optional[str] = None
    profile_id: Optional[str] = None
    profile: Optional[DigitalProfile] = None
    profile_snapshot: Optional[Dict[str, Any]] = None
    probes: Optional[List[str]] = None
    steps: Optional[List[ChatStep]] = None
    # 1-10. Server defaults to 3 for the judged kinds and 1 for `standard`.
    samples: Optional[int] = None
    # 1-60. Server default 12.
    max_turns: Optional[int] = None


class DigitalTestConfigBase(_DigitalBase):
    """The reusable parts of a digital test. Every field optional here; the
    concrete request/response models tighten what is required."""

    name: Optional[str] = None
    description: Optional[str] = None
    target_ref: Optional[str] = None
    target: Optional[DigitalTarget] = None
    sector: Optional[str] = None
    mission: Optional[str] = None
    # Server default `freeform`.
    kind: Optional[DigitalTestKind] = None
    acceptance: Optional[str] = None
    catalogue_test_id: Optional[str] = None
    pass_conditions: Optional[List[str]] = None
    fail_conditions: Optional[List[str]] = None
    setup: Optional[str] = None
    additional_context: Optional[str] = None
    profile_id: Optional[str] = None
    profile: Optional[DigitalProfile] = None
    profile_snapshot: Optional[Dict[str, Any]] = None
    probes: Optional[List[str]] = None
    steps: Optional[List[ChatStep]] = None
    samples: Optional[int] = None
    max_turns: Optional[int] = None


class CreateDigitalTestConfigRequest(DigitalTestConfigBase):
    """Body for ``POST /digital-testing/configs``.

    ``required: [name, targetRef, target, sector, mission]``.
    """

    name: str
    target_ref: str
    target: DigitalTarget
    sector: str
    mission: str


class UpdateDigitalTestConfigRequest(DigitalTestConfigBase):
    """Body for ``PATCH /digital-testing/configs/{id}`` — every field optional.

    The MERGED result is validated server-side, not the patch alone.
    """


class DigitalTestConfig(DigitalTestConfigBase):
    """A saved digital test config.

    ``required: [id, workspaceId, name, targetRef, target, sector, mission, kind,
    createdAt, updatedAt]``.
    """

    id: str
    workspace_id: str
    name: str
    target_ref: str
    target: DigitalTarget
    sector: str
    mission: str
    kind: DigitalTestKind
    user_id: Optional[str] = None
    created_at: str
    updated_at: str


class LaunchDigitalTestConfigRequest(_DigitalBase):
    """Optional overrides for ``POST /digital-testing/configs/{id}/runs``.

    ``target`` and ``target_ref`` must be overridden TOGETHER — a half-override
    is a 400.
    """

    target_ref: Optional[str] = None
    target: Optional[DigitalTarget] = None
    samples: Optional[int] = None


# ---------------------------------------------------------------------------
# Envelopes
# ---------------------------------------------------------------------------


class CreateDigitalTestRunResponse(_DigitalBase):
    message: str
    run: DigitalTestRun


class ListDigitalTestRunsResponse(_DigitalBase):
    """One page of runs, newest first.

    ``next_cursor`` is present ONLY when another page exists, and OMITTED (not
    null) on the last page.
    """

    runs: List[DigitalTestRun]
    next_cursor: Optional[str] = None


class ListDigitalTestConfigsResponse(_DigitalBase):
    """One page of saved configs, most recently updated first."""

    configs: List[DigitalTestConfig]
    next_cursor: Optional[str] = None


class DigitalComplianceAuditSummary(_DigitalBase):
    """One row of ``GET /digital-testing/compliance-audits`` (inline in the
    document; named here)."""

    target_ref: str
    last_run_at: str
    run_count: int
    catalogue_test_ids: List[str]
