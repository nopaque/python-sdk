import pytest
from nopaque._pagination import SyncPaginator, AsyncPaginator, Page


def test_page_holds_items_and_next_token():
    p = Page(items=[1, 2, 3], next_token="abc")
    assert p.items == [1, 2, 3]
    assert p.next_token == "abc"


def test_sync_paginator_follows_next_token():
    calls = []

    def fetch(params):
        calls.append(params)
        if not params.get("nextToken"):
            return {"items": [1, 2], "nextToken": "t1"}
        if params["nextToken"] == "t1":
            return {"items": [3, 4], "nextToken": "t2"}
        return {"items": [5], "nextToken": None}

    it = SyncPaginator(fetch_page=fetch, params={})
    assert list(it) == [1, 2, 3, 4, 5]
    assert len(calls) == 3


def test_sync_paginator_respects_caller_limit():
    def fetch(params):
        limit = params.get("limit")
        items = list(range(1, 21))
        if limit:
            items = items[:limit]
        return {"items": items, "nextToken": None}

    it = SyncPaginator(fetch_page=fetch, params={"limit": 5})
    assert list(it) == [1, 2, 3, 4, 5]


def test_sync_paginator_empty_result():
    def fetch(params):
        return {"items": [], "nextToken": None}

    it = SyncPaginator(fetch_page=fetch, params={})
    assert list(it) == []


def test_sync_paginator_single_page():
    def fetch(params):
        return {"items": [1, 2, 3], "nextToken": None}

    it = SyncPaginator(fetch_page=fetch, params={})
    assert list(it) == [1, 2, 3]


@pytest.mark.asyncio
async def test_async_paginator_follows_next_token():
    calls = []

    async def fetch(params):
        calls.append(params)
        if not params.get("nextToken"):
            return {"items": [1, 2], "nextToken": "t1"}
        return {"items": [3], "nextToken": None}

    it = AsyncPaginator(fetch_page=fetch, params={})
    out = [x async for x in it]
    assert out == [1, 2, 3]
