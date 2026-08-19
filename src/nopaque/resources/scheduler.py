"""Scheduler resource - /schedules endpoints."""
from __future__ import annotations

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.scheduler import Schedule, ScheduleTargetType, ScheduleType


class SchedulerResource(SyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[Schedule]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/schedules", params=p, request_options=request_options
            )

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=Schedule, items_key="schedules"
        )

    def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[Schedule]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/schedules", params=params, request_options=request_options
        )
        raw_items = raw.get("schedules", raw.get("items", []))
        items = [Schedule.model_validate(i) for i in raw_items]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, schedule_id: str, *, request_options: RequestOptions | None = None
    ) -> Schedule:
        raw = self._transport.request(
            "GET", f"/schedules/{schedule_id}", request_options=request_options
        )
        return Schedule.model_validate(raw)

    def create(
        self,
        *,
        name: str,
        schedule_type: ScheduleType,
        description: str | None = None,
        target_id: str | None = None,
        target_type: ScheduleTargetType | None = None,
        cron_expression: str | None = None,
        interval_minutes: int | None = None,
        run_at: str | None = None,
        timezone: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Schedule:
        """Create a schedule.

        ``schedule_type`` decides which companion field the API requires:
        ``cron`` -> ``cron_expression``, ``recurring`` -> ``interval_minutes``,
        ``once`` -> ``run_at`` (an ISO timestamp in the future).
        """
        body: dict = {"name": name, "scheduleType": schedule_type}
        for key, value in (
            ("description", description),
            ("targetId", target_id),
            ("targetType", target_type),
            ("cronExpression", cron_expression),
            ("intervalMinutes", interval_minutes),
            ("runAt", run_at),
            ("timezone", timezone),
        ):
            if value is not None:
                body[key] = value
        raw = self._transport.request(
            "POST", "/schedules", json=body, request_options=request_options
        )
        return Schedule.model_validate(raw)

    def update(
        self,
        schedule_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        schedule_type: ScheduleType | None = None,
        cron_expression: str | None = None,
        interval_minutes: int | None = None,
        run_at: str | None = None,
        timezone: str | None = None,
        enabled: bool | None = None,
        request_options: RequestOptions | None = None,
    ) -> Schedule:
        body: dict = {}
        for key, value in (
            ("name", name),
            ("description", description),
            ("scheduleType", schedule_type),
            ("cronExpression", cron_expression),
            ("intervalMinutes", interval_minutes),
            ("runAt", run_at),
            ("timezone", timezone),
            ("enabled", enabled),
        ):
            if value is not None:
                body[key] = value
        raw = self._transport.request(
            "PUT",
            f"/schedules/{schedule_id}",
            json=body,
            request_options=request_options,
        )
        return Schedule.model_validate(raw)

    def delete(
        self, schedule_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        self._transport.request(
            "DELETE", f"/schedules/{schedule_id}", request_options=request_options
        )

    def pause(
        self, schedule_id: str, *, request_options: RequestOptions | None = None
    ) -> Schedule:
        raw = self._transport.request(
            "POST",
            f"/schedules/{schedule_id}/pause",
            request_options=request_options,
        )
        return Schedule.model_validate(raw)

    def resume(
        self, schedule_id: str, *, request_options: RequestOptions | None = None
    ) -> Schedule:
        raw = self._transport.request(
            "POST",
            f"/schedules/{schedule_id}/resume",
            request_options=request_options,
        )
        return Schedule.model_validate(raw)


class AsyncSchedulerResource(AsyncResource):
    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[Schedule]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/schedules", params=p, request_options=request_options
            )

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=Schedule, items_key="schedules"
        )

    async def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[Schedule]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/schedules", params=params, request_options=request_options
        )
        raw_items = raw.get("schedules", raw.get("items", []))
        items = [Schedule.model_validate(i) for i in raw_items]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, schedule_id: str, *, request_options: RequestOptions | None = None
    ) -> Schedule:
        raw = await self._transport.request(
            "GET", f"/schedules/{schedule_id}", request_options=request_options
        )
        return Schedule.model_validate(raw)

    async def create(
        self,
        *,
        name: str,
        schedule_type: ScheduleType,
        description: str | None = None,
        target_id: str | None = None,
        target_type: ScheduleTargetType | None = None,
        cron_expression: str | None = None,
        interval_minutes: int | None = None,
        run_at: str | None = None,
        timezone: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Schedule:
        """Create a schedule.

        ``schedule_type`` decides which companion field the API requires:
        ``cron`` -> ``cron_expression``, ``recurring`` -> ``interval_minutes``,
        ``once`` -> ``run_at`` (an ISO timestamp in the future).
        """
        body: dict = {"name": name, "scheduleType": schedule_type}
        for key, value in (
            ("description", description),
            ("targetId", target_id),
            ("targetType", target_type),
            ("cronExpression", cron_expression),
            ("intervalMinutes", interval_minutes),
            ("runAt", run_at),
            ("timezone", timezone),
        ):
            if value is not None:
                body[key] = value
        raw = await self._transport.request(
            "POST", "/schedules", json=body, request_options=request_options
        )
        return Schedule.model_validate(raw)

    async def update(
        self,
        schedule_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        schedule_type: ScheduleType | None = None,
        cron_expression: str | None = None,
        interval_minutes: int | None = None,
        run_at: str | None = None,
        timezone: str | None = None,
        enabled: bool | None = None,
        request_options: RequestOptions | None = None,
    ) -> Schedule:
        body: dict = {}
        for key, value in (
            ("name", name),
            ("description", description),
            ("scheduleType", schedule_type),
            ("cronExpression", cron_expression),
            ("intervalMinutes", interval_minutes),
            ("runAt", run_at),
            ("timezone", timezone),
            ("enabled", enabled),
        ):
            if value is not None:
                body[key] = value
        raw = await self._transport.request(
            "PUT",
            f"/schedules/{schedule_id}",
            json=body,
            request_options=request_options,
        )
        return Schedule.model_validate(raw)

    async def delete(
        self, schedule_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        await self._transport.request(
            "DELETE", f"/schedules/{schedule_id}", request_options=request_options
        )

    async def pause(
        self, schedule_id: str, *, request_options: RequestOptions | None = None
    ) -> Schedule:
        raw = await self._transport.request(
            "POST",
            f"/schedules/{schedule_id}/pause",
            request_options=request_options,
        )
        return Schedule.model_validate(raw)

    async def resume(
        self, schedule_id: str, *, request_options: RequestOptions | None = None
    ) -> Schedule:
        raw = await self._transport.request(
            "POST",
            f"/schedules/{schedule_id}/resume",
            request_options=request_options,
        )
        return Schedule.model_validate(raw)
