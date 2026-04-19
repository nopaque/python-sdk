"""Models for /testing/sweeps endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


_ALIAS_MAP = {
    "config_id": "configId",
    "sweep_id": "sweepId",
    "run_id": "runId",
    "pass_rate": "passRate",
    "total_combinations": "totalCombinations",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "started_at": "startedAt",
    "completed_at": "completedAt",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


class _SweepsBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class Sweep(_SweepsBase):
    id: str
    name: str
    config_id: Optional[str] = None
    parameters: Optional[Dict[str, List[str]]] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SweepRun(_SweepsBase):
    run_id: Optional[str] = None
    id: Optional[str] = None
    sweep_id: Optional[str] = None
    status: str
    total_combinations: Optional[int] = None
    passed: Optional[int] = None
    failed: Optional[int] = None
    pass_rate: Optional[float] = None
    results: Optional[List[Any]] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
