"""Tests for the digital testing resource."""
import json

import pytest
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque, NopaqueTimeoutError

BASE = "https://api.nopaque.co.uk"


def client():
    return Nopaque(api_key="k", max_retries=0)


def run_json(**over):
    """Shaped from the OpenAPI DigitalTestRun schema, camelCase as the wire sends it."""
    doc = {
        "id": "r1",
        "workspaceId": "w1",
        "targetRef": "acme/billing-bot",
        "channel": "chat",
        "kind": "freeform",
        "status": "pending",
        "startedAt": "2026-08-12T00:00:00Z",
    }
    doc.update(over)
    return doc


def test_create_unwraps_envelope_and_sends_camel_case(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs",
        method="POST",
        json={"message": "Digital test queued", "run": run_json()},
    )
    c = client()
    r = c.digital_testing.create(
        target_ref="acme/billing-bot",
        target={"transport": "web-widget", "url": "https://example.com/support"},
        sector="utilities",
        mission="check the outstanding balance",
        kind="freeform",
        acceptance="The bot states the outstanding balance.",
    )
    assert r.id == "r1"
    sent = json.loads(httpx_mock.get_requests()[0].content)
    assert sent["targetRef"] == "acme/billing-bot"
    assert sent["target"]["transport"] == "web-widget"
    assert "target_ref" not in sent
    c.close()


def test_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs/r1", json=run_json(status="completed")
    )
    c = client()
    assert c.digital_testing.get("r1").status == "completed"
    c.close()


def test_cancel_posts(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs/r1/cancel",
        method="POST",
        json=run_json(status="cancelled"),
    )
    c = client()
    assert c.digital_testing.cancel("r1").status == "cancelled"
    c.close()


def test_list_walks_pages_via_next_cursor(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs?limit=2",
        json={"runs": [run_json(id="r1")], "nextCursor": "c2"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs?limit=2&cursor=c2",
        json={"runs": [run_json(id="r2")]},
    )
    c = client()
    assert [r.id for r in c.digital_testing.list(limit=2)] == ["r1", "r2"]
    c.close()


def test_list_with_explicit_cursor_advances(httpx_mock: HTTPXMock):
    """A caller-supplied starting cursor must not pin every page to page one."""
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs?cursor=c1",
        json={"runs": [run_json(id="r1")], "nextCursor": "c2"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs?cursor=c2",
        json={"runs": [run_json(id="r2")]},
    )
    c = client()
    assert [r.id for r in c.digital_testing.list(cursor="c1")] == ["r1", "r2"]
    c.close()


def test_list_page_maps_runs_and_next_cursor(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs",
        json={"runs": [run_json()], "nextCursor": "c2"},
    )
    c = client()
    page = c.digital_testing.list_page()
    assert len(page.items) == 1
    assert page.next_token == "c2"
    c.close()


def test_wait_for_run_returns_on_completed_even_when_outcome_is_fail(httpx_mock: HTTPXMock):
    """A badly-behaved bot is a RESULT, not an error. This must not raise."""
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs/r1",
        json=run_json(status="completed", outcome="fail", passRate=0.25),
    )
    c = client()
    r = c.digital_testing.wait_for_run("r1", poll_interval=0.001)
    assert r.status == "completed"
    assert r.outcome == "fail"
    assert r.pass_rate == 0.25
    c.close()


def test_wait_for_run_returns_on_cancelled(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs/r1", json=run_json(status="cancelled")
    )
    c = client()
    assert c.digital_testing.wait_for_run("r1", poll_interval=0.001).status == "cancelled"
    c.close()


def test_wait_for_run_returns_on_failed_with_reason(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs/r1",
        json=run_json(status="failed", failureReason="transport timeout"),
    )
    c = client()
    r = c.digital_testing.wait_for_run("r1", poll_interval=0.001)
    assert r.failure_reason == "transport timeout"
    c.close()


def test_wait_for_run_times_out(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs/r1",
        json=run_json(status="running"),
        # This build of pytest_httpx consumes a response on first match, so a
        # poll loop needs it registered as reusable.
        is_reusable=True,
    )
    c = client()
    with pytest.raises(NopaqueTimeoutError):
        c.digital_testing.wait_for_run("r1", timeout=0.05, poll_interval=0.01)
    c.close()


async def test_create_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs",
        method="POST",
        json={"message": "Digital test queued", "run": run_json()},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    r = await c.digital_testing.create(
        target_ref="acme/billing-bot",
        target={"transport": "web-widget", "url": "https://example.com/support"},
        sector="utilities",
        mission="check the outstanding balance",
    )
    assert r.id == "r1"
    await c.aclose()


async def test_list_async_walks_pages(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs",
        json={"runs": [run_json(id="r1")], "nextCursor": "c2"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/runs?cursor=c2",
        json={"runs": [run_json(id="r2")]},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    seen = [r.id async for r in c.digital_testing.list()]
    assert seen == ["r1", "r2"]
    await c.aclose()
