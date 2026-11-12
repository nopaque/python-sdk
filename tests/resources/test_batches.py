import json

import pytest
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, BatchMember, Nopaque, RateLimitError


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_create(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batches",
        method="POST",
        json={"id": "b1", "name": "UK", "configId": "c1", "datasetId": "d1"},
    )
    c = client()
    b = c.batches.create(name="UK", config_id="c1", dataset_id="d1")
    assert b.id == "b1"
    c.close()


def test_list(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batches",
        json={"batches": [{"id": "b1", "name": "UK"}]},
    )
    c = client()
    out = list(c.batches.list())
    assert out[0].id == "b1"
    c.close()


def test_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batches/b1",
        json={"id": "b1", "name": "UK"},
    )
    c = client()
    b = c.batches.get("b1")
    assert b.id == "b1"
    c.close()


def test_update(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batches/b1",
        method="PUT",
        json={"id": "b1", "name": "EU"},
    )
    c = client()
    b = c.batches.update("b1", name="EU")
    assert b.name == "EU"
    c.close()


def test_delete(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batches/b1",
        method="DELETE",
        json={"message": "ok"},
    )
    c = client()
    c.batches.delete("b1")
    c.close()


def test_run(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batches/b1/run",
        method="POST",
        json={"batchId": "b1", "id": "r1", "status": "running"},
    )
    c = client()
    r = c.batches.run("b1")
    assert r.id == "r1"
    c.close()


def test_runs(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batches/b1/runs",
        json={"runs": [{"id": "r1", "status": "completed"}]},
    )
    c = client()
    out = list(c.batches.runs("b1"))
    assert out[0].id == "r1"
    c.close()


def test_list_runs(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batch-runs",
        json={"runs": [{"id": "r1", "batchId": "b1", "status": "completed"}]},
    )
    c = client()
    out = list(c.batches.list_runs())
    assert out[0].id == "r1"
    c.close()


def test_get_run(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batch-runs/r1",
        json={"id": "r1", "batchId": "b1", "status": "completed", "passRate": 0.9},
    )
    c = client()
    r = c.batches.get_run("r1")
    assert r.pass_rate == 0.9
    c.close()


def test_wait_for_run(httpx_mock: HTTPXMock):
    for status in ("running", "completed"):
        httpx_mock.add_response(
            url="https://api.nopaque.co.uk/testing/batch-runs/r1",
            json={"id": "r1", "status": status},
        )
    c = client()
    run = c.batches.wait_for_run("r1", timeout=5.0, poll_interval=0.01)
    assert run.status == "completed"
    c.close()


def test_rerun(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batch-runs/br1/rerun",
        method="POST",
        status_code=201,
        json={
            "id": "br2",
            "batchId": "b1",
            "workspaceId": "w1",
            "status": "pending",
            "testRunIds": ["t1"],
            "summary": {"total": 1, "pending": 1, "running": 0, "passed": 0, "failed": 0, "error": 0},
            "startedAt": "2026-11-12T09:00:00Z",
            "triggeredBy": "rerun",
            "parentBatchRunId": "br1",
            "createdBy": "u1",
        },
    )
    c = client()
    out = c.batches.rerun(
        "br1",
        filter="errors",
        members=[BatchMember(type="param", config_id="c1"), {"type": "mission", "configId": "m1"}],
    )
    assert json.loads(httpx_mock.get_requests()[0].content) == {
        "filter": "errors",
        "members": [
            {"type": "param", "configId": "c1"},
            {"type": "mission", "configId": "m1"},
        ],
    }
    assert out.id == "br2" and out.triggered_by == "rerun"
    assert out.parent_batch_run_id == "br1" and out.test_run_ids == ["t1"]
    c.close()


async def test_rerun_async_empty_body(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batch-runs/br1/rerun",
        method="POST",
        status_code=201,
        json={"id": "br2", "status": "pending"},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    out = await c.batches.rerun("br1", test_config_ids=["c1"])
    assert json.loads(httpx_mock.get_requests()[0].content) == {"testConfigIds": ["c1"]}
    assert out.status == "pending"
    await c.aclose()


def test_rerun_is_never_retried_by_default(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batch-runs/br1/rerun",
        method="POST",
        status_code=429,
        headers={"retry-after": "0"},
        json={"error": "rate"},
    )
    c = Nopaque(api_key="k", max_retries=3)
    with pytest.raises(RateLimitError):
        c.batches.rerun("br1")
    assert len(httpx_mock.get_requests()) == 1
    c.close()


def test_wait_for_run_stops_on_partial(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batch-runs/br1",
        json={"id": "br1", "status": "partial"},
    )
    c = client()
    out = c.batches.wait_for_run("br1", timeout=5, poll_interval=0.01)
    assert out.status == "partial"
    assert len(httpx_mock.get_requests()) == 1
    c.close()
