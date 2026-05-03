"""Models for /mapping endpoints."""
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict

_ALIAS_MAP = {
    "workspace_id": "workspaceId",
    "user_id": "userId",
    "phone_number": "phoneNumber",
    "mapping_mode": "mappingMode",
    "profile_id": "profileId",
    "voice_profile_id": "voiceProfileId",
    "data_profile_id": "dataProfileId",
    "current_run_id": "currentRunId",
    "limit_reason": "limitReason",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "started_at": "startedAt",
    "completed_at": "completedAt",
    "cancelled_at": "cancelledAt",
    "max_depth": "maxDepth",
    "max_calls": "maxCalls",
    "max_duration_minutes": "maxDurationMinutes",
    "max_concurrency": "maxConcurrency",
    "retry_config": "retryConfig",
    "total_calls": "totalCalls",
    "completed_calls": "completedCalls",
    "failed_calls": "failedCalls",
    "loops_detected": "loopsDetected",
    "retried_calls": "retriedCalls",
    "in_flight_count": "inFlightCount",
    "pending_paths": "pendingPaths",
    "parent_step_id": "parentStepId",
    "path_string": "pathString",
    "transcript_hash": "transcriptHash",
    "retry_count": "retryCount",
    "step_id": "stepId",
    "audio_url": "audioUrl",
    "audio_size_bytes": "audioSizeBytes",
    "is_terminal": "isTerminal",
    "dtmf_options": "dtmfOptions",
    "dtmf_option": "dtmfOption",
    "job_id": "jobId",
    "run_id": "runId",
    "repeat_behavior": "repeatBehavior",
    "remap_path": "remapPath",
}


def _alias(name: str) -> str:
    return _ALIAS_MAP.get(name, name)


JobStatus = Literal[
    "idle",
    "created",
    "queued",
    "running",
    "completed",
    "failed",
    "limited",
    "cancelled",
]
StepStatus = Literal[
    "pending", "running", "completed", "failed", "retrying", "skipped"
]
MappingMode = Literal["dtmf", "dtmf-audio", "full-audio"]


class _MappingBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class MappingJobStats(_MappingBase):
    total_calls: int = 0
    completed_calls: int = 0
    failed_calls: int = 0
    loops_detected: int = 0
    retried_calls: int = 0


class RetryConfig(_MappingBase):
    enabled: bool = False
    max_retries: int = 3


class MappingJobConfig(_MappingBase):
    max_depth: Optional[int] = None
    max_calls: Optional[int] = None
    max_duration_minutes: Optional[int] = None
    max_concurrency: Optional[int] = None
    language: Optional[str] = None
    voice_profile_id: Optional[str] = None
    data_profile_id: Optional[str] = None
    retry_config: Optional[RetryConfig] = None
    mapping_mode: Optional[MappingMode] = None


class MappingJob(_MappingBase):
    id: str
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    name: str
    phone_number: Optional[str] = None
    profile_id: Optional[str] = None
    status: str
    run_id: Optional[str] = None
    config: Optional[MappingJobConfig] = None
    stats: Optional[MappingJobStats] = None
    in_flight_count: Optional[int] = None
    pending_paths: Optional[List[str]] = None
    current_run_id: Optional[str] = None
    limit_reason: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cancelled_at: Optional[str] = None


class DTMFOption(_MappingBase):
    digit: str
    label: Optional[str] = None


class StepResult(_MappingBase):
    transcript: str = ""
    dtmf_options: List[DTMFOption] = []
    is_terminal: bool = False
    audio_url: Optional[str] = None
    audio_size_bytes: Optional[int] = None
    duration: Optional[float] = None


class MappingStep(_MappingBase):
    id: Optional[str] = None
    step_id: Optional[str] = None
    job_id: Optional[str] = None
    run_id: Optional[str] = None
    workspace_id: Optional[str] = None
    parent_step_id: Optional[str] = None
    depth: int = 0
    path: List[str] = []
    path_string: Optional[str] = None
    status: str
    retry_count: int = 0
    result: Optional[StepResult] = None
    transcript_hash: Optional[str] = None
    transcript: Optional[str] = None
    dtmf_option: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class TreeNode(_MappingBase):
    step_id: Optional[str] = None
    path: Optional[str] = None
    dtmf_option: Optional[str] = None
    digit: Optional[str] = None
    label: Optional[str] = None
    depth: Optional[int] = None
    status: Optional[str] = None
    transcript: Optional[str] = None
    is_terminal: bool = False
    children: List["TreeNode"] = []
    duration: Optional[float] = None
    audio_url: Optional[str] = None


TreeNode.model_rebuild()


class MappingTree(_MappingBase):
    job_id: Optional[str] = None
    run_id: Optional[str] = None
    status: Optional[str] = None
    stats: Optional[MappingJobStats] = None
    tree: Optional[TreeNode] = None
    root: Optional[TreeNode] = None
    message: Optional[str] = None


class MappingPath(_MappingBase):
    """A single path in a mapping job's path table."""

    job_id: Optional[str] = None
    path: str
    status: Optional[str] = None
    transcript: Optional[str] = None
    is_terminal: Optional[bool] = None
    repeat_behavior: Optional[str] = None


class MappingRun(_MappingBase):
    """A single run of a mapping job."""

    id: Optional[str] = None
    run_id: Optional[str] = None
    job_id: Optional[str] = None
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    stats: Optional[MappingJobStats] = None
