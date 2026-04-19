"""Datasets resource - /datasets endpoints."""
from __future__ import annotations

from typing import Optional

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.datasets import Dataset, ResolvedDataset


class DatasetsResource(SyncResource):
    def list(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> SyncPaginator[Dataset]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/datasets", params=p, request_options=request_options
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=Dataset)

    def list_page(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Page[Dataset]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/datasets", params=params, request_options=request_options
        )
        items = [Dataset.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, dataset_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> Dataset:
        raw = self._transport.request(
            "GET", f"/datasets/{dataset_id}", request_options=request_options
        )
        return Dataset.model_validate(raw)

    def create(
        self,
        *,
        name: str,
        description: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Dataset:
        body: dict = {"name": name}
        if description is not None:
            body["description"] = description
        raw = self._transport.request(
            "POST", "/datasets", json=body, request_options=request_options
        )
        return Dataset.model_validate(raw)

    def update(
        self,
        dataset_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Dataset:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        raw = self._transport.request(
            "PUT",
            f"/datasets/{dataset_id}",
            json=body,
            request_options=request_options,
        )
        return Dataset.model_validate(raw)

    def delete(
        self, dataset_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> None:
        self._transport.request(
            "DELETE", f"/datasets/{dataset_id}", request_options=request_options
        )

    def resolve(
        self, dataset_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> ResolvedDataset:
        raw = self._transport.request(
            "GET",
            f"/datasets/{dataset_id}/resolve",
            request_options=request_options,
        )
        return ResolvedDataset.model_validate(raw)


class AsyncDatasetsResource(AsyncResource):
    def list(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> AsyncPaginator[Dataset]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/datasets", params=p, request_options=request_options
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=Dataset)

    async def list_page(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Page[Dataset]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/datasets", params=params, request_options=request_options
        )
        items = [Dataset.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, dataset_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> Dataset:
        raw = await self._transport.request(
            "GET", f"/datasets/{dataset_id}", request_options=request_options
        )
        return Dataset.model_validate(raw)

    async def create(
        self,
        *,
        name: str,
        description: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Dataset:
        body: dict = {"name": name}
        if description is not None:
            body["description"] = description
        raw = await self._transport.request(
            "POST", "/datasets", json=body, request_options=request_options
        )
        return Dataset.model_validate(raw)

    async def update(
        self,
        dataset_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Dataset:
        body: dict = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        raw = await self._transport.request(
            "PUT",
            f"/datasets/{dataset_id}",
            json=body,
            request_options=request_options,
        )
        return Dataset.model_validate(raw)

    async def delete(
        self, dataset_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> None:
        await self._transport.request(
            "DELETE", f"/datasets/{dataset_id}", request_options=request_options
        )

    async def resolve(
        self, dataset_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> ResolvedDataset:
        raw = await self._transport.request(
            "GET",
            f"/datasets/{dataset_id}/resolve",
            request_options=request_options,
        )
        return ResolvedDataset.model_validate(raw)
