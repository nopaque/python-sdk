"""Parse the responses the API actually sends.

Each fixture in ``tests/fixtures/api_responses/`` is built from the api
handler code (nopaque/api main, 12 November 2026), not from the OpenAPI
document, which disagrees with the handlers in places. Every endpoint here
either raised a ``ValidationError`` or returned empty fields in 0.14.0.
"""
import json
from pathlib import Path
from typing import Any, Dict

import pytest
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "api_responses"
BASE = "https://api.nopaque.co.uk"


def fixture(name: str) -> Dict[str, Any]:
    with open(FIXTURES / f"{name}.json", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    return data


def client() -> Nopaque:
    return Nopaque(api_key="k", max_retries=0)


# ---- compliance -------------------------------------------------------------


def test_compliance_catalogue_parses_the_real_response(httpx_mock: HTTPXMock):
    body = fixture("compliance_catalogue")
    httpx_mock.add_response(url=f"{BASE}/testing/compliance-catalogue", json=body)
    c = client()
    r = c.compliance.get_catalogue()

    assert isinstance(r.catalogue.version, int)
    assert r.catalogue.version == body["catalogue"]["version"]
    # `regulations` is a map keyed by regulation key.
    assert set(r.catalogue.regulations) == set(body["catalogue"]["regulations"])
    ai_act = r.catalogue.regulations["eu-ai-act"]
    assert ai_act.name == "EU Artificial Intelligence Act"
    assert ai_act.full_ref == "Regulation (EU) 2024/1689"
    assert ai_act.in_force_phases and ai_act.in_force_phases[0].date == "2025-02-02"

    first = r.catalogue.tests[0]
    raw_first = body["catalogue"]["tests"][0]
    assert first.id == raw_first["id"]
    assert first.name == raw_first["name"]
    assert first.summary == raw_first["summary"]
    assert first.pass_ == raw_first["pass"]
    assert first.fail == raw_first["fail"]
    assert first.probe_count == raw_first["probeCount"]
    assert first.covers[0].regulation == raw_first["covers"][0]["regulation"]
    assert first.covers[0].weight == raw_first["covers"][0]["weight"]
    assert first.regulation_keys == [cv["regulation"] for cv in raw_first["covers"]]

    assert r.picker_limit == 3
    assert r.compliance_seconds_available == 540
    assert r.tier == "free"
    c.close()


def test_compliance_catalogue_paid_tier_has_no_local_seconds(httpx_mock: HTTPXMock):
    body = fixture("compliance_catalogue")
    body["complianceSecondsAvailable"] = None
    body["tier"] = "team"
    httpx_mock.add_response(url=f"{BASE}/testing/compliance-catalogue", json=body)
    c = client()
    r = c.compliance.get_catalogue()
    assert r.compliance_seconds_available is None
    c.close()


def test_compliance_report_parses_the_real_response(httpx_mock: HTTPXMock):
    body = fixture("compliance_report")
    httpx_mock.add_response(
        url=f"{BASE}/testing/compliance-reports/%2B441234567890", json=body
    )
    c = client()
    r = c.compliance.get_report("+441234567890")

    assert r.phone_number == "+441234567890"
    assert r.workspace_id == "ws_3f9a"
    assert r.catalogue_version == body["catalogueVersion"]
    assert (r.summary.ran, r.summary.passed, r.summary.failed, r.summary.total) == (2, 1, 1, 3)

    ai_act = next(s for s in r.regulations if s.key == "eu-ai-act")
    assert ai_act.name == "EU Artificial Intelligence Act"
    assert ai_act.summary.ran == 2
    row = ai_act.tests[0]
    assert row.primary_for is True
    assert row.clauses
    assert row.last_run is not None
    assert row.last_run.verdict == "pass"
    assert row.last_run.pass_evidence and row.last_run.pass_evidence[0].met is True
    assert row.last_run.catalogue_version == body["catalogueVersion"]

    failed = next(t for s in r.regulations for t in s.tests if t.last_run and t.last_run.verdict == "fail")
    assert failed.last_run is not None
    assert failed.last_run.channel == "chat"
    assert failed.last_run.pass_rate == 0.25
    assert failed.last_run.fail_evidence and failed.last_run.fail_evidence[0].triggered is True

    untested = next(t for s in r.regulations for t in s.tests if t.last_run is None)
    assert untested.last_run is None

    assert r.metadata is not None
    assert r.metadata.display_name == "Acme Bank main line"
    assert r.metadata.additional_context is None
    c.close()


def test_compliance_rerun_returns_the_new_run_id(httpx_mock: HTTPXMock):
    body = fixture("compliance_rerun")
    httpx_mock.add_response(
        url=f"{BASE}/testing/compliance-runs/r1/rerun", method="POST", json=body
    )
    c = client()
    r = c.compliance.rerun("r1")
    assert r.run_id == body["runId"]
    c.close()


async def test_compliance_async_methods_parse_the_real_responses(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/compliance-catalogue", json=fixture("compliance_catalogue")
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/compliance-reports/%2B441234567890",
        json=fixture("compliance_report"),
    )
    httpx_mock.add_response(
        url=f"{BASE}/testing/compliance-runs/r1/rerun",
        method="POST",
        json=fixture("compliance_rerun"),
    )
    async with AsyncNopaque(api_key="k", max_retries=0) as c:
        cat = await c.compliance.get_catalogue()
        report = await c.compliance.get_report("+441234567890")
        rerun = await c.compliance.rerun("r1")
    assert "eu-ai-act" in cat.catalogue.regulations
    assert report.summary.total == 3
    assert rerun.run_id


# ---- mission tests ----------------------------------------------------------


def test_mission_test_defaults_parses_the_sector_catalogue(httpx_mock: HTTPXMock):
    body = fixture("mission_test_defaults")
    httpx_mock.add_response(url=f"{BASE}/testing/mission-tests/defaults", json=body)
    c = client()
    r = c.mission_tests.get_defaults()
    assert r.schema_version == 1
    assert [s.id for s in r.sectors] == [s["id"] for s in body["sectors"]]
    mission = r.sectors[0].missions[0]
    raw = body["sectors"][0]["missions"][0]
    assert mission.id == raw["id"]
    assert mission.label == raw["label"]
    assert mission.default_acceptance == raw["defaultAcceptance"]
    c.close()


async def test_mission_test_defaults_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/testing/mission-tests/defaults", json=fixture("mission_test_defaults")
    )
    async with AsyncNopaque(api_key="k", max_retries=0) as c:
        r = await c.mission_tests.get_defaults()
    assert r.sectors


