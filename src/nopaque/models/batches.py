"""Models for /testing/batches endpoints."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


_ALIAS_MAP = {
    "config_id": "configId",
    "dataset_id": "datasetId",
    "batch_id": "batchId",
    "run_id": "runId",
    "pass_rate": "passRate",
    "total_numbers": "totalNumbers",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "started_at": "startedAt",
    "completed_at": "completedAt",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


class _BatchesBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class Batch(_BatchesBase):
    id: str
    name: str
    config_id: Optional[str] = None
    dataset_id: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BatchRun(_BatchesBase):
    run_id: Optional[str] = None
    id: Optional[str] = None
    batch_id: Optional[str] = None
    status: str
    total_numbers: Optional[int] = None
    passed: Optional[int] = None
    failed: Optional[int] = None
    pass_rate: Optional[float] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
