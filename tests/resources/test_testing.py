import json

import pytest
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, CarrierCustomHeader, Nopaque


def client():
    return Nopaque(api_key="k", max_retries=0)


# --- configs ---

def test_configs_create(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/configs",
        method="POST",
        json={"id": "cfg_1", "name": "T1", "phoneNumber": "+441", "steps": []},
    )
    c = client()
    cfg = c.testing.configs.create(
        name="T1", phone_number="+441", steps=[]
    )
    assert cfg.id == "cfg_1"
    c.close()


def test_configs_list(httpx_mock: HTTPXMock):
    # Server returns { configs: [...] } (not { items }) — SDK normalizes.
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/configs",
        json={"configs": [{"id": "cfg_1", "name": "T1"}]},
    )
    c = client()
    out = list(c.testing.configs.list())
    assert out[0].id == "cfg_1"
    c.close()


def test_configs_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/configs/cfg_1",
        json={"id": "cfg_1", "name": "T1"},
    )
    c = client()
    cfg = c.testing.configs.get("cfg_1")
    assert cfg.id == "cfg_1"
    c.close()


def test_configs_update(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/configs/cfg_1",
        method="PUT",
        json={"id": "cfg_1", "name": "updated"},
    )
    c = client()
    cfg = c.testing.configs.update("cfg_1", name="updated")
    assert cfg.name == "updated"
    c.close()


def test_configs_delete(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/configs/cfg_1",
        method="DELETE",
        json={"message": "ok"},
    )
    c = client()
    c.testing.configs.delete("cfg_1")
    c.close()


# --- jobs ---

def test_jobs_create(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/jobs",
        method="POST",
        json={"id": "job_1", "configId": "cfg_1", "status": "created"},
    )
    c = client()
    job = c.testing.jobs.create(config_id="cfg_1")
    assert job.id == "job_1"
    c.close()


def test_jobs_list(httpx_mock: HTTPXMock):
    # Server returns { jobs: [...] } — SDK normalizes.
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/jobs",
        json={"jobs": [{"id": "job_1", "status": "completed"}]},
    )
    c = client()
    out = list(c.testing.jobs.list())
    assert out[0].id == "job_1"
    c.close()


def test_jobs_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/jobs/job_1",
        json={"id": "job_1", "status": "completed"},
    )
    c = client()
    job = c.testing.jobs.get("job_1")
    assert job.status == "completed"
    c.close()


def test_jobs_delete(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/jobs/job_1",
        method="DELETE",
        json={"message": "ok"},
    )
    c = client()
    c.testing.jobs.delete("job_1")
    c.close()


# --- runs ---

def test_runs_create_from_job(httpx_mock: HTTPXMock):
    # Server wraps as { message, run } and uses `id` (not `runId`) on the entity.
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs",
        method="POST",
        json={"message": "Test run started", "run": {"id": "r1", "jobId": "job_1", "status": "pending"}},
    )
    c = client()
    run = c.testing.runs.create(job_id="job_1")
    assert run.id == "r1"
    assert run.status == "pending"
    # Verify we sent jobId, not testConfigId
    import json as _j
    assert _j.loads(httpx_mock.get_requests()[0].content) == {"jobId": "job_1"}
    c.close()


def test_runs_create_from_config(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs",
        method="POST",
        json={"message": "Test run started", "run": {"id": "r2", "testConfigId": "cfg_1", "status": "pending"}},
    )
    c = client()
    run = c.testing.runs.create(test_config_id="cfg_1")
    assert run.id == "r2"
    assert run.test_config_id == "cfg_1"
    import json as _j
    assert _j.loads(httpx_mock.get_requests()[0].content) == {"testConfigId": "cfg_1"}
    c.close()


def test_runs_create_requires_exactly_one_id():
    import pytest
    c = client()
    with pytest.raises(ValueError):
        c.testing.runs.create()
    with pytest.raises(ValueError):
        c.testing.runs.create(job_id="j", test_config_id="c")
    c.close()


