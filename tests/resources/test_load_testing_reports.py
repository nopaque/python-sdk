"""Tests for the load_testing report, export and failure-pattern methods."""
import json

from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque

BASE = "https://api.nopaque.co.uk"
RUN = "11111111-1111-1111-1111-111111111111"

REPORT = {
    "reportId": "r1",
    "name": "Peak",
    "kind": "load-test-runs",
    "loadTestRunIds": [RUN],
    "packs": ["data", "pdf"],
    "includeAudio": False,
    "status": "ready",
    "createdAt": "2026-11-12T09:00:00Z",
    "counts": {"runs": 1, "calls": 100, "steps": 400, "recordings": 0},
    "files": [
        {"pack": "pdf", "fileName": "peak.pdf", "sizeBytes": 1234, "contentType": "application/pdf"}
    ],
}

EXPORT = {
    "exportId": "e1",
    "runId": RUN,
    "status": "ready",
    "createdAt": "2026-11-12T09:00:00Z",
    "expiresAt": "2026-12-12T09:00:00Z",
    "counts": {"calls": 100, "steps": 400},
    "downloadUrl": "https://s3.example/e1.zip",
}


def client():
    return Nopaque(api_key="k", max_retries=0)


# ---- reports ----------------------------------------------------------------


def test_reports_create_body(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/reports",
        method="POST",
        status_code=202,
        json={"report": {**REPORT, "status": "pending", "files": []}},
    )
    c = client()
    out = c.load_testing.create_report(
        load_test_run_ids=[RUN], packs=["data", "pdf"], include_audio=False
    )
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {"loadTestRunIds": [RUN], "packs": ["data", "pdf"], "includeAudio": False}
    assert out.report_id == "r1" and out.status == "pending"
    c.close()


def test_reports_create_minimal_body(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/reports", method="POST", status_code=202, json={"report": REPORT}
    )
    c = client()
    c.load_testing.create_report(load_test_run_ids=[RUN], name="Peak")
    assert json.loads(httpx_mock.get_requests()[0].content) == {
        "loadTestRunIds": [RUN],
        "name": "Peak",
    }
    c.close()


