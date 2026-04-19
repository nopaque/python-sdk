"""Models for /schedules endpoints."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


_ALIAS_MAP = {
    "config_id": "configId",
    "cron_expression": "cronExpression",
    "next_run_at": "nextRunAt",
    "last_run_at": "lastRunAt",
    "paused_at": "pausedAt",
    "resumed_at": "resumedAt",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


class _SchedulerBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class Schedule(_SchedulerBase):
    id: str
    name: Optional[str] = None
    config_id: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    status: Optional[str] = None
    next_run_at: Optional[str] = None
    last_run_at: Optional[str] = None
    paused_at: Optional[str] = None
    resumed_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
