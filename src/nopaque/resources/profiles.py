"""Profiles resource - /profiles endpoints."""
from __future__ import annotations

import builtins

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.profiles import Profile, ProfileItem, ProfileParameters


class ProfilesResource(SyncResource):
    """Synchronous /profiles endpoints."""

    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[Profile]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/profiles", params=p, request_options=request_options
            )

        return SyncPaginator(
            fetch_page=fetch, params=params, model_cls=Profile, items_key="profiles"
        )

    def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[Profile]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/profiles", params=params, request_options=request_options
        )
        raw_items = raw.get("profiles", raw.get("items", []))
        items = [Profile.model_validate(i) for i in raw_items]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, profile_id: str, *, request_options: RequestOptions | None = None
    ) -> Profile:
        raw = self._transport.request(
            "GET", f"/profiles/{profile_id}", request_options=request_options
        )
        return Profile.model_validate(raw)

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Profile:
        body: dict = {"name": name}
        if description is not None:
            body["description"] = description
        raw = self._transport.request(
            "POST", "/profiles", json=body, request_options=request_options
        )
        return Profile.model_validate(raw)

    def update(
        self,
        profile_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Profile:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        raw = self._transport.request(
            "PUT", f"/profiles/{profile_id}", json=body, request_options=request_options
        )
        return Profile.model_validate(raw)

    def delete(
        self, profile_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        self._transport.request(
            "DELETE", f"/profiles/{profile_id}", request_options=request_options
        )

    def add_item(
        self,
        profile_id: str,
        *,
        label: str,
        value: str,
        request_options: RequestOptions | None = None,
    ) -> ProfileItem:
        raw = self._transport.request(
            "POST",
            f"/profiles/{profile_id}/items",
            json={"label": label, "value": value},
            request_options=request_options,
        )
        return ProfileItem.model_validate(raw)

    def update_item(
        self,
        profile_id: str,
        item_id: str,
        *,
        label: str | None = None,
        value: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> ProfileItem:
        body: dict = {}
        if label is not None:
            body["label"] = label
        if value is not None:
            body["value"] = value
        raw = self._transport.request(
            "PUT",
            f"/profiles/{profile_id}/items/{item_id}",
            json=body,
            request_options=request_options,
        )
        return ProfileItem.model_validate(raw)

    def delete_item(
        self,
        profile_id: str,
        item_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> None:
        self._transport.request(
            "DELETE",
            f"/profiles/{profile_id}/items/{item_id}",
            request_options=request_options,
        )

    def list_parameters(
        self, *, request_options: RequestOptions | None = None
    ) -> ProfileParameters:
        raw = self._transport.request(
            "GET", "/profiles/parameters", request_options=request_options
        )
        return ProfileParameters.model_validate(raw)

    def find_by_parameters(
        self,
        *,
        labels: builtins.list[str],
        request_options: RequestOptions | None = None,
    ) -> builtins.list[Profile]:
        raw = self._transport.request(
            "GET",
            "/profiles/by-parameters",
            params={"labels": ",".join(labels)},
            request_options=request_options,
        )
        return [
            Profile.model_validate(i)
            for i in raw.get("profiles", raw.get("items", []))
        ]


class AsyncProfilesResource(AsyncResource):
    """Asynchronous /profiles endpoints."""

    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[Profile]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/profiles", params=p, request_options=request_options
            )

        return AsyncPaginator(
            fetch_page=fetch, params=params, model_cls=Profile, items_key="profiles"
        )

    async def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[Profile]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/profiles", params=params, request_options=request_options
        )
        raw_items = raw.get("profiles", raw.get("items", []))
        items = [Profile.model_validate(i) for i in raw_items]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, profile_id: str, *, request_options: RequestOptions | None = None
    ) -> Profile:
        raw = await self._transport.request(
            "GET", f"/profiles/{profile_id}", request_options=request_options
        )
        return Profile.model_validate(raw)

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Profile:
        body: dict = {"name": name}
        if description is not None:
            body["description"] = description
        raw = await self._transport.request(
            "POST", "/profiles", json=body, request_options=request_options
        )
        return Profile.model_validate(raw)

    async def update(
        self,
        profile_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Profile:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        raw = await self._transport.request(
            "PUT", f"/profiles/{profile_id}", json=body, request_options=request_options
        )
        return Profile.model_validate(raw)

    async def delete(
        self, profile_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        await self._transport.request(
            "DELETE", f"/profiles/{profile_id}", request_options=request_options
        )

    async def add_item(
        self,
        profile_id: str,
        *,
        label: str,
        value: str,
        request_options: RequestOptions | None = None,
    ) -> ProfileItem:
        raw = await self._transport.request(
            "POST",
            f"/profiles/{profile_id}/items",
            json={"label": label, "value": value},
            request_options=request_options,
        )
        return ProfileItem.model_validate(raw)

    async def update_item(
        self,
        profile_id: str,
        item_id: str,
        *,
        label: str | None = None,
        value: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> ProfileItem:
        body: dict = {}
        if label is not None:
            body["label"] = label
        if value is not None:
            body["value"] = value
        raw = await self._transport.request(
            "PUT",
            f"/profiles/{profile_id}/items/{item_id}",
            json=body,
            request_options=request_options,
        )
        return ProfileItem.model_validate(raw)

    async def delete_item(
        self,
        profile_id: str,
        item_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> None:
        await self._transport.request(
            "DELETE",
            f"/profiles/{profile_id}/items/{item_id}",
            request_options=request_options,
        )

    async def list_parameters(
        self, *, request_options: RequestOptions | None = None
    ) -> ProfileParameters:
        raw = await self._transport.request(
            "GET", "/profiles/parameters", request_options=request_options
        )
        return ProfileParameters.model_validate(raw)

    async def find_by_parameters(
        self,
        *,
        labels: builtins.list[str],
        request_options: RequestOptions | None = None,
    ) -> builtins.list[Profile]:
        raw = await self._transport.request(
            "GET",
            "/profiles/by-parameters",
            params={"labels": ",".join(labels)},
            request_options=request_options,
        )
        return [
            Profile.model_validate(i)
            for i in raw.get("profiles", raw.get("items", []))
        ]
