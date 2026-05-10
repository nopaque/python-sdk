"""Models for /testing/mission-tests endpoints."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

_ALIAS_MAP = {
    "phone_number": "phoneNumber",
    "workspace_id": "workspaceId",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "catalogue_version": "catalogueVersion",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


MissionTestKind = Literal["freeform", "compliance"]
MissionTestStatus = Literal["queued", "running", "completed", "failed", "cancelled"]


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
    id: str
    workspace_id: str
    kind: MissionTestKind
    sector: str
    mission: str
    acceptance: str
    profile: MissionTestProfile
    status: MissionTestStatus
    verdict: Optional[Literal["pass", "fail"]] = None
    created_at: str
    updated_at: str


class MissionTestDefaults(_MissionTestBase):
    sector: str
    mission: str
    acceptance: str
    catalogue_version: str
