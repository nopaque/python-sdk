"""Models for /testing/sweeps endpoints."""
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
    "test_run_ids": "testRunIds",
    "test_runs": "testRuns",
    "test_config_id": "testConfigId",
    "profile_id": "profileId",
    "triggered_by": "triggeredBy",
    "schedule_id": "scheduleId",
    "workspace_id": "workspaceId",
    "created_by": "createdBy",
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


class SweepRunSummary(_SweepsBase):
    """Test-run counts for a sweep run, recomputed on every read."""

    total: int = 0
    pending: int = 0
    running: int = 0
    passed: int = 0
    failed: int = 0
    error: int = 0


class SweepRunTestRun(_SweepsBase):
    """One test run in a sweep run (one per profile)."""

    id: str
    test_config_id: Optional[str] = None
    profile_id: Optional[str] = None
    status: Optional[str] = None
    #: ``"PASS"``, ``"FAIL"`` or ``"ERROR"`` once the run has finished.
    outcome: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class SweepRun(_SweepsBase):
    """A sweep run. ``status`` is ``pending``, ``running``, ``completed``,
    ``failed`` or ``partial`` (some passed, some did not).

    ``summary`` and ``test_run_ids`` are on every sweep run; ``test_runs`` is
    only on ``get_run()``.
    """

    run_id: Optional[str] = None
    id: Optional[str] = None
    sweep_id: Optional[str] = None
    workspace_id: Optional[str] = None
    status: str
    summary: Optional[SweepRunSummary] = None
    test_run_ids: Optional[List[str]] = None
    test_runs: Optional[List[SweepRunTestRun]] = None
    triggered_by: Optional[str] = None
    schedule_id: Optional[str] = None
    created_by: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    #: Never sent by the API; always ``None``. Use ``summary``.
    total_combinations: Optional[int] = None
    #: Never sent by the API; always ``None``. Use ``summary.passed``.
    passed: Optional[int] = None
    #: Never sent by the API; always ``None``. Use ``summary.failed``.
    failed: Optional[int] = None
    #: Never sent by the API; always ``None``.
    pass_rate: Optional[float] = None
    #: Never sent by the API; always ``None``. Use ``test_runs``.
    results: Optional[List[Any]] = None
