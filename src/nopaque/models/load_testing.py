"""Models for /testing/load-tests endpoints."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


_ALIAS_MAP = {
    "config_id": "configId",
    "load_test_id": "loadTestId",
    "run_id": "runId",
    "total_calls": "totalCalls",
    "completed_calls": "completedCalls",
    "pass_rate": "passRate",
    "estimated_minutes": "estimatedMinutes",
    "estimated_cost": "estimatedCost",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "started_at": "startedAt",
    "completed_at": "completedAt",
    "aborted_at": "abortedAt",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


class _LoadTestingBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class LoadTest(_LoadTestingBase):
    id: str
    name: str
    config_id: Optional[str] = None
    concurrency: Optional[int] = None
    total_calls: Optional[int] = None
    status: Optional[str] = None
    run_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    aborted_at: Optional[str] = None


class LoadTestEstimate(_LoadTestingBase):
    estimated_minutes: Optional[float] = None
    estimated_cost: Optional[str] = None
    concurrency: Optional[int] = None
    total_calls: Optional[int] = None


class LoadTestProgress(_LoadTestingBase):
    completed_calls: Optional[int] = None
    total_calls: Optional[int] = None
    pass_rate: Optional[float] = None


class LoadTestStatus(_LoadTestingBase):
    id: Optional[str] = None
    status: str
    progress: Optional[LoadTestProgress] = None


class LoadTestRun(_LoadTestingBase):
    run_id: Optional[str] = None
    id: Optional[str] = None
    load_test_id: Optional[str] = None
    status: str
    pass_rate: Optional[float] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
