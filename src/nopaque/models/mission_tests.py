"""Models for /testing/mission-tests endpoints."""
from __future__ import annotations

from typing import Literal, Optional, Union

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
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


MissionTestKind = Literal["freeform", "compliance"]
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
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MissionTestDefaults(_MissionTestBase):
    sector: str
    mission: str
    acceptance: str
    catalogue_version: str
