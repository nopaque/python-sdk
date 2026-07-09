"""Models for /testing/mission-test-configs endpoints."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict

_ALIAS_MAP = {
    "profile_id": "profileId",
    "workspace_id": "workspaceId",
    "phone_number": "phoneNumber",
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
    phone_number: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class MissionTestConfig(_MissionTestConfigBase):
    id: str
    workspace_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    phone_number: Optional[str] = None
    sector: str
    mission: str
    acceptance: str
    profile_id: str
    tags: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MissionTestConfigListItem(_MissionTestConfigBase):
    """Slim projection returned by ``GET /testing/mission-test-configs`` (list).

    Drops the long-text ``mission`` and ``acceptance`` fields — call
    ``mission_test_configs.get(id)`` for the full row.
    """

    id: str
    workspace_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    phone_number: Optional[str] = None
    sector: Optional[str] = None
    profile_id: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
