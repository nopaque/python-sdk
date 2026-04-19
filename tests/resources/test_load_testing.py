import pytest
from pytest_httpx import HTTPXMock
from nopaque import Nopaque


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_create(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/load-tests",
        method="POST",
        json={"id": "lt1", "name": "Peak", "concurrency": 10, "totalCalls": 100},
    )
    c = client()
    out = c.load_testing.create(name="Peak", config_id="c1", concurrency=10, total_calls=100)
    assert out.id == "lt1"
    c.close()


def test_list(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/load-tests",
        json={"items": [{"id": "lt1", "name": "Peak"}], "nextToken": None},
    )
    c = client()
    out = list(c.load_testing.list())
    assert out[0].id == "lt1"
    c.close()


def test_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/load-tests/lt1",
        json={"id": "lt1", "name": "Peak"},
    )
    c = client()
    out = c.load_testing.get("lt1")
    assert out.id == "lt1"
    c.close()


def test_update(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/load-tests/lt1",
        method="PUT",
        json={"id": "lt1", "name": "Peak", "concurrency": 20},
    )
    c = client()
    out = c.load_testing.update("lt1", concurrency=20)
    assert out.concurrency == 20
    c.close()


def test_delete(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/load-tests/lt1",
        method="DELETE",
        json={"message": "ok"},
    )
    c = client()
    c.load_testing.delete("lt1")
    c.close()


def test_estimate(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/load-tests/estimate",
        method="POST",
        json={"estimatedMinutes": 15.5, "estimatedCost": "$4.65"},
    )
    c = client()
    est = c.load_testing.estimate(config_id="c1", concurrency=10, total_calls=100)
    assert est.estimated_minutes == 15.5
    c.close()


def test_start(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/load-tests/lt1/start",
        method="POST",
        json={"id": "lt1", "runId": "r1", "status": "running", "name": "Peak"},
    )
    c = client()
    out = c.load_testing.start("lt1")
    assert out.status == "running"
    c.close()


def test_abort(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/load-tests/lt1/abort",
        method="POST",
        json={"id": "lt1", "status": "aborted", "name": "Peak"},
    )
    c = client()
    out = c.load_testing.abort("lt1")
    assert out.status == "aborted"
    c.close()


def test_status(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/load-tests/lt1/status",
        json={
            "id": "lt1",
            "status": "running",
            "progress": {"completedCalls": 45, "totalCalls": 100, "passRate": 0.93},
        },
    )
    c = client()
    s = c.load_testing.status("lt1")
    assert s.status == "running"
    assert s.progress.completed_calls == 45
    c.close()


def test_list_runs(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/load-tests/runs",
        json={"items": [{"runId": "r1", "loadTestId": "lt1", "status": "completed"}], "nextToken": None},
    )
    c = client()
    out = list(c.load_testing.list_runs())
    assert out[0].run_id == "r1"
    c.close()


def test_wait_for_complete(httpx_mock: HTTPXMock):
    for status in ("running", "completed"):
        httpx_mock.add_response(
            url="https://api.nopaque.co.uk/testing/load-tests/lt1/status",
            json={"id": "lt1", "status": status},
        )
    c = client()
    s = c.load_testing.wait_for_complete("lt1", timeout=5.0, poll_interval=0.01)
    assert s.status == "completed"
    c.close()
