"""Models for /profiles endpoints."""
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict

#: Which kind of thing a profile item points at.
ProfileItemType = Literal["voice", "data"]


def _alias(name: str) -> str:
    """snake_case field name -> camelCase wire name.

    Computed rather than listed, so a new field cannot silently serialise as
    snake_case and be ignored by the API.
    """
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


class _ProfilesBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class _ProfileItemBase(_ProfilesBase):
    id: str
    #: Legacy display label. Deprecated server-side and no longer written — for
    #: data items it is derived from the dataset item's key at read time, so it
    #: is frequently absent. Do not rely on it.
    label: Optional[str] = None
    description: Optional[str] = None


class ProfileVoiceItem(_ProfileItemBase):
    """A profile item pointing at an uploaded audio row."""

    type: Literal["voice"]
    audio_id: str


class ProfileDataItem(_ProfileItemBase):
    """A profile item pointing at an item inside a dataset."""

    type: Literal["data"]
    dataset_id: str
    item_id: str


#: Discriminated on ``type``. Branch on it before reaching for ``audio_id`` or
#: ``dataset_id``.
ProfileItem = Union[ProfileVoiceItem, ProfileDataItem]


class Profile(_ProfilesBase):
    id: str
    workspace_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    items: List[ProfileItem] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None


class ProfileParameters(_ProfilesBase):
    parameters: List[str]
