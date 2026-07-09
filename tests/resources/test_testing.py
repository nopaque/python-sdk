from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque


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
        json={"id": "r1", "status": "completed", "result": "pass"},
    )
    c = client()
    run = c.testing.runs.get("r1")
    assert run.result == "pass"
    c.close()


def test_wait_for_run(httpx_mock: HTTPXMock):
    for status in ("running", "completed"):
        httpx_mock.add_response(
            url="https://api.nopaque.co.uk/testing/runs/r1",
            json={"id": "r1", "status": status},
        )
    c = client()
    run = c.testing.runs.wait_for_run("r1", timeout=5.0, poll_interval=0.01)
    assert run.status == "completed"
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