# ---- mapping ----------------------------------------------------------------


def test_mapping_tree_paths_are_lists(httpx_mock: HTTPXMock):
    body = fixture("mapping_tree")
    httpx_mock.add_response(url=f"{BASE}/mapping/job_9c2e/tree?format=tree", json=body)
    c = client()
    r = c.mapping.tree("job_9c2e")
    assert r.tree is not None
    assert r.tree.path == []
    assert r.tree.children[0].path == ["1"]
    assert r.tree.children[0].input_required is not None
    assert r.tree.children[0].input_required.start_time_ms == 4200
    # voice-agent turns carry stepType 's2s_node'
    assert r.tree.children[1].step_type == "s2s_node"
    assert r.tree.children[1].menu_label == "loan_enquiry"
    assert r.stats is not None and r.stats.total_calls == 3
    c.close()


def test_mapping_steps_fill_step_id_from_id(httpx_mock: HTTPXMock):
    body = fixture("mapping_steps")
    httpx_mock.add_response(url=f"{BASE}/mapping/job_9c2e/steps", json=body)
    c = client()
    steps = list(c.mapping.steps("job_9c2e"))
    assert len(steps) == 1
    step = steps[0]
    assert step.id == "step_1"
    assert step.step_id == "step_1"
    assert step.path == ["1"]
    assert step.path_string == "1"
    assert step.result is not None
    assert step.result.dtmf_options[0].label == "report a lost card"
    c.close()


# ---- enrichment -------------------------------------------------------------


def test_enrichment_get_completed_is_unwrapped(httpx_mock: HTTPXMock):
    body = fixture("enrichment_completed")
    httpx_mock.add_response(
        url=f"{BASE}/mapping/job_9c2e/runs/run_41aa/enrichments/quality_scoring", json=body
    )
    c = client()
    r = c.enrichment.get("job_9c2e", "run_41aa", "quality_scoring")
    assert r.status == "completed"
    assert r.job_id == "job_9c2e"
    assert r.run_id == "run_41aa"
    assert r.type == "quality_scoring"
    assert r.results is not None
    assert r.results["overallScore"] == 72
    assert r.results["dimensions"][0]["key"] == "clarity"
    # The unwrapped fields stay readable at the top level, as in 0.14.0.
    assert r.model_dump()["overallScore"] == 72
    c.close()


def test_enrichment_get_not_completed_returns_the_record(httpx_mock: HTTPXMock):
    body = fixture("enrichment_failed")
    httpx_mock.add_response(
        url=f"{BASE}/mapping/job_9c2e/runs/run_41aa/enrichments/quality_scoring", json=body
    )
    c = client()
    r = c.enrichment.get("job_9c2e", "run_41aa", "quality_scoring")
    assert r.status == "failed"
    assert r.enrichment_id == "enr_5d1c"
    assert r.enrichment_type == "quality_scoring"
    assert r.type == "quality_scoring"
    assert r.error == "llm-gateway returned 503"
    assert r.completed_at == "2026-11-10T10:05:00.000Z"
    assert r.results is None
    c.close()


def test_enrichment_token_usage_parses_services_and_total(httpx_mock: HTTPXMock):
    body = fixture("enrichment_token_usage")
    httpx_mock.add_response(
        url=f"{BASE}/mapping/job_9c2e/runs/run_41aa/token-usage", json=body
    )
    c = client()
    r = c.enrichment.token_usage("job_9c2e", "run_41aa")
    assert r.run_id == "run_41aa"
    assert r.job_id == "job_9c2e"
    assert r.total is not None and r.total.total_tokens == 19435
    assert r.services["ivr_analysis"].event_count == 3
    assert r.services["quality_scoring"].input_tokens == 5123
    # `usage` (the 0.14.0 field) is now filled from the same numbers.
    assert r.usage is not None
    assert r.usage.ivr_analysis_tokens == 13500
    assert r.usage.quality_scoring_tokens == 5935
    assert r.usage.total_tokens == 19435
    c.close()