def test_reports_list_follows_next_cursor(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/reports",
        json={"reports": [REPORT], "nextCursor": "c2"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/reports?cursor=c2",
        json={"reports": [{**REPORT, "reportId": "r2"}]},
    )
    c = client()
    out = list(c.load_testing.list_reports())
    assert [r.report_id for r in out] == ["r1", "r2"]
    assert out[0].files[0].file_name == "peak.pdf"
    assert out[0].counts is not None and out[0].counts.calls == 100
    c.close()


def test_reports_list_page(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/reports?limit=1&cursor=c1",
        json={"reports": [REPORT], "nextCursor": "c2"},
    )
    c = client()
    page = c.load_testing.list_reports_page(limit=1, cursor="c1")
    assert page.items[0].report_id == "r1"
    assert page.next_token == "c2"
    c.close()


def test_reports_get_delete_download(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/testing/reports/r1", json={"report": REPORT})
    httpx_mock.add_response(url=f"{BASE}/testing/reports/r1", method="DELETE", status_code=204)
    httpx_mock.add_response(
        url=f"{BASE}/testing/reports/r1/files/pdf",
        json={
            "url": "https://s3.example/peak.pdf",
            "fileName": "peak.pdf",
            "sizeBytes": 1234,
            "expiresAt": "2026-11-12T10:00:00Z",
        },
    )
    c = client()
    assert c.load_testing.get_report("r1").load_test_run_ids == [RUN]
    assert c.load_testing.delete_report("r1") is None
    dl = c.load_testing.get_report_file_url("r1", "pdf")
    assert dl.url == "https://s3.example/peak.pdf" and dl.size_bytes == 1234
    c.close()


# ---- exports ----------------------------------------------------------------


def test_exports(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/exports",
        method="POST",
        status_code=202,
        json={"export": {**EXPORT, "status": "pending", "downloadUrl": None}},
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/exports", json={"exports": [EXPORT]}
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/exports/e1", json={"export": EXPORT}
    )
    c = client()
    started = c.load_testing.create_export(RUN)
    assert started.status == "pending" and started.download_url is None
    listed = c.load_testing.list_exports(RUN)
    assert listed[0].export_id == "e1"
    got = c.load_testing.get_export(RUN, "e1")
    assert got.download_url == "https://s3.example/e1.zip"
    assert got.counts is not None and got.counts.steps == 400
    c.close()


# ---- failure patterns -------------------------------------------------------


def test_failure_patterns_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/failure-patterns?scope=lane",
        json={
            "runId": RUN,
            "groupId": None,
            "scope": "lane",
            "rulesVersion": 3,
            "totalCalls": 100,
            "failedCalls": 10,
            "unclassified": 1,
            "lateStarts": 2,
            "lateStartsPassed": 1,
            "patterns": [
                {
                    "id": "P2a",
                    "label": "No answer",
                    "owner": "carrier",
                    "description": "The call was never answered.",
                    "count": 9,
                    "share": 0.9,
                    "byLane": {RUN: 9},
                    "firstSeen": "2026-11-12T09:00:00Z",
                    "lastSeen": "2026-11-12T09:05:00Z",
                    "examples": [{"callId": "c1"}],
                }
            ],
            "timeline": {
                "bucketSecs": 15,
                "buckets": [{"t": "2026-11-12T09:00:00Z", "inFlight": 20, "counts": {"P2a": 3}}],
            },
            "lanes": [{"runId": RUN, "name": "Lane A"}],
        },
    )
    c = client()
    out = c.load_testing.get_failure_patterns(RUN, scope="lane")
    assert out.failed_calls == 10 and out.late_starts_passed == 1
    assert out.patterns[0].by_lane == {RUN: 9}
    assert out.timeline is not None and out.timeline.buckets[0].in_flight == 20
    assert out.lanes[0].name == "Lane A"
    c.close()


def test_failure_patterns_reclassify(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/failure-patterns/reclassify",
        method="POST",
        status_code=202,
        json={"jobId": "j1"},
    )
    c = client()
    assert c.load_testing.reclassify_failure_patterns(RUN).job_id == "j1"
    c.close()


def test_failure_patterns_list_calls_follows_cursor(httpx_mock: HTTPXMock):
    call = {
        "callId": "c1",
        "runId": RUN,
        "laneName": "Lane A",
        "startedAt": "2026-11-12T09:00:00Z",
        "failedStepIndex": 2,
        "failedStepName": "Menu",
        "evidence": {"sipCode": 480},
        "recordingAvailable": True,
    }
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/failure-patterns/P2a/calls?scope=group",
        json={"items": [call], "cursor": "next"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/failure-patterns/P2a/calls?scope=group&cursor=next",
        json={"items": [{**call, "callId": "c2"}]},
    )
    c = client()
    out = list(c.load_testing.list_failure_pattern_calls(RUN, "P2a", scope="group"))
    assert [x.call_id for x in out] == ["c1", "c2"]
    assert out[0].failed_step_index == 2 and out[0].evidence == {"sipCode": 480}
    c.close()


def test_failure_patterns_list_calls_page(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/failure-patterns/P1/calls?limit=1&cursor=abc",
        json={"items": [{"callId": "c9", "runId": RUN}], "cursor": "def"},
    )
    c = client()
    page = c.load_testing.list_failure_pattern_calls_page(RUN, "P1", limit=1, cursor="abc")
    assert page.items[0].call_id == "c9" and page.next_token == "def"
    c.close()


async def test_async_reports_exports_patterns(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/reports", method="POST", status_code=202, json={"report": REPORT}
    )
    httpx_mock.add_response(url=f"{BASE}/testing/reports", json={"reports": [REPORT]})
    httpx_mock.add_response(url=f"{BASE}/testing/reports?limit=5", json={"reports": [REPORT]})
    httpx_mock.add_response(url=f"{BASE}/testing/reports/r1", json={"report": REPORT})
    httpx_mock.add_response(url=f"{BASE}/testing/reports/r1", method="DELETE", status_code=204)
    httpx_mock.add_response(
        url=f"{BASE}/testing/reports/r1/files/data",
        json={"url": "u", "fileName": "d.zip", "sizeBytes": 1, "expiresAt": "t"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/exports",
        method="POST",
        json={"export": EXPORT},
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/exports", json={"exports": [EXPORT]}
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/exports/e1", json={"export": EXPORT}
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/failure-patterns",
        json={"runId": RUN, "patterns": [], "lanes": []},
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/failure-patterns/reclassify?scope=lane",
        method="POST",
        json={"jobId": "j1"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/failure-patterns/LATE_START/calls",
        json={"items": []},
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/load-tests/{RUN}/failure-patterns/LATE_START/calls?scope=lane",
        json={"items": []},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    lt = c.load_testing
    assert (await lt.create_report(load_test_run_ids=[RUN])).report_id == "r1"
    assert [r.report_id async for r in lt.list_reports()] == ["r1"]
    assert (await lt.list_reports_page(limit=5)).next_token is None
    assert (await lt.get_report("r1")).status == "ready"
    assert await lt.delete_report("r1") is None
    assert (await lt.get_report_file_url("r1", "data")).file_name == "d.zip"
    assert (await lt.create_export(RUN)).export_id == "e1"
    assert len(await lt.list_exports(RUN)) == 1
    assert (await lt.get_export(RUN, "e1")).status == "ready"
    assert (await lt.get_failure_patterns(RUN)).patterns == []
    assert (await lt.reclassify_failure_patterns(RUN, scope="lane")).job_id == "j1"
    assert [x async for x in lt.list_failure_pattern_calls(RUN, "LATE_START")] == []
    page = await lt.list_failure_pattern_calls_page(RUN, "LATE_START", scope="lane")
    assert page.items == [] and page.next_token is None
    await c.aclose()
