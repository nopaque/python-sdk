"""Models for /schedules endpoints."""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

#: Which firing strategy a schedule uses. Required on create — each variant
#: requires a different companion field: ``cron`` needs ``cron_expression``,
#: ``recurring`` needs ``interval_minutes``, ``once`` needs a future ``run_at``.
ScheduleType = Literal["once", "recurring", "cron"]

#: What the schedule fires against. Optional — a schedule with no target is a
#: reusable template.
ScheduleTargetType = Literal["test", "map", "batch"]


def _alias(name: str) -> str:
    """snake_case field name -> camelCase wire name.

    Computed rather than listed, so a new field cannot silently serialise as
    snake_case and be ignored by the API.
    """
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


class _SchedulerBase(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_alias,
    )


class Schedule(_SchedulerBase):
    id: str
    workspace_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    target_id: Optional[str] = None
    target_type: Optional[ScheduleTargetType] = None

    schedule_type: Optional[ScheduleType] = None
    cron_expression: Optional[str] = None
    interval_minutes: Optional[int] = None
    run_at: Optional[str] = None
    timezone: Optional[str] = None

    #: Wire value is the string ``"true"`` / ``"false"``, not a bool — it backs
    #: a GSI key. Pause and resume flip this.
    enabled: Optional[str] = None
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    run_count: Optional[int] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
