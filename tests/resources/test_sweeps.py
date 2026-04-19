from pytest_httpx import HTTPXMock

from nopaque import Nopaque


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_create(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/sweeps",
        method="POST",
        json={"id": "s1", "name": "X", "configId": "c1"},
    )
    c = client()
    out = c.sweeps.create(name="X", config_id="c1", parameters={"a": ["1", "2"]})
    assert out.id == "s1"
    c.close()


def test_list(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/sweeps",
        json={"sweeps": [{"id": "s1", "name": "X"}]},
    )
    c = client()
    out = list(c.sweeps.list())
    assert out[0].id == "s1"
    c.close()


def test_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/sweeps/s1",
        json={"id": "s1", "name": "X"},
    )
    c = client()
    out = c.sweeps.get("s1")
    assert out.id == "s1"
    c.close()


def test_update(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/sweeps/s1",
        method="PUT",
        json={"id": "s1", "name": "Y"},
    )
    c = client()
    out = c.sweeps.update("s1", name="Y")
    assert out.name == "Y"
    c.close()


def test_delete(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/sweeps/s1",
        method="DELETE",
        json={"message": "ok"},
    )
    c = client()
    c.sweeps.delete("s1")
    c.close()


def test_run(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/sweeps/s1/run",
        method="POST",
        json={"sweepId": "s1", "id": "r1", "status": "running"},
    )
    c = client()
    r = c.sweeps.run("s1")
    assert r.id == "r1"
    c.close()


def test_runs(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/sweeps/s1/runs",
        json={"runs": [{"id": "r1", "status": "completed"}]},
    )
    c = client()
    out = list(c.sweeps.runs("s1"))
    assert out[0].id == "r1"
    c.close()


def test_list_runs(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/sweep-runs",
        json={"runs": [{"id": "r1", "sweepId": "s1", "status": "completed"}]},
    )
    c = client()
    out = list(c.sweeps.list_runs())
    assert out[0].id == "r1"
    c.close()


def test_get_run(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/sweep-runs/r1",
        json={"id": "r1", "status": "completed", "passRate": 0.5},
    )
    c = client()
    r = c.sweeps.get_run("r1")
    assert r.pass_rate == 0.5
    c.close()


def test_wait_for_run(httpx_mock: HTTPXMock):
    for status in ("running", "completed"):
        httpx_mock.add_response(
            url="https://api.nopaque.co.uk/testing/sweep-runs/r1",
            json={"id": "r1", "status": status},
        )
    c = client()
    run = c.sweeps.wait_for_run("r1", timeout=5.0, poll_interval=0.01)
    assert run.status == "completed"
    c.close()
