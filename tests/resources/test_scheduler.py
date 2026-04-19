from pytest_httpx import HTTPXMock

from nopaque import Nopaque


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_create(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/schedules",
        method="POST",
        json={"id": "s1", "name": "Daily", "cronExpression": "0 9 * * *"},
    )
    c = client()
    out = c.scheduler.create(name="Daily", config_id="c1", cron_expression="0 9 * * *")
    assert out.id == "s1"
    c.close()


def test_list(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/schedules",
        json={"schedules": [{"id": "s1", "name": "Daily"}], "count": 1},
    )
    c = client()
    out = list(c.scheduler.list())
    assert out[0].id == "s1"
    c.close()


def test_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/schedules/s1",
        json={"id": "s1", "nextRunAt": "2026-04-11T09:00:00Z"},
    )
    c = client()
    out = c.scheduler.get("s1")
    assert out.next_run_at == "2026-04-11T09:00:00Z"
    c.close()


def test_update(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/schedules/s1",
        method="PUT",
        json={"id": "s1", "cronExpression": "0 8 * * *"},
    )
    c = client()
    out = c.scheduler.update("s1", cron_expression="0 8 * * *")
    assert out.cron_expression == "0 8 * * *"
    c.close()


def test_delete(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/schedules/s1",
        method="DELETE",
        json={"message": "ok"},
    )
    c = client()
    c.scheduler.delete("s1")
    c.close()


def test_pause(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/schedules/s1/pause",
        method="POST",
        json={"id": "s1", "status": "paused"},
    )
    c = client()
    out = c.scheduler.pause("s1")
    assert out.status == "paused"
    c.close()


def test_resume(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/schedules/s1/resume",
        method="POST",
        json={"id": "s1", "status": "active"},
    )
    c = client()
    out = c.scheduler.resume("s1")
    assert out.status == "active"
    c.close()
