from pytest_httpx import HTTPXMock

from nopaque import Nopaque


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
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/configs",
        json={"items": [{"id": "cfg_1", "name": "T1"}], "nextToken": None},
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
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/jobs",
        json={"items": [{"id": "job_1", "status": "completed"}], "nextToken": None},
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

def test_runs_create(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs",
        method="POST",
        json={"runId": "r1", "jobId": "job_1", "status": "running"},
    )
    c = client()
    run = c.testing.runs.create(job_id="job_1")
    assert run.run_id == "r1"
    c.close()


def test_runs_list(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs",
        json={"items": [{"runId": "r1", "status": "completed"}], "nextToken": None},
    )
    c = client()
    out = list(c.testing.runs.list())
    assert out[0].run_id == "r1"
    c.close()


def test_runs_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/runs/r1",
        json={"runId": "r1", "status": "completed", "result": "pass"},
    )
    c = client()
    run = c.testing.runs.get("r1")
    assert run.result == "pass"
    c.close()


def test_wait_for_run(httpx_mock: HTTPXMock):
    for status in ("running", "completed"):
        httpx_mock.add_response(
            url="https://api.nopaque.co.uk/testing/runs/r1",
            json={"runId": "r1", "status": status},
        )
    c = client()
    run = c.testing.runs.wait_for_run("r1", timeout=5.0, poll_interval=0.01)
    assert run.status == "completed"
    c.close()
