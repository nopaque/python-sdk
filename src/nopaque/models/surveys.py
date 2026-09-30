"""Models for the survey testing endpoints.

Transcribed from ``openapi/openapi.json``: ``/testing/survey-runs``,
``/testing/survey-results`` and ``/testing/survey-test-configs``.

A survey test is the inverse of a call test. Nopaque does not start the
conversation - the customer's survey platform does. Starting a test claims one of
the workspace's numbers and arms a respondent on it; the customer then sends
their survey to that number, and the respondent answers it.
"""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


def _alias(name: str) -> str:
    """snake_case field name -> camelCase wire name.

    ``from_`` maps to ``from``: the trailing underscore only exists because
    ``from`` is a Python keyword.
    """
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


class _SurveyBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


SurveyScenario = Literal[
    "happy-path", "out-of-range", "changes-mind", "abandons", "asks-question-back"
]
"""How the respondent behaves: answer properly, give an out-of-range answer, change
its mind, stop part way, or ask a question back."""

SurveyChannel = Literal["sms_chat", "phone_call"]
SurveyRunState = Literal["waiting", "in_progress", "complete", "timed_out"]
SurveyResultState = Literal["live", "ended"]
SurveyOutcome = Literal[
    "completed", "partial", "ended", "no_survey_arrived", "stopped", "start_failed"
]
SurveyEndReason = Literal["survey_over", "window_lapsed", "stopped", "start_failed"]
SurveyCaptureStatus = Literal["pending", "provisional", "final", "failed"]

SURVEY_CAPTURE_TERMINAL_STATUSES = frozenset({"final", "failed"})
"""Capture statuses after which a result's transcript will not change again."""


# ---------------------------------------------------------------------------
# Configs
# ---------------------------------------------------------------------------


class SurveyTestConfigBase(_SurveyBase):
    """Fields shared by the full config and its list item."""

    id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    sector: str
    profile_id: Optional[str] = None
    expected_turns: Optional[int] = None
    scenario: SurveyScenario
    tags: Optional[List[str]] = None
    voice_id: Optional[str] = None
    created_at: str
    updated_at: str


class SurveyTestConfigListItem(SurveyTestConfigBase):
    """A config as the list endpoint returns it: no ``mission`` or ``acceptance``."""


class SurveyTestConfig(SurveyTestConfigBase):
    """A saved survey test config: who the respondent is and how it should behave."""

    mission: str
    acceptance: str


class CreateSurveyTestConfigRequest(_SurveyBase):
    name: str
    description: Optional[str] = None
    sector: str
    mission: str
    acceptance: str
    profile_id: Optional[str] = None
    expected_turns: Optional[int] = None
    scenario: SurveyScenario
    tags: Optional[List[str]] = None
    voice_id: Optional[str] = None


class UpdateSurveyTestConfigRequest(_SurveyBase):
    name: Optional[str] = None
    description: Optional[str] = None
    sector: Optional[str] = None
    mission: Optional[str] = None
    acceptance: Optional[str] = None
    profile_id: Optional[str] = None
    expected_turns: Optional[int] = None
    scenario: Optional[SurveyScenario] = None
    tags: Optional[List[str]] = None
    voice_id: Optional[str] = None


class ListSurveyTestConfigsResponse(_SurveyBase):
    configs: List[SurveyTestConfigListItem] = []


# ---------------------------------------------------------------------------
# Runs (live tests)
# ---------------------------------------------------------------------------


class StartSurveyTestRequest(_SurveyBase):
    config_id: str
    end_user_e164: str
    window_secs: Optional[int] = None
    expected_turns: Optional[int] = None
    max_messages: Optional[int] = None


class SurveyRunStarted(_SurveyBase):
    """What ``POST /testing/survey-runs`` returns.

    ``agent_e164`` is the number to send the survey to. ``expires_at`` is epoch
    SECONDS: the survey must arrive before then.
    """

    run_id: str
    config_id: str
    agent_e164: str
    end_user_e164: str
    state: Literal["waiting"]
    started_at: str
    expires_at: int
    max_messages: int


class SurveyRun(_SurveyBase):
    """A survey test that holds a number. Gone from the list once it has ended."""

    run_id: str
    config_id: str
    agent_e164: str
    end_user_e164: str
    state: SurveyRunState
    started_at: str
    engaged_at: Optional[str] = None
    channel: Optional[SurveyChannel] = None
    expires_at: int
    live: bool
    expected_turns: Optional[int] = None
    answers_given: Optional[int] = None
    enforcement_active: Optional[bool] = None


class SurveyNumberCounts(_SurveyBase):
    total: int
    busy: int
    free: int


class SurveyRunList(_SurveyBase):
    """The workspace's live survey tests, and how many of its numbers are free."""

    runs: List[SurveyRun] = []
    numbers: SurveyNumberCounts


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


class SurveyCapture(_SurveyBase):
    """Where the transcript copy stands.

    ``final`` and ``failed`` are settled; ``pending`` and ``provisional`` will
    change. A ``failed`` capture carries ``error``.
    """

    status: SurveyCaptureStatus
    captured_at: Optional[str] = None
    error: Optional[str] = None


class SurveyTurn(_SurveyBase):
    """One message in the conversation: ``survey`` is the customer's platform."""

    at: str
    from_: Literal["survey", "respondent"]
    text: str


class SurveyResultSummary(_SurveyBase):
    """What happened in one survey test, kept after the test itself has ended."""

    run_id: str
    config_id: str
    config_name: Optional[str] = None
    scenario: Optional[SurveyScenario] = None
    profile_name: Optional[str] = None
    agent_e164: str
    end_user_e164: str
    channel: Optional[SurveyChannel] = None
    started_at: str
    expires_at: int
    expected_turns: Optional[int] = None
    answers_given: int
    engaged_at: Optional[str] = None
    ended_at: Optional[str] = None
    state: SurveyResultState
    outcome: Optional[SurveyOutcome] = None
    end_reason: Optional[SurveyEndReason] = None
    turns_truncated: bool = False
    capture: SurveyCapture


class SurveyResult(SurveyResultSummary):
    """A result with its conversation."""

    turns: List[SurveyTurn] = []


class ListSurveyResultsResponse(_SurveyBase):
    results: List[SurveyResultSummary] = []
    next_cursor: Optional[str] = None
