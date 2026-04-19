"""Models for /testing endpoints."""
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict

_ALIAS_MAP = {
    "phone_number": "phoneNumber",
    "config_id": "configId",
    "job_id": "jobId",
    "run_id": "runId",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "started_at": "startedAt",
    "completed_at": "completedAt",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


class _TestingBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class TestConfig(_TestingBase):
    id: str
    name: str
    phone_number: Optional[str] = None
    steps: List[Any] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TestJob(_TestingBase):
    id: str
    config_id: Optional[str] = None
    name: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class TestRun(_TestingBase):
    run_id: Optional[str] = None
    id: Optional[str] = None
    job_id: Optional[str] = None
    status: str
    result: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
