"""Models for /testing endpoints."""
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict

_ALIAS_MAP = {
    "phone_number": "phoneNumber",
    "config_id": "configId",
    "test_config_id": "testConfigId",
    "job_id": "jobId",
    "workspace_id": "workspaceId",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "started_at": "startedAt",
    "completed_at": "completedAt",
    "launch_deadline": "launchDeadline",
    "total_steps": "totalSteps",
    "passed_steps": "passedSteps",
    "failed_steps": "failedSteps",
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
    """A single execution of a test.

    The primary identifier is `id` (matches what the server sends in the
    entity). Pass this to `wait_for_run()` and `get()`.
    """

    id: str
    job_id: Optional[str] = None
    test_config_id: Optional[str] = None
    workspace_id: Optional[str] = None
    status: Optional[str] = None
    result: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    launch_deadline: Optional[str] = None
    total_steps: Optional[int] = None
    passed_steps: Optional[int] = None
    failed_steps: Optional[int] = None
