"""Models for /profiles endpoints."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

_ALIAS_MAP = {
    "profile_id": "profileId",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "matched_labels": "matchedLabels",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


class _ProfilesBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class ProfileItem(_ProfilesBase):
    id: str
    profile_id: Optional[str] = None
    label: str
    value: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Profile(_ProfilesBase):
    id: str
    name: str
    description: Optional[str] = None
    items: List[ProfileItem] = []
    matched_labels: Optional[List[str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProfileParameters(_ProfilesBase):
    parameters: List[str]