def test_runs_list(httpx_mock: HTTPXMock):
    # Server returns { runs: [...] } — SDK normalizes.
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs",
        json={"runs": [{"id": "r1", "status": "completed"}]},
    )
    c = client()
    out = list(c.testing.runs.list())
    assert out[0].id == "r1"
    c.close()


def test_runs_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/r1",
        json={"id": "r1", "status": "completed", "outcome": "PASS"},
    )
    c = client()
    run = c.testing.runs.get("r1")
    # The API sends `outcome` (uppercase), never `result`.
    assert run.outcome == "PASS"
    c.close()


def test_wait_for_run(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/r1",
        json={"id": "r1", "status": "running"},
    )
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/r1",
        json={"id": "r1", "status": "completed", "outcome": "PASS"},
    )
    c = client()
    run = c.testing.runs.wait_for_run("r1", timeout=5.0, poll_interval=0.01)
    assert run.status == "completed"
    assert run.outcome == "PASS"
    c.close()


def test_wait_for_run_keeps_polling_until_the_verdict_is_written(
    httpx_mock: HTTPXMock,
):
    """run_status_changed{completed} can land before run_completed{outcome}:
    separate SQS messages, no ordering guarantee. Polling on status alone
    returned that row — outcome None, no steps — on a passing run."""
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/r1",
        json={"id": "r1", "status": "completed", "stepResults": []},
    )
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/r1",
        json={"id": "r1", "status": "completed", "outcome": "pending"},
    )
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/r1",
        json={
            "id": "r1",
            "status": "completed",
            "outcome": "PASS",
            "stepResults": [
                {"id": "s1", "runId": "r1", "stepIndex": 0, "outcome": "PASS"}
            ],
        },
    )
    c = client()
    run = c.testing.runs.wait_for_run("r1", timeout=5.0, poll_interval=0.01)
    assert run.outcome == "PASS"
    assert len(run.step_results) == 1
    c.close()


def test_wait_for_run_settles_on_failed_without_a_verdict(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/r2",
        json={"id": "r2", "status": "failed"},
    )
    c = client()
    run = c.testing.runs.wait_for_run("r2", timeout=5.0, poll_interval=0.01)
    assert run.status == "failed"
    c.close()


# --- v0.3.0: runs filters + aggregate + mission-test-run ---

def test_runs_list_sends_filters_and_returns_slim_items(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs?runType=mission&outcome=PASS&limit=25&sortBy=completedAt",
        json={
            "runs": [
                {
                    "id": "r1",
                    "workspaceId": "w",
                    "runType": "mission",
                    "status": "completed",
                    "outcome": "PASS",
                    "passedSteps": 3,
                    "callDurationSecs": 42.5,
                    "startedAt": "2026-07-09T00:00:00Z",
                }
            ],
            "nextCursor": None,
        },
    )
    c = client()
    out = list(
        c.testing.runs.list(
            run_type="mission", outcome="PASS", limit=25, sort_by="completedAt"
        )
    )
    assert out[0].id == "r1"
    assert out[0].run_type == "mission"
    assert out[0].call_duration_secs == 42.5
    c.close()


def test_runs_list_paginates_on_next_cursor(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs",
        json={"runs": [{"id": "r1", "status": "completed"}], "nextCursor": "C2"},
    )
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs?cursor=C2",
        json={"runs": [{"id": "r2", "status": "completed"}], "nextCursor": None},
    )
    c = client()
    ids = [r.id for r in c.testing.runs.list()]
    assert ids == ["r1", "r2"]
    c.close()


def test_aggregate_runs_flat_groups(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/aggregate?groupBy=outcome",
        json={
            "groups": [{"key": "PASS", "count": 10}, {"key": "FAIL", "count": 2}],
            "truncated": False,
            "totalGroups": 2,
        },
    )
    c = client()
    agg = c.testing.aggregate_runs(group_by="outcome")
    assert agg.total_groups == 2
    assert agg.truncated is False
    assert agg.groups is not None
    assert agg.groups[0].key == "PASS"
    assert agg.groups[0].count == 10
    req = httpx_mock.get_requests()[0]
    assert req.url.path == "/testing/runs/aggregate"
    c.close()


