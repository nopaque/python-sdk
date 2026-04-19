"""Sync + async pagination helpers.

List endpoints respond with {items: [...], nextToken?: str}. Paginators
transparently follow nextToken. A caller-supplied `limit` caps total items;
a caller-supplied `nextToken` in params is used as the starting page.
"""
from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Iterator
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Generic,
    TypeVar,
)

T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    """A single page of list results."""

    items: list[T]
    next_token: str | None


class SyncPaginator(Generic[T]):
    """Iterable that fetches pages on demand and yields individual items."""

    def __init__(
        self,
        *,
        fetch_page: Callable[[dict], dict],
        params: dict,
        model_cls: type | None = None,
    ) -> None:
        self._fetch_page = fetch_page
        self._params = dict(params)
        self._model_cls = model_cls
        self._requested_limit: int | None = params.get("limit")

    def __iter__(self) -> Iterator[T]:
        yielded = 0
        params = dict(self._params)
        while True:
            result = self._fetch_page(params)
            items = result.get("items", [])
            for raw in items:
                item: Any
                if self._model_cls:
                    item = self._model_cls.model_validate(raw)  # type: ignore[attr-defined]
                else:
                    item = raw
                yield item
                yielded += 1
                if self._requested_limit and yielded >= self._requested_limit:
                    return
            next_token = result.get("nextToken")
            if not next_token:
                return
            params["nextToken"] = next_token


class AsyncPaginator(Generic[T]):
    """Async iterable that fetches pages on demand and yields individual items."""

    def __init__(
        self,
        *,
        fetch_page: Callable[[dict], Awaitable[dict]],
        params: dict,
        model_cls: type | None = None,
    ) -> None:
        self._fetch_page = fetch_page
        self._params = dict(params)
        self._model_cls = model_cls
        self._requested_limit: int | None = params.get("limit")

    async def __aiter__(self) -> AsyncIterator[T]:
        yielded = 0
        params = dict(self._params)
        while True:
            result = await self._fetch_page(params)
            items = result.get("items", [])
            for raw in items:
                item: Any
                if self._model_cls:
                    item = self._model_cls.model_validate(raw)  # type: ignore[attr-defined]
                else:
                    item = raw
                yield item
                yielded += 1
                if self._requested_limit and yielded >= self._requested_limit:
                    return
            next_token = result.get("nextToken")
            if not next_token:
                return
            params["nextToken"] = next_token
