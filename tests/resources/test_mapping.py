import pytest
from pytest_httpx import HTTPXMock
from nopaque import Nopaque
from nopaque._errors import NopaqueTimeoutError


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_create_mapping_sends_expected_body(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping",
        method="POST",
        json={
            "id": "map_1",
            "name": "Main IVR",
            "phoneNumber": "+441234567890",
            "mappingMode": "dtmf",
            "status": "idle",
        },
    )
    c = client()
    job = c.mapping.create(
        name="Main IVR",
        phone_number="+441234567890",
        mapping_mode="dtmf",
    )
    assert job.id == "map_1"
    assert job.name == "Main IVR"
    req = httpx_mock.get_requests()[0]
    import json as _j
    assert _j.loads(req.content) == {
        "name": "Main IVR",
        "phoneNumber": "+441234567890",
        "mappingMode": "dtmf",
    }
    c.close()


def test_get_mapping(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1",
        json={"id": "map_1", "name": "x", "status": "running"},
    )
    c = client()
    job = c.mapping.get("map_1")
    assert job.status == "running"
    c.close()


def test_list_mapping_paginates(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping",
        json={"items": [{"id": "map_1", "name": "a", "status": "idle"}], "nextToken": None},
    )
    c = client()
    jobs = list(c.mapping.list())
    assert [j.id for j in jobs] == ["map_1"]
    c.close()


def test_update_mapping(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1",
        method="PATCH",
        json={"id": "map_1", "name": "new name", "status": "idle"},
    )
    c = client()
    job = c.mapping.update("map_1", name="new name")
    assert job.name == "new name"
    c.close()


def test_delete_mapping(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1",
        method="DELETE",
        json={"message": "ok"},
    )
    c = client()
    c.mapping.delete("map_1")
    c.close()


def test_start_mapping(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/start",
        method="POST",
        json={"id": "map_1", "runId": "run_1", "status": "running", "name": "x"},
    )
    c = client()
    job = c.mapping.start("map_1")
    assert job.status == "running"
    c.close()


def test_cancel_mapping(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/cancel",
        method="POST",
        json={"id": "map_1", "status": "cancelled", "name": "x"},
    )
    c = client()
    job = c.mapping.cancel("map_1")
    assert job.status == "cancelled"
    c.close()


def test_attest(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/attest",
        method="POST",
        json={"attested": True},
    )
    c = client()
    out = c.mapping.attest("map_1")
    assert out == {"attested": True}
    c.close()


def test_steps(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/steps",
        json={
            "items": [
                {"id": "s1", "jobId": "map_1", "runId": "r1", "depth": 0, "path": [], "pathString": "", "status": "completed"}
            ],
            "nextToken": None,
        },
    )
    c = client()
    steps = list(c.mapping.steps("map_1"))
    assert steps[0].id == "s1"
    c.close()


def test_tree_default_format(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/tree?format=tree",
        json={
            "jobId": "map_1",
            "runId": "r1",
            "status": "completed",
            "tree": {
                "stepId": "s1",
                "depth": 0,
                "path": "/",
                "status": "completed",
                "isTerminal": False,
                "children": [],
            },
        },
    )
    c = client()
    tree = c.mapping.tree("map_1")
    assert tree.job_id == "map_1"
    assert tree.tree is not None
    assert tree.tree.step_id == "s1"
    c.close()


def test_runs_paginates(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/runs",
        json={"items": [{"id": "r1", "jobId": "map_1", "status": "completed"}], "nextToken": None},
    )
    c = client()
    runs = list(c.mapping.runs("map_1"))
    assert runs[0].id == "r1"
    c.close()


def test_paths_and_update_and_delete(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/paths",
        json={"items": [{"jobId": "map_1", "path": "1>2", "status": "completed"}], "nextToken": None},
    )
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/paths/1%3E2",
        method="PATCH",
        json={"jobId": "map_1", "path": "1>2", "status": "completed"},
    )
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/paths/1%3E2",
        method="DELETE",
        json={"message": "ok"},
    )
    c = client()
    paths = list(c.mapping.paths("map_1"))
    assert paths[0].path == "1>2"
    p = c.mapping.update_path("map_1", "1>2", repeat_behavior="explore-once")
    assert p.path == "1>2"
    c.mapping.delete_path("map_1", "1>2")
    c.close()


def test_remap(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/remap/1%3E2",
        method="POST",
        json={"id": "map_1", "name": "x", "status": "running"},
    )
    c = client()
    c.mapping.remap("map_1", "1>2")
    c.close()


def test_wait_for_complete(httpx_mock: HTTPXMock):
    # Three polls: running, running, completed.
    for status in ("running", "running", "completed"):
        httpx_mock.add_response(
            url="https://api.nopaque.co.uk/mapping/map_1",
            json={"id": "map_1", "name": "x", "status": status},
        )
    c = client()
    job = c.mapping.wait_for_complete(
        "map_1", timeout=5.0, poll_interval=0.01,
    )
    assert job.status == "completed"
    c.close()


def test_wait_for_complete_times_out(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1",
        json={"id": "map_1", "name": "x", "status": "running"},
        is_reusable=True,
    )
    c = client()
    with pytest.raises(NopaqueTimeoutError):
        c.mapping.wait_for_complete(
            "map_1", timeout=0.05, poll_interval=0.02,
        )
    c.close()
