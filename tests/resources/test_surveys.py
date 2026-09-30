"""Tests for the surveys resource: runs, results and configs."""
import json
import time

import pytest
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, ConflictError, Nopaque, NopaqueTimeoutError, NotFoundError

BASE = "https://api.nopaque.co.uk"
RESULT_URL = f"{BASE}/testing/survey-results/r1"


def client():
    return Nopaque(api_key="k", max_retries=0)


def config_json(**over):
    """Shaped from the OpenAPI SurveyTestConfig schema."""
    doc = {
        "id": "c1",
        "workspaceId": "w1",
        "name": "300200 happy path",
        "sector": "energy",
        "mission": "Had an engineer visit, happy with it, would score 10.",
        "acceptance": "Asks for a 0-10 score, then a reason, then closes.",
        "scenario": "happy-path",
        "expectedTurns": 5,
        "createdAt": "2026-09-30T00:00:00Z",
        "updatedAt": "2026-09-30T00:00:00Z",
    }
    doc.update(over)
    return doc


def started_json(**over):
    doc = {
        "runId": "r1",
        "configId": "c1",
        "agentE164": "+447457416494",
        "endUserE164": "+447921721840",
        "state": "waiting",
        "startedAt": "2026-09-30T13:30:00Z",
        "expiresAt": 1790861400,
        "maxMessages": 40,
    }
    doc.update(over)
    return doc


def result_json(status="final", expires_at=None, **over):
    """Shaped from the OpenAPI SurveyResult schema."""
    doc = {
        "runId": "r1",
        "configId": "c1",
        "configName": "300200 happy path",
        "scenario": "happy-path",
        "agentE164": "+447457416494",
        "endUserE164": "+447921721840",
        "channel": "sms_chat",
        "startedAt": "2026-09-30T13:30:00Z",
        "expiresAt": int(time.time()) + 600 if expires_at is None else expires_at,
        "expectedTurns": 5,
        "answersGiven": 5,
        "state": "ended",
        "outcome": "completed",
        "endReason": "survey_over",
        "turnsTruncated": False,
        "capture": {"status": status},
        "turns": [
            {"at": "2026-09-30T13:36:41Z", "from": "survey", "text": "How likely... 0-10?"},
            {"at": "2026-09-30T13:36:50Z", "from": "respondent", "text": "10"},
        ],
    }
    doc.update(over)
    return doc


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------


def test_start_sends_sender_as_end_user_e164(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-runs", method="POST", status_code=201, json=started_json()
    )
    c = client()
    run = c.surveys.start(
        config_id="c1", sender="+447921721840", window_secs=600, expected_turns=5
    )
    assert run.agent_e164 == "+447457416494"
    assert run.run_id == "r1"
    assert run.expires_at == 1790861400
    sent = json.loads(httpx_mock.get_requests()[0].content)
    assert sent == {
        "configId": "c1",
        "endUserE164": "+447921721840",
        "windowSecs": 600,
        "expectedTurns": 5,
    }
    c.close()


def test_start_omits_unset_optionals(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-runs", method="POST", status_code=201, json=started_json()
    )
    c = client()
    c.surveys.start(config_id="c1", sender="+447921721840")
    sent = json.loads(httpx_mock.get_requests()[0].content)
    assert sent == {"configId": "c1", "endUserE164": "+447921721840"}
    c.close()


def test_start_busy_raises_conflict(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-runs",
        method="POST",
        status_code=409,
        json={"error": "All 2 survey numbers are already running a test against this sender."},
    )
    c = client()
    with pytest.raises(ConflictError, match="already running"):
        c.surveys.start(config_id="c1", sender="+447921721840")
    c.close()


def test_stop(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-runs/r1", method="DELETE", status_code=204
    )
    c = client()
    assert c.surveys.stop("r1") is None
    c.close()


def test_list_runs_and_number_counts(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-runs",
        json={
            "runs": [
                {
                    "runId": "r1",
                    "configId": "c1",
                    "agentE164": "+447457416494",
                    "endUserE164": "+447921721840",
                    "state": "in_progress",
                    "startedAt": "2026-09-30T13:30:00Z",
                    "expiresAt": 1790861400,
                    "live": True,
                    "answersGiven": 2,
                }
            ],
            "numbers": {"total": 3, "busy": 1, "free": 2},
        },
    )
    c = client()
    listed = c.surveys.list()
    assert listed.runs[0].state == "in_progress"
    assert listed.runs[0].answers_given == 2
    assert listed.numbers.free == 2
    c.close()


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


def test_result_get_parses_turns(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=RESULT_URL, json=result_json())
    c = client()
    r = c.surveys.results.get("r1")
    assert r.outcome == "completed"
    assert r.capture.status == "final"
    assert [(t.from_, t.text) for t in r.turns] == [
        ("survey", "How likely... 0-10?"),
        ("respondent", "10"),
    ]
    c.close()


def test_results_list_walks_pages_with_cursor(httpx_mock: HTTPXMock):
    summary = {k: v for k, v in result_json().items() if k != "turns"}
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-results",
        json={"results": [summary], "nextCursor": "cur1"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-results?cursor=cur1",
        json={"results": [dict(summary, runId="r2")]},
    )
    c = client()
    ids = [r.run_id for r in c.surveys.results.list()]
    assert ids == ["r1", "r2"]
    c.close()


