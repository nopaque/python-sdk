from pytest_httpx import HTTPXMock

from nopaque import Nopaque


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_get(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/runs/run_1/enrichments/quality_scoring",
        json={
            "jobId": "map_1",
            "runId": "run_1",
            "type": "quality_scoring",
            "status": "completed",
            "results": {"overallScore": 78},
        },
    )
    c = client()
    res = c.enrichment.get("map_1", "run_1", "quality_scoring")
    assert res.type == "quality_scoring"
    assert res.results["overallScore"] == 78
    c.close()


def test_token_usage(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/runs/run_1/token-usage",
        json={
            "jobId": "map_1",
            "runId": "run_1",
            "usage": {"ivrAnalysisTokens": 4520, "totalTokens": 5800},
        },
    )
    c = client()
    u = c.enrichment.token_usage("map_1", "run_1")
    assert u.usage.total_tokens == 5800
    c.close()


def test_enrich(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/mapping/map_1/runs/run_1/enrich",
        method="POST",
        json={
            "jobId": "map_1",
            "runId": "run_1",
            "status": "queued",
            "enrichmentTypes": ["quality_scoring"],
        },
    )
    c = client()
    out = c.enrichment.enrich("map_1", "run_1")
    assert out.status == "queued"
    assert out.enrichment_types == ["quality_scoring"]
    c.close()
