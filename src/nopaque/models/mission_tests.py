"""Models for /testing/mission-tests endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict

_ALIAS_MAP = {
    "phone_number": "phoneNumber",
    "workspace_id": "workspaceId",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "catalogue_version": "catalogueVersion",
    "test_type": "testType",
    "started_at": "startedAt",
    "completed_at": "completedAt",
    "config_id": "configId",
    "voice_id": "voiceId",
    "pass_reasoning": "passReasoning",
    "pass_evidence": "passEvidence",
    "error_message": "errorMessage",
    "run_id": "runId",
    "schema_version": "schemaVersion",
    "default_acceptance": "defaultAcceptance",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


MissionTestKind = Literal["freeform", "compliance"]

#: The language a mission test **call** is held in. These are the languages
#: Telnyx ``deepgram/flux`` accepts on the AI Assistant: one language, or
#: ``multi`` (Flux-multi), which code-switches across the other ten. Absent
#: means English -- that is how every mission test behaved before the field
#: existed, so omitting it is always safe.
#:
#: .. warning::
#:    This is **not** the transcription language that standard tests and
#:    mapping use (``MappingJobConfig.language``, ``en-GB`` and friends). The
#:    two sets are genuinely different and the difference bites: bare ``en``
#:    is **valid here** but is rejected with a 400 as a transcription
#:    language, which wants a region -- ``en-GB``. Bare ``en`` is the only
#:    code in this set with no transcription counterpart; the other ten all
#:    appear in both, which is what makes the mistake easy to make.
#:
#: Mirrors the ``CallLanguage`` schema in the OpenAPI document.
CallLanguage = Literal[
    "en",
    "multi",
    "es",
    "fr",
    "de",
    "it",
    "pt",
    "nl",
    "hi",
    "ru",
    "ja",
]
# "pending" is what the api sends (openapi MissionTestRun.status); "queued" is
# kept so nothing that validated before stops validating.
MissionTestStatus = Literal["pending", "queued", "running", "completed", "failed", "cancelled"]


class _MissionTestBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class MissionTestProfile(_MissionTestBase):
    phone_number: str
    name: Optional[str] = None


class CreateMissionTestRequest(_MissionTestBase):
    sector: str
    mission: str
    acceptance: str
    profile: MissionTestProfile
    #: Optional call language. Omit for English, which is how every mission
    #: test has behaved to date. Use ``multi`` when the IVR may start in
    #: English and switch.
    language: Optional[CallLanguage] = None


class MissionTestRun(_MissionTestBase):
    """A mission or compliance run, as GET /testing/mission-tests returns it.

    Required fields match the openapi `MissionTestRun` schema (id, workspaceId,
    testType, status, startedAt). Everything else is optional: runs launched
    from a saved config carry no `kind`, `createdAt` or `updatedAt`, and
    `profile` is the profile ID string, not an object. When those were
    required, listing a real workspace raised a ValidationError.
    """

    id: str
    workspace_id: str
    test_type: Optional[str] = None
    status: MissionTestStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    kind: Optional[MissionTestKind] = None
    sector: Optional[str] = None
    mission: Optional[str] = None
    acceptance: Optional[str] = None
    # A profile ID string from the api; the object form is accepted for
    # callers that built runs by hand against the old model.
    profile: Optional[Union[str, MissionTestProfile]] = None
    phone_number: Optional[str] = None
    config_id: Optional[str] = None
    voice_id: Optional[str] = None
    passed: Optional[bool] = None
    pass_reasoning: Optional[str] = None
    pass_evidence: Optional[str] = None
    verdict: Optional[Literal["pass", "fail"]] = None
    error_message: Optional[str] = None
    #: The call language the run was dispatched with, one of the
    #: :data:`CallLanguage` codes. None means English -- every run from before
    #: the field existed, and every run that did not set it.
    #:
    #: Typed ``str``, not that Literal, because this is a response field:
    #: reading a run must never raise over an unrecognised code. The Literal
    #: guards the write path instead (``mission_tests.create(language=...)``).
    language: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MissionDefaultsMission(_MissionTestBase):
    """A ready-made mission: what to attempt, and when it counts as done."""

    id: str
    label: Optional[str] = None
    default_acceptance: Optional[str] = None


class MissionDefaultsSector(_MissionTestBase):
    id: str
    label: Optional[str] = None
    missions: List[MissionDefaultsMission] = []


class MissionTestDefaults(_MissionTestBase):
    """The sector catalogue from GET /testing/mission-tests/defaults.

    Each sector lists ready-made missions with a default acceptance criterion,
    for use as ``sector``, ``mission`` and ``acceptance`` on
    ``mission_tests.create()``. The API passes through the catalogue the
    mission-tester service publishes, so keys may be added without notice.
    """

    schema_version: Optional[int] = None
    sectors: List[MissionDefaultsSector] = []


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


class TestRunAnalysis(BaseModel):
    """One post-call analysis of a test run, as stored.

    ``type`` is ``judge_mission``, ``transcribe_words``, ``compute_latencies``
    or ``detect_silences``; ``status`` is ``pending``, ``completed`` or
    ``failed``. The shape of ``data`` depends on ``type``.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_camel,
    )

    run_id: str
    type: str
    status: str
    version: Optional[str] = None
    produced_at: Optional[str] = None
    workspace_id: Optional[str] = None
    phone_number: Optional[str] = None
    range_key: Optional[str] = None
    status_produced_at: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    model: Optional[str] = None
    raw_response: Optional[Any] = None


class MissionTestAnalysesByType(BaseModel):
    """The newest analysis of each type. A type that has not run yet is None."""

    model_config = ConfigDict(extra="allow")

    judge_mission: Optional[TestRunAnalysis] = None
    transcribe_words: Optional[TestRunAnalysis] = None
    compute_latencies: Optional[TestRunAnalysis] = None
    detect_silences: Optional[TestRunAnalysis] = None


class MissionTestAnalyses(_MissionTestBase):
    """Response for ``GET /testing/mission-tests/{id}/analyses``."""

    run_id: str
    analyses: MissionTestAnalysesByType