def test_results_list_page(httpx_mock: HTTPXMock):
    summary = {k: v for k, v in result_json().items() if k != "turns"}
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-results?cursor=cur1",
        json={"results": [summary], "nextCursor": "cur2"},
    )
    c = client()
    page = c.surveys.results.list_page(cursor="cur1")
    assert page.items[0].run_id == "r1"
    assert page.next_token == "cur2"
    c.close()


# ---------------------------------------------------------------------------
# wait_for_result
# ---------------------------------------------------------------------------


def test_wait_for_result_tolerates_404_then_waits_past_provisional(httpx_mock: HTTPXMock):
    """The result row lags the start; provisional is not settled."""
    httpx_mock.add_response(url=RESULT_URL, status_code=404, json={"error": "Survey result not found"})
    httpx_mock.add_response(url=RESULT_URL, json=result_json(status="provisional"))
    httpx_mock.add_response(url=RESULT_URL, json=result_json(status="final"))
    c = client()
    seen = []
    r = c.surveys.wait_for_result(
        "r1", poll_interval=0.001, on_update=lambda res: seen.append(res.capture.status)
    )
    assert r.capture.status == "final"
    assert seen == ["provisional", "final"]
    c.close()


def test_wait_for_result_returns_failed_capture(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=RESULT_URL,
        json=result_json(status="failed", capture={"status": "failed", "error": "telnyx 500"}),
    )
    c = client()
    r = c.surveys.wait_for_result("r1", poll_interval=0.001)
    assert r.capture.status == "failed"
    assert r.capture.error == "telnyx 500"
    c.close()


def test_wait_for_result_rethrows_404_after_grace(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=RESULT_URL, status_code=404, json={"error": "Survey result not found"}, is_reusable=True
    )
    c = client()
    with pytest.raises(NotFoundError):
        c.surveys.wait_for_result("r1", poll_interval=0.01, not_found_grace=0.05)
    c.close()


def test_wait_for_result_explicit_timeout(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=RESULT_URL, json=result_json(status="provisional"), is_reusable=True
    )
    c = client()
    with pytest.raises(NopaqueTimeoutError, match="provisional"):
        c.surveys.wait_for_result("r1", timeout=0.05, poll_interval=0.01)
    c.close()


def test_wait_for_result_default_deadline_comes_from_the_window(httpx_mock: HTTPXMock):
    """No timeout: give up 10 minutes after the window ended."""
    long_gone = int(time.time()) - 700
    httpx_mock.add_response(
        url=RESULT_URL, json=result_json(status="pending", expires_at=long_gone)
    )
    c = client()
    with pytest.raises(NopaqueTimeoutError):
        c.surveys.wait_for_result("r1", poll_interval=0.001)
    c.close()


async def test_wait_for_result_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=RESULT_URL, status_code=404, json={"error": "Survey result not found"})
    httpx_mock.add_response(url=RESULT_URL, json=result_json(status="final"))
    c = AsyncNopaque(api_key="k", max_retries=0)
    r = await c.surveys.wait_for_result("r1", poll_interval=0.001)
    assert r.outcome == "completed"
    await c.aclose()


# ---------------------------------------------------------------------------
# Configs
# ---------------------------------------------------------------------------


def test_config_create(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-test-configs",
        method="POST",
        status_code=201,
        json=config_json(),
    )
    c = client()
    cfg = c.surveys.configs.create(
        name="300200 happy path",
        sector="energy",
        mission="Had an engineer visit, happy with it, would score 10.",
        acceptance="Asks for a 0-10 score, then a reason, then closes.",
        scenario="happy-path",
        expected_turns=5,
        profile_id="p1",
    )
    assert cfg.id == "c1"
    sent = json.loads(httpx_mock.get_requests()[0].content)
    assert sent["expectedTurns"] == 5
    assert sent["profileId"] == "p1"
    assert "description" not in sent
    c.close()


def test_config_list_is_a_plain_list(httpx_mock: HTTPXMock):
    item = {k: v for k, v in config_json().items() if k not in ("mission", "acceptance")}
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-test-configs", json={"configs": [item]}
    )
    c = client()
    configs = c.surveys.configs.list()
    assert [x.name for x in configs] == ["300200 happy path"]
    c.close()


def test_config_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/testing/survey-test-configs/c1", json=config_json())
    c = client()
    assert c.surveys.configs.get("c1").acceptance.startswith("Asks")
    c.close()


def test_config_update_is_a_patch_of_only_passed_fields(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-test-configs/c1",
        method="PATCH",
        json=config_json(scenario="abandons"),
    )
    c = client()
    cfg = c.surveys.configs.update("c1", scenario="abandons")
    assert cfg.scenario == "abandons"
    sent = json.loads(httpx_mock.get_requests()[0].content)
    assert sent == {"scenario": "abandons"}
    c.close()


def test_config_delete(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-test-configs/c1", method="DELETE", status_code=204
    )
    c = client()
    assert c.surveys.configs.delete("c1") is None
    c.close()


async def test_config_create_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/survey-test-configs",
        method="POST",
        status_code=201,
        json=config_json(),
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    cfg = await c.surveys.configs.create(
        name="300200 happy path",
        sector="energy",
        mission="m",
        acceptance="a",
        scenario="happy-path",
    )
    assert cfg.workspace_id == "w1"
    await c.aclose()