def test_aggregate_runs_time_buckets(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/aggregate?groupBy=outcome&timeBucket=day",
        json={
            "buckets": [
                {"bucket": "2026-07-09", "groups": [{"key": "PASS", "count": 4}]}
            ],
            "truncated": False,
            "totalGroups": 1,
        },
    )
    c = client()
    agg = c.testing.aggregate_runs(group_by="outcome", time_bucket="day")
    assert agg.buckets is not None
    assert agg.buckets[0].bucket == "2026-07-09"
    assert agg.buckets[0].groups[0].key == "PASS"
    c.close()


def test_get_mission_test_run(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-test-runs/mtr_1",
        json={
            "id": "mtr_1",
            "workspaceId": "w",
            "status": "completed",
            "outcome": "PASS",
            "verdict": "pass",
            "passed": True,
            "sector": "insurance",
            "startedAt": "2026-07-09T00:00:00Z",
        },
    )
    c = client()
    run = c.testing.get_mission_test_run("mtr_1")
    assert run.id == "mtr_1"
    assert run.verdict == "pass"
    assert run.passed is True
    assert run.outcome == "PASS"
    c.close()


async def test_async_aggregate_and_mission_run(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/aggregate?groupBy=runType",
        json={"groups": [{"key": "mission", "count": 3}], "truncated": False, "totalGroups": 1},
    )
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-test-runs/mtr_9",
        json={"id": "mtr_9", "workspaceId": "w", "status": "running", "startedAt": "t"},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    agg = await c.testing.aggregate_runs(group_by="runType")
    assert agg.groups is not None and agg.groups[0].key == "mission"
    run = await c.testing.get_mission_test_run("mtr_9")
    assert run.id == "mtr_9"
    await c.aclose()


# --- voices ---

def test_list_voices(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/voices",
        json={
            "voices": [
                {
                    "voiceId": "Telnyx.Ultra.c8f7835e-28a3-4f0c-80d7-c1302ac62aae",
                    "name": "Ultra",
                }
            ],
            "defaultVoiceId": "Telnyx.Ultra.c8f7835e-28a3-4f0c-80d7-c1302ac62aae",
        },
    )
    c = client()
    r = c.testing.list_voices()
    assert r.voices[0].voice_id.startswith("Telnyx.")
    assert r.default_voice_id == r.voices[0].voice_id
    c.close()


async def test_list_voices_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/voices",
        json={"voices": [{"voiceId": "v1", "name": "Ultra"}]},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    r = await c.testing.list_voices()
    assert r.voices[0].voice_id == "v1"
    await c.aclose()


# --- bring your own carrier ---

BASE = "https://api.nopaque.co.uk/testing/carrier-integrations"

ROUTE = {
    "routeId": "rt_1",
    "integrationId": "ci_1",
    "name": "Vendor X premium",
    "techPrefix": "R7Q2#",
    "customHeaders": [{"name": "X-Vendor-Route", "value": "vx-premium"}],
    "enabled": True,
    "dialable": True,
    "createdAt": "2026-10-01T00:00:00Z",
    "updatedAt": "2026-10-01T00:00:00Z",
}

INTEGRATION = {
    "integrationId": "ci_1",
    "name": "Integral London SBC",
    "host": "sbc.example.net",
    "port": 5060,
    "transport": "UDP",
    "mediaEncryption": "disabled",
    "status": "active",
    "hasCredentials": False,
    "maxConcurrentCalls": 5,
    "dailyMinutes": 300,
    "createdAt": "2026-10-01T00:00:00Z",
    "updatedAt": "2026-10-01T00:00:00Z",
    "routes": [ROUTE],
}


