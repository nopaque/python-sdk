"""Models for /testing/mission-test-configs endpoints."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict

_ALIAS_MAP = {
    "profile_id": "profileId",
    "workspace_id": "workspaceId",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


class _MissionTestConfigBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class CreateMissionTestConfigRequest(_MissionTestConfigBase):
    name: str
    sector: str
    mission: str
    acceptance: str
    profile_id: str


class MissionTestConfig(_MissionTestConfigBase):
    id: str
    workspace_id: Optional[str] = None
    name: str
    sector: str
    mission: str
    acceptance: str
    profile_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
