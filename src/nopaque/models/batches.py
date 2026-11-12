"""Models for /testing/batches endpoints."""
from typing import Any, Dict, List, Literal, Optional

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
    "test_run_ids": "testRunIds",
    "triggered_by": "triggeredBy",
    "parent_batch_run_id": "parentBatchRunId",
    "workspace_id": "workspaceId",
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
    workspace_id: Optional[str] = None
    #: Test run IDs created by this batch run.
    test_run_ids: Optional[List[str]] = None
    #: Roll-up counters (``total``, ``pending``, ``running``, ``passed``,
    #: ``failed``, ``error``).
    summary: Optional[Dict[str, Any]] = None
    #: ``manual``, ``schedule`` or ``rerun``.
    triggered_by: Optional[str] = None
    #: Set on a run created by ``batches.rerun()``: the run it re-ran.
    parent_batch_run_id: Optional[str] = None


class BatchMember(BaseModel):
    """One member of a batch: ``param`` is a step-based test config,
    ``mission`` a mission test config."""

    model_config = ConfigDict(extra="allow", populate_by_name=True, alias_generator=_alias)

    type: Literal["param", "mission"]
    config_id: str
