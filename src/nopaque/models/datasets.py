"""Models for /datasets endpoints."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


_ALIAS_MAP = {
    "item_count": "itemCount",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "dataset_id": "datasetId",
    "resolved_entries": "resolvedEntries",
    "phone_number": "phoneNumber",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


class _DatasetsBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class Dataset(_DatasetsBase):
    id: str
    name: str
    description: Optional[str] = None
    item_count: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ResolvedEntry(_DatasetsBase):
    phone_number: Optional[str] = None
    name: Optional[str] = None


class ResolvedDataset(_DatasetsBase):
    dataset_id: str
    resolved_entries: List[ResolvedEntry] = []