def test_carrier_integrations_list(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=BASE, method="GET", json={"integrations": [INTEGRATION]})
    c = client()
    out = c.testing.carrier_integrations.list()
    assert len(out) == 1
    ci = out[0]
    assert ci.integration_id == "ci_1"
    assert ci.status == "active"
    assert ci.max_concurrent_calls == 5
    assert ci.daily_minutes == 300
    assert ci.has_credentials is False
    assert ci.routes[0].route_id == "rt_1"
    assert ci.routes[0].tech_prefix == "R7Q2#"
    assert ci.routes[0].custom_headers[0].name == "X-Vendor-Route"
    assert ci.routes[0].dialable is True
    c.close()


def test_carrier_integrations_list_empty(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=BASE, json={"integrations": []})
    c = client()
    assert c.testing.carrier_integrations.list() == []
    c.close()


def test_carrier_integrations_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/ci_1", json={"integration": INTEGRATION})
    c = client()
    ci = c.testing.carrier_integrations.get("ci_1")
    assert ci.integration_id == "ci_1"
    assert ci.host == "sbc.example.net"
    assert ci.routes[0].route_id == "rt_1"
    c.close()


def test_carrier_routes_list(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/ci_1/routes", json={"routes": [ROUTE]})
    c = client()
    routes = c.testing.carrier_integrations.routes.list("ci_1")
    assert [r.route_id for r in routes] == ["rt_1"]
    c.close()


def test_carrier_routes_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/ci_1/routes/rt_1", json={"route": ROUTE})
    c = client()
    r = c.testing.carrier_integrations.routes.get("ci_1", "rt_1")
    assert r.route_id == "rt_1"
    assert r.integration_id == "ci_1"
    c.close()


def test_carrier_routes_create(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/ci_1/routes", method="POST", status_code=201, json={"route": ROUTE}
    )
    c = client()
    r = c.testing.carrier_integrations.routes.create(
        "ci_1",
        name="Vendor X premium",
        tech_prefix="R7Q2#",
        custom_headers=[{"name": "X-Vendor-Route", "value": "vx-premium"}],
    )
    assert r.route_id == "rt_1"
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {
        "name": "Vendor X premium",
        "techPrefix": "R7Q2#",
        "customHeaders": [{"name": "X-Vendor-Route", "value": "vx-premium"}],
    }
    c.close()


def test_carrier_routes_create_sends_only_name_by_default(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/ci_1/routes", method="POST", status_code=201, json={"route": ROUTE}
    )
    c = client()
    c.testing.carrier_integrations.routes.create("ci_1", name="Default")
    assert json.loads(httpx_mock.get_requests()[0].content) == {"name": "Default"}
    c.close()


def test_carrier_routes_update(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/ci_1/routes/rt_1",
        method="PATCH",
        json={"route": {**ROUTE, "enabled": False, "dialable": False, "customHeaders": []}},
    )
    c = client()
    r = c.testing.carrier_integrations.routes.update(
        "ci_1",
        "rt_1",
        enabled=False,
        custom_headers=[CarrierCustomHeader(name="X-A", value="b")],
    )
    assert r.enabled is False
    assert r.dialable is False
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {"enabled": False, "customHeaders": [{"name": "X-A", "value": "b"}]}
    c.close()


def test_carrier_routes_update_requires_a_field():
    c = client()
    with pytest.raises(ValueError):
        c.testing.carrier_integrations.routes.update("ci_1", "rt_1")
    c.close()


async def test_async_carrier_integrations(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=BASE, json={"integrations": [INTEGRATION]})
    httpx_mock.add_response(url=f"{BASE}/ci_1", json={"integration": INTEGRATION})
    httpx_mock.add_response(url=f"{BASE}/ci_1/routes", json={"routes": [ROUTE]})
    httpx_mock.add_response(url=f"{BASE}/ci_1/routes/rt_1", json={"route": ROUTE})
    httpx_mock.add_response(
        url=f"{BASE}/ci_1/routes", method="POST", status_code=201, json={"route": ROUTE}
    )
    httpx_mock.add_response(
        url=f"{BASE}/ci_1/routes/rt_1", method="PATCH", json={"route": {**ROUTE, "name": "New"}}
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    ci = c.testing.carrier_integrations
    assert (await ci.list())[0].integration_id == "ci_1"
    assert (await ci.get("ci_1")).name == "Integral London SBC"
    assert (await ci.routes.list("ci_1"))[0].route_id == "rt_1"
    assert (await ci.routes.get("ci_1", "rt_1")).tech_prefix == "R7Q2#"
    created = await ci.routes.create("ci_1", name="Vendor X premium", tech_prefix="R7Q2#")
    assert created.route_id == "rt_1"
    updated = await ci.routes.update("ci_1", "rt_1", name="New")
    assert updated.name == "New"
    await c.aclose()


def test_configs_create_with_carrier_route(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/configs",
        method="POST",
        json={"id": "cfg_1", "name": "T1", "phoneNumber": "+441", "carrierRouteId": "rt_1"},
    )
    c = client()
    cfg = c.testing.configs.create(
        name="T1", phone_number="+441", steps=[], carrier_route_id="rt_1"
    )
    assert cfg.carrier_route_id == "rt_1"
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["carrierRouteId"] == "rt_1"
    c.close()


def test_configs_create_omits_carrier_route_by_default(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/configs",
        method="POST",
        json={"id": "cfg_1", "name": "T1"},
    )
    c = client()
    cfg = c.testing.configs.create(name="T1", phone_number="+441", steps=[])
    assert cfg.carrier_route_id is None
    assert "carrierRouteId" not in json.loads(httpx_mock.get_requests()[0].content)
    c.close()


def test_configs_update_carrier_route_set_remove_and_leave(httpx_mock: HTTPXMock):
    url = "https://api.nopaque.co.uk/testing/configs/cfg_1"
    for _ in range(3):
        httpx_mock.add_response(url=url, method="PUT", json={"id": "cfg_1", "name": "T1"})
    c = client()
    c.testing.configs.update("cfg_1", carrier_route_id="rt_2")
    c.testing.configs.update("cfg_1", carrier_route_id=None)
    c.testing.configs.update("cfg_1", name="T1")
    bodies = [json.loads(r.content) for r in httpx_mock.get_requests()]
    assert bodies[0] == {"carrierRouteId": "rt_2"}
    assert bodies[1] == {"carrierRouteId": None}
    assert bodies[2] == {"name": "T1"}
    c.close()


async def test_async_configs_carrier_route(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/configs",
        method="POST",
        json={"id": "cfg_1", "name": "T1", "carrierRouteId": "rt_1"},
    )
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/configs/cfg_1",
        method="PUT",
        json={"id": "cfg_1", "name": "T1"},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    cfg = await c.testing.configs.create(
        name="T1", phone_number="+441", steps=[], carrier_route_id="rt_1"
    )
    assert cfg.carrier_route_id == "rt_1"
    await c.testing.configs.update("cfg_1", carrier_route_id=None)
    bodies = [json.loads(r.content) for r in httpx_mock.get_requests()]
    assert bodies[0]["carrierRouteId"] == "rt_1"
    assert bodies[1] == {"carrierRouteId": None}
    await c.aclose()


def test_runs_get_exposes_dtmf_steps_and_carrier_outcome(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/run_1",
        json={
            "id": "run_1",
            "workspaceId": "w",
            "status": "completed",
            "outcome": "FAIL",
            "startedAt": "2026-10-01T00:00:00Z",
            "carrier": {"integrationId": "ci_1", "routeId": "rt_1"},
            "callTelemetry": {
                "schemaVersion": 1,
                "telephony": {
                    "hangupCause": "normal_clearing",
                    "hangupSource": "callee",
                    "sipHangupCause": "200",
                },
            },
            "stepResults": [
                {
                    "id": "s1",
                    "runId": "run_1",
                    "stepIndex": 0,
                    "stepId": "st1",
                    "stepName": "Press 1",
                    "outcome": "FAIL",
                    "expectedTranscript": "Thank you",
                    "actualTranscript": "Sorry, I didn't get that",
                    "similarity": 12.5,
                    "threshold": 80,
                    "actionType": "dtmf",
                    "actionValue": "1",
                    "createdAt": "2026-10-01T00:00:01Z",
                }
            ],
        },
    )
    c = client()
    run = c.testing.runs.get("run_1")
    assert run.carrier is not None
    assert run.carrier.integration_id == "ci_1"
    assert run.carrier.route_id == "rt_1"
    assert run.call_telemetry is not None
    assert run.call_telemetry.telephony is not None
    assert run.call_telemetry.telephony["sipHangupCause"] == "200"
    assert run.call_telemetry.telephony["hangupCause"] == "normal_clearing"
    step = run.step_results[0]
    assert (step.action_type, step.action_value, step.outcome) == ("dtmf", "1", "FAIL")
    assert step.actual_transcript == "Sorry, I didn't get that"
    assert step.expected_transcript == "Thank you"
    assert step.similarity == 12.5
    c.close()


def test_runs_get_without_carrier(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/run_2",
        json={"id": "run_2", "status": "running"},
    )
    c = client()
    run = c.testing.runs.get("run_2")
    assert run.carrier is None
    assert run.call_telemetry is None
    c.close()


# --- configs: full create/update field coverage ---

_CONFIG_URL = "https://api.nopaque.co.uk/testing/configs"
_FULL_CONFIG = {
    "id": "cfg_1",
    "workspaceId": "ws_1",
    "name": "T1",
    "description": "Main menu",
    "phoneNumber": "+441",
    "type": "parameterized",
    "profileId": "prof_1",
    "requiredParameters": ["accountNumber", "dob"],
    "scheduleId": "sch_1",
    "maxDurationSecs": 600,
    "carrierRouteId": "rt_1",
    "steps": [],
    "version": 2,
    "createdBy": "user_1",
}
_FULL_CREATE_KWARGS = dict(
    name="T1",
    phone_number="+441",
    steps=[{"name": "Hold", "type": "hold", "durationSecs": 30}],
    description="Main menu",
    type="parameterized",
    profile_id="prof_1",
    required_parameters=("accountNumber", "dob"),
    schedule_id="template:weekday-9am",
    max_duration_secs=600,
    carrier_route_id="rt_1",
)
_FULL_CREATE_BODY = {
    "name": "T1",
    "phoneNumber": "+441",
    "steps": [{"name": "Hold", "type": "hold", "durationSecs": 30}],
    "description": "Main menu",
    "type": "parameterized",
    "profileId": "prof_1",
    "requiredParameters": ["accountNumber", "dob"],
    "scheduleId": "template:weekday-9am",
    "maxDurationSecs": 600,
    "carrierRouteId": "rt_1",
}


def _assert_full_config(cfg):
    assert cfg.workspace_id == "ws_1"
    assert cfg.description == "Main menu"
    assert cfg.type == "parameterized"
    assert cfg.profile_id == "prof_1"
    assert cfg.required_parameters == ["accountNumber", "dob"]
    assert cfg.schedule_id == "sch_1"
    assert cfg.max_duration_secs == 600
    assert cfg.version == 2
    assert cfg.created_by == "user_1"
    assert cfg.model_extra == {}


def test_configs_create_sends_all_fields(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=_CONFIG_URL, method="POST", json=_FULL_CONFIG)
    c = client()
    cfg = c.testing.configs.create(**_FULL_CREATE_KWARGS)
    assert json.loads(httpx_mock.get_requests()[0].content) == _FULL_CREATE_BODY
    _assert_full_config(cfg)
    c.close()


def test_configs_create_sends_only_required_by_default(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=_CONFIG_URL, method="POST", json={"id": "cfg_1", "name": "T1"})
    c = client()
    cfg = c.testing.configs.create(name="T1", phone_number="+441", steps=[])
    assert json.loads(httpx_mock.get_requests()[0].content) == {
        "name": "T1",
        "phoneNumber": "+441",
        "steps": [],
    }
    assert cfg.max_duration_secs is None and cfg.schedule_id is None
    c.close()


def test_configs_update_sends_all_fields(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{_CONFIG_URL}/cfg_1", method="PUT", json=_FULL_CONFIG)
    c = client()
    cfg = c.testing.configs.update(
        "cfg_1",
        name="T1",
        description="Main menu",
        phone_number="+441",
        type="standard",
        profile_id="prof_1",
        required_parameters=["accountNumber"],
        steps=[],
        schedule_id="sch_1",
        max_duration_secs=900,
        carrier_route_id="rt_1",
    )
    assert json.loads(httpx_mock.get_requests()[0].content) == {
        "name": "T1",
        "description": "Main menu",
        "phoneNumber": "+441",
        "type": "standard",
        "profileId": "prof_1",
        "requiredParameters": ["accountNumber"],
        "steps": [],
        "scheduleId": "sch_1",
        "maxDurationSecs": 900,
        "carrierRouteId": "rt_1",
    }
    _assert_full_config(cfg)
    c.close()


def test_configs_update_omit_vs_null(httpx_mock: HTTPXMock):
    url = f"{_CONFIG_URL}/cfg_1"
    for _ in range(3):
        httpx_mock.add_response(url=url, method="PUT", json={"id": "cfg_1", "name": "T1"})
    c = client()
    # None clears the nullable fields.
    c.testing.configs.update(
        "cfg_1", schedule_id=None, max_duration_secs=None, carrier_route_id=None
    )
    # Omitted nullable fields are not sent at all.
    c.testing.configs.update("cfg_1", description="d")
    # None on a non-nullable field means "leave unchanged", not null.
    c.testing.configs.update(
        "cfg_1", description=None, type=None, profile_id=None, required_parameters=None
    )
    bodies = [json.loads(r.content) for r in httpx_mock.get_requests()]
    assert bodies[0] == {"scheduleId": None, "maxDurationSecs": None, "carrierRouteId": None}
    assert bodies[1] == {"description": "d"}
    assert bodies[2] == {}
    c.close()


async def test_async_configs_create_sends_all_fields(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=_CONFIG_URL, method="POST", json=_FULL_CONFIG)
    c = AsyncNopaque(api_key="k", max_retries=0)
    cfg = await c.testing.configs.create(**_FULL_CREATE_KWARGS)
    assert json.loads(httpx_mock.get_requests()[0].content) == _FULL_CREATE_BODY
    _assert_full_config(cfg)
    await c.aclose()


async def test_async_configs_update_fields_and_omit_vs_null(httpx_mock: HTTPXMock):
    url = f"{_CONFIG_URL}/cfg_1"
    for _ in range(3):
        httpx_mock.add_response(url=url, method="PUT", json=_FULL_CONFIG)
    c = AsyncNopaque(api_key="k", max_retries=0)
    cfg = await c.testing.configs.update(
        "cfg_1",
        description="Main menu",
        type="parameterized",
        profile_id="prof_1",
        required_parameters=["dob"],
        schedule_id="sch_1",
        max_duration_secs=600,
    )
    _assert_full_config(cfg)
    await c.testing.configs.update("cfg_1", schedule_id=None, max_duration_secs=None)
    await c.testing.configs.update("cfg_1", name="T1")
    bodies = [json.loads(r.content) for r in httpx_mock.get_requests()]
    assert bodies[0] == {
        "description": "Main menu",
        "type": "parameterized",
        "profileId": "prof_1",
        "requiredParameters": ["dob"],
        "scheduleId": "sch_1",
        "maxDurationSecs": 600,
    }
    assert bodies[1] == {"scheduleId": None, "maxDurationSecs": None}
    assert bodies[2] == {"name": "T1"}
    await c.aclose()
