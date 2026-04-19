import pytest
from pytest_httpx import HTTPXMock
from nopaque import Nopaque


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
        json={"items": [{"id": "b1", "name": "UK"}], "nextToken": None},
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
        json={"batchId": "b1", "runId": "r1", "status": "running"},
    )
    c = client()
    r = c.batches.run("b1")
    assert r.run_id == "r1"
    c.close()


def test_runs(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batches/b1/runs",
        json={"items": [{"runId": "r1", "status": "completed"}], "nextToken": None},
    )
    c = client()
    out = list(c.batches.runs("b1"))
    assert out[0].run_id == "r1"
    c.close()


def test_list_runs(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batch-runs",
        json={"items": [{"runId": "r1", "batchId": "b1", "status": "completed"}], "nextToken": None},
    )
    c = client()
    out = list(c.batches.list_runs())
    assert out[0].run_id == "r1"
    c.close()


def test_get_run(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/batch-runs/r1",
        json={"runId": "r1", "batchId": "b1", "status": "completed", "passRate": 0.9},
    )
    c = client()
    r = c.batches.get_run("r1")
    assert r.pass_rate == 0.9
    c.close()


def test_wait_for_run(httpx_mock: HTTPXMock):
    for status in ("running", "completed"):
        httpx_mock.add_response(
            url="https://api.nopaque.co.uk/testing/batch-runs/r1",
            json={"runId": "r1", "status": status},
        )
    c = client()
    run = c.batches.wait_for_run("r1", timeout=5.0, poll_interval=0.01)
    assert run.status == "completed"
    c.close()
