import pytest
from pytest_httpx import HTTPXMock

from nopaque import Nopaque
from nopaque._errors import NopaqueTimeoutError


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_create_mapping_sends_expected_body(httpx_mock: HTTPXMock):
    from nopaque.models.mapping import MappingJobConfig

    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping",
        method="POST",
        json={
            "id": "map_1",
            "name": "Main IVR",
            "phoneNumber": "+441234567890",
            "config": {"mappingMode": "dtmf"},
            "status": "idle",
        },
    )
    c = client()
    job = c.mapping.create(
        name="Main IVR",
        phone_number="+441234567890",
        config=MappingJobConfig(mapping_mode="dtmf"),
    )
    assert job.id == "map_1"
    assert job.name == "Main IVR"
    req = httpx_mock.get_requests()[0]
    import json as _j
    assert _j.loads(req.content) == {
        "name": "Main IVR",
        "phoneNumber": "+441234567890",
        "config": {"mappingMode": "dtmf"},
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
        json={"jobId": "map_1", "runs": [{"id": "r1", "jobId": "map_1", "status": "completed"}], "totalRuns": 1},
    )
    c = client()
    runs = list(c.mapping.runs("map_1"))
    assert runs[0].id == "r1"
    c.close()


def test_paths_and_update_and_delete(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/paths",
        json={"jobId": "map_1", "rules": [{"jobId": "map_1", "path": "1>2", "status": "completed"}], "totalRules": 1},
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


def test_probe_returns_queue_summary(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/runs/r_1/probe",
        method="POST",
        json={"message": "Queued 3 security probe steps", "probeCount": 3},
    )
    c = client()
    result = c.mapping.probe("map_1", "r_1")
    assert result.probe_count == 3
    assert "Queued" in result.message
    req = httpx_mock.get_requests()[0]
    assert req.url.path == "/mapping/map_1/runs/r_1/probe"
    assert req.method == "POST"
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


# --- v0.3.0: tags, filters, currentRun, telemetry, tree enrichment ---

def test_create_with_tags_sends_tags(httpx_mock: HTTPXMock):
    from nopaque.models.mapping import MappingJobConfig

    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping",
        method="POST",
        json={"id": "map_1", "name": "x", "status": "idle", "tags": ["compliance-eu"]},
    )
    c = client()
    job = c.mapping.create(
        name="x",
        phone_number="+441",
        config=MappingJobConfig(mapping_mode="dtmf"),
        tags=["compliance-eu"],
    )
    assert job.tags == ["compliance-eu"]
    import json as _j
    body = _j.loads(httpx_mock.get_requests()[0].content)
    assert body["tags"] == ["compliance-eu"]
    c.close()


def test_update_with_tags_sends_tags(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1",
        method="PATCH",
        json={"id": "map_1", "name": "x", "status": "idle", "tags": ["a", "b"]},
    )
    c = client()
    job = c.mapping.update("map_1", tags=["a", "b"])
    assert job.tags == ["a", "b"]
    import json as _j
    assert _j.loads(httpx_mock.get_requests()[0].content) == {"tags": ["a", "b"]}
    c.close()


def test_list_sends_filters_and_returns_slim_items(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping?status=completed&tag=compliance-eu&phoneNumber=%2B441&limit=10&sortDir=asc",
        json={
            "items": [
                {"id": "map_1", "name": "a", "status": "completed", "tags": ["compliance-eu"], "runNumber": 2}
            ],
            "nextCursor": None,
        },
    )
    c = client()
    jobs = list(
        c.mapping.list(
            status="completed",
            tag="compliance-eu",
            phone_number="+441",
            limit=10,
            sort_dir="asc",
        )
    )
    assert [j.id for j in jobs] == ["map_1"]
    assert jobs[0].run_number == 2
    assert jobs[0].tags == ["compliance-eu"]
    c.close()


def test_list_paginates_on_next_cursor(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping",
        json={"items": [{"id": "map_1", "name": "a", "status": "idle"}], "nextCursor": "CUR2"},
    )
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping?cursor=CUR2",
        json={"items": [{"id": "map_2", "name": "b", "status": "idle"}], "nextCursor": None},
    )
    c = client()
    ids = [j.id for j in c.mapping.list()]
    assert ids == ["map_1", "map_2"]
    # Second request carried the cursor forwarded from nextCursor.
    assert "cursor=CUR2" in str(httpx_mock.get_requests()[1].url)
    c.close()


def test_get_exposes_run_number_and_current_run(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1",
        json={
            "id": "map_1",
            "name": "x",
            "status": "running",
            "runNumber": 3,
            "currentRun": {
                "id": "run_3",
                "status": "completed",
                "runNumber": 3,
                "stats": {"totalCalls": 5},
            },
        },
    )
    c = client()
    job = c.mapping.get("map_1")
    assert job.run_number == 3
    assert job.current_run is not None
    assert job.current_run.status == "completed"
    assert job.current_run.run_number == 3
    c.close()


def test_tree_empty_state_envelope(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/tree?format=tree",
        json={
            "jobId": "map_1",
            "status": "idle",
            "tree": None,
            "reason": "no_runs",
            "message": "This job has not been run yet.",
        },
    )
    c = client()
    tree = c.mapping.tree("map_1")
    assert tree.tree is None
    assert tree.reason == "no_runs"
    assert "not been run" in (tree.message or "")
    c.close()


def test_tree_node_enrichment_fields(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/tree?format=tree",
        json={
            "jobId": "map_1",
            "runId": "r1",
            "runNumber": 2,
            "status": "completed",
            "tree": {
                "stepId": "s1",
                "depth": 0,
                "path": "/",
                "status": "completed",
                "isTerminal": False,
                "children": [],
                "stepType": "voice",
                "voicePrompt": "Welcome",
                "menuLabel": "greeting",
                "probeCategory": "social-engineering",
                "inputRequired": {"type": "pin", "description": "Enter PIN", "terminator": "#"},
            },
        },
    )
    c = client()
    tree = c.mapping.tree("map_1")
    assert tree.run_number == 2
    assert tree.tree is not None
    assert tree.tree.step_type == "voice"
    assert tree.tree.menu_label == "greeting"
    assert tree.tree.probe_category == "social-engineering"
    assert tree.tree.input_required is not None
    assert tree.tree.input_required.terminator == "#"
    c.close()


def test_call_telemetry_parses_permissively():
    from nopaque.models.mapping import CallTelemetry

    tel = CallTelemetry.model_validate(
        {
            "schemaVersion": 1,
            "telephony": {"callLegId": "abc", "unknownField": True},
            "turns": [{"schemaVersion": 1, "timing": {"durationMs": 100}}],
            "brandNewGroup": {"x": 1},
        }
    )
    assert tel.schema_version == 1
    assert tel.telephony == {"callLegId": "abc", "unknownField": True}
    assert tel.turns is not None
    assert tel.turns[0].timing == {"durationMs": 100}


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