async def test_enrichment_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/mapping/job_9c2e/runs/run_41aa/enrichments/quality_scoring",
        json=fixture("enrichment_completed"),
    )
    httpx_mock.add_response(
        url=f"{BASE}/mapping/job_9c2e/runs/run_41aa/token-usage",
        json=fixture("enrichment_token_usage"),
    )
    async with AsyncNopaque(api_key="k", max_retries=0) as c:
        e = await c.enrichment.get("job_9c2e", "run_41aa", "quality_scoring")
        u = await c.enrichment.token_usage("job_9c2e", "run_41aa")
    assert e.results is not None and e.results["overallScore"] == 72
    assert e.job_id == "job_9c2e"
    assert u.total is not None and u.total.total_tokens == 19435


# ---- load testing -----------------------------------------------------------


def test_load_test_status_parses_progress_and_stats(httpx_mock: HTTPXMock):
    body = fixture("load_test_status")
    httpx_mock.add_response(url=f"{BASE}/testing/load-tests/ltr_8e21/status", json=body)
    c = client()
    r = c.load_testing.status("ltr_8e21")
    assert r.status == "running"
    assert r.current_second == 90
    assert r.total_seconds == 300
    assert r.progress_percent == 30
    assert r.stats is not None
    assert (r.stats.started, r.stats.completed, r.stats.failed, r.stats.errors) == (42, 30, 4, 1)
    assert r.stats.p95 == 58.9
    assert r.stats.quality is not None and r.stats.quality.poor_calls == 2
    assert r.stats.patterns == {"no_answer": 3, "dtmf_not_recognised": 1}
    assert r.load_test_config_id == "ltc_7"
    assert r.started_at == "2026-11-10T11:00:00.000Z"
    c.close()


# ---- sweeps -----------------------------------------------------------------


@pytest.mark.parametrize("method", ["get_run"])
def test_sweep_run_parses_summary_and_test_runs(httpx_mock: HTTPXMock, method: str):
    body = fixture("sweep_run")
    httpx_mock.add_response(url=f"{BASE}/testing/sweep-runs/swr_3b9f", json=body)
    c = client()
    r = getattr(c.sweeps, method)("swr_3b9f")
    assert r.status == "partial"
    assert r.summary is not None
    assert (r.summary.total, r.summary.passed, r.summary.failed) == (2, 1, 1)
    assert r.test_run_ids == ["tr_1", "tr_2"]
    assert r.test_runs is not None
    assert [t.outcome for t in r.test_runs] == ["PASS", "FAIL"]
    assert r.test_runs[0].profile_id == "prof_a"
    assert r.triggered_by == "manual"
    c.close()


# ---- audio ------------------------------------------------------------------


def test_audio_create_upload_url_sends_metadata(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/audio/upload-url",
        method="POST",
        json={
            "audioId": "aud_1",
            "uploadUrl": "https://example-bucket.s3.amazonaws.com/put",
            "s3Key": "audio/voice/ws/aud_1/hello.wav",
            "expiresIn": 900,
        },
    )
    c = client()
    c.audio.create_upload_url(
        filename="hello.wav",
        content_type="audio/wav",
        category="voice",
        size_bytes=1024,
        metadata={"displayName": "Hello"},
    )
    sent = json.loads(httpx_mock.get_requests()[0].content)
    assert sent["metadata"] == {"displayName": "Hello"}
    c.close()


def test_audio_create_upload_url_omits_metadata_by_default(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/audio/upload-url",
        method="POST",
        json={"audioId": "aud_1", "uploadUrl": "u", "s3Key": "k", "expiresIn": 900},
    )
    c = client()
    c.audio.create_upload_url(
        filename="hello.wav", content_type="audio/wav", category="voice", size_bytes=1
    )
    assert "metadata" not in json.loads(httpx_mock.get_requests()[0].content)
    c.close()


def test_mapping_step_keeps_an_explicit_step_id():
    from nopaque import MappingStep

    by_alias = MappingStep.model_validate({"id": "row_1", "stepId": "step_1", "status": "completed"})
    by_name = MappingStep(id="row_1", step_id="step_1", status="completed")
    assert by_alias.step_id == "step_1"
    assert by_name.step_id == "step_1"


def test_token_usage_summary_accepts_field_names():
    from nopaque import TokenUsage

    u = TokenUsage.model_validate(
        {
            "run_id": "r",
            "services": {"ivr_analysis": {"total_tokens": 5}},
            "total": {"total_tokens": 12},
        }
    )
    assert u.usage is not None
    assert u.usage.ivr_analysis_tokens == 5
    assert u.usage.total_tokens == 12
