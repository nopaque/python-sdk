"""Tests for the digital test configs resource."""
import json

from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque

BASE = "https://api.nopaque.co.uk"


def client():
    return Nopaque(api_key="k", max_retries=0)


def cfg_json(**over):
    """Shaped from the OpenAPI DigitalTestConfig schema."""
    doc = {
        "id": "c1",
        "workspaceId": "w1",
        "name": "Billing bot smoke",
        "targetRef": "acme/billing-bot",
        "target": {"transport": "web-widget", "url": "https://example.com/support"},
        "sector": "utilities",
        "mission": "check the outstanding balance",
        "kind": "freeform",
        "createdAt": "2026-08-12T00:00:00Z",
        "updatedAt": "2026-08-12T00:00:00Z",
    }
    doc.update(over)
    return doc


def test_create_posts(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs", method="POST", json=cfg_json()
    )
    c = client()
    r = c.digital_test_configs.create(
        name="Billing bot smoke",
        target_ref="acme/billing-bot",
        target={"transport": "web-widget", "url": "https://example.com/support"},
        sector="utilities",
        mission="check the outstanding balance",
    )
    assert r.id == "c1"
    sent = json.loads(httpx_mock.get_requests()[0].content)
    assert sent["targetRef"] == "acme/billing-bot"
    c.close()


def test_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/digital-testing/configs/c1", json=cfg_json())
    c = client()
    assert c.digital_test_configs.get("c1").name == "Billing bot smoke"
    c.close()


def test_update_uses_patch_not_put(httpx_mock: HTTPXMock):
    """The voice config resource uses PUT. Digital deliberately uses PATCH."""
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs/c1",
        method="PATCH",
        json=cfg_json(name="Renamed"),
    )
    c = client()
    r = c.digital_test_configs.update("c1", name="Renamed")
    assert r.name == "Renamed"
    assert httpx_mock.get_requests()[0].method == "PATCH"
    c.close()


def test_delete(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs/c1", method="DELETE", status_code=204
    )
    c = client()
    assert c.digital_test_configs.delete("c1") is None
    assert httpx_mock.get_requests()[0].method == "DELETE"
    c.close()


def test_launch_posts_to_runs_subpath_and_unwraps(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs/c1/runs",
        method="POST",
        json={
            "message": "Digital test queued",
            "run": {
                "id": "r9",
                "workspaceId": "w1",
                "targetRef": "acme/billing-bot",
                "channel": "chat",
                "kind": "freeform",
                "status": "pending",
                "startedAt": "2026-08-12T00:00:00Z",
            },
        },
    )
    c = client()
    assert c.digital_test_configs.launch("c1", samples=3).id == "r9"
    c.close()


def test_list_walks_pages_via_configs_key(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs",
        json={"configs": [cfg_json(id="c1")], "nextCursor": "n2"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs?cursor=n2",
        json={"configs": [cfg_json(id="c2")]},
    )
    c = client()
    assert [x.id for x in c.digital_test_configs.list()] == ["c1", "c2"]
    c.close()


def test_list_with_explicit_cursor_advances(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs?cursor=n1",
        json={"configs": [cfg_json(id="c1")], "nextCursor": "n2"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs?cursor=n2",
        json={"configs": [cfg_json(id="c2")]},
    )
    c = client()
    assert [x.id for x in c.digital_test_configs.list(cursor="n1")] == ["c1", "c2"]
    c.close()


def test_list_page_maps_configs_and_next_cursor(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs",
        json={"configs": [cfg_json()], "nextCursor": "n2"},
    )
    c = client()
    page = c.digital_test_configs.list_page()
    assert len(page.items) == 1
    assert page.next_token == "n2"
    c.close()


async def test_update_async_uses_patch(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs/c1",
        method="PATCH",
        json=cfg_json(name="Renamed"),
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    r = await c.digital_test_configs.update("c1", name="Renamed")
    assert r.name == "Renamed"
    await c.aclose()


async def test_launch_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/configs/c1/runs",
        method="POST",
        json={
            "run": {
                "id": "r9",
                "workspaceId": "w1",
                "targetRef": "acme/billing-bot",
                "channel": "chat",
                "kind": "freeform",
                "status": "pending",
                "startedAt": "2026-08-12T00:00:00Z",
            }
        },
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    assert (await c.digital_test_configs.launch("c1")).id == "r9"
    await c.aclose()
