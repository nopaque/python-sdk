"""Scheduler resource - /schedules endpoints."""
from __future__ import annotations

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.scheduler import Schedule


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
        config_id: str,
        cron_expression: str,
        timezone: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Schedule:
        body: dict = {
            "name": name,
            "configId": config_id,
            "cronExpression": cron_expression,
        }
        if timezone is not None:
            body["timezone"] = timezone
        raw = self._transport.request(
            "POST", "/schedules", json=body, request_options=request_options
        )
        return Schedule.model_validate(raw)

    def update(
        self,
        schedule_id: str,
        *,
        name: str | None = None,
        cron_expression: str | None = None,
        timezone: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Schedule:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if cron_expression is not None:
            body["cronExpression"] = cron_expression
        if timezone is not None:
            body["timezone"] = timezone
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
        config_id: str,
        cron_expression: str,
        timezone: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Schedule:
        body: dict = {
            "name": name,
            "configId": config_id,
            "cronExpression": cron_expression,
        }
        if timezone is not None:
            body["timezone"] = timezone
        raw = await self._transport.request(
            "POST", "/schedules", json=body, request_options=request_options
        )
        return Schedule.model_validate(raw)

    async def update(
        self,
        schedule_id: str,
        *,
        name: str | None = None,
        cron_expression: str | None = None,
        timezone: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Schedule:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if cron_expression is not None:
            body["cronExpression"] = cron_expression
        if timezone is not None:
            body["timezone"] = timezone
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
