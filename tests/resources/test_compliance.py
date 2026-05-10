"""Tests for the compliance resource."""
import json

import pytest
from pytest_httpx import HTTPXMock

from nopaque import Nopaque, NopaqueAPIError, NotFoundError


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_get_catalogue(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/compliance-catalogue",
        json={
            "catalogue": {"version": "v1", "regulations": [], "tests": []},
            "pickerLimit": 50,
            "s2stestSecondsAvailable": 600,
            "tier": "pro",
        },
    )
    c = client()
    r = c.compliance.get_catalogue()
    assert r.catalogue.version == "v1"
    assert r.picker_limit == 50
    c.close()


def test_run_dispatches_a_batch(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/compliance-runs",
        method="POST",
        json={
            "runIds": ["r1", "r2"],
            "reportUrl": "/testing/compliance-reports/%2B441234",
        },
    )
    c = client()
    r = c.compliance.run(
        phone_number="+441234",
        sector="insurance",
        test_ids=["M-001", "M-002"],
    )
    assert r.run_ids == ["r1", "r2"]
    req = httpx_mock.get_requests()[0]
    assert json.loads(req.content) == {
        "phoneNumber": "+441234",
        "sector": "insurance",
        "testIds": ["M-001", "M-002"],
    }
    c.close()


def test_run_surfaces_batch_size_exceeds_tier(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/compliance-runs",
        method="POST",
        status_code=402,
        json={"error": "too many", "code": "BATCH_SIZE_EXCEEDS_TIER"},
    )
    c = client()
    with pytest.raises(NopaqueAPIError) as exc:
        c.compliance.run(
            phone_number="+441234",
            sector="insurance",
            test_ids=["M-001"] * 100,
        )
    assert exc.value.code == "BATCH_SIZE_EXCEEDS_TIER"
    c.close()


def test_list_reports_paginates(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/compliance-reports",
        json={
            "items": [
                {
                    "phoneNumber": "+441234",
                    "passed": 2,
                    "failed": 3,
                    "total": 5,
                    "lastRunAt": "",
                }
            ],
            "nextToken": None,
        },
    )
    c = client()
    out = [r.phone_number for r in c.compliance.list_reports()]
    assert out == ["+441234"]
    c.close()


def test_get_report_url_encodes_phone_number(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/compliance-reports/%2B441234",
        json={
            "summary": {
                "phoneNumber": "+441234",
                "catalogueVersion": "v1",
                "passed": 2,
                "failed": 3,
                "pending": 0,
                "generatedAt": "",
            },
            "sections": [],
        },
    )
    c = client()
    r = c.compliance.get_report("+441234")
    assert r.summary.phone_number == "+441234"
    req = httpx_mock.get_requests()[0]
    # httpx decodes url.path; the encoded form is preserved in raw_path / str(url).
    assert "/testing/compliance-reports/%2B441234" in str(req.url)
    c.close()


def test_get_report_unknown_number_raises_not_found(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/compliance-reports/%2B449999999",
        status_code=404,
        json={"error": "not found"},
    )
    c = client()
    with pytest.raises(NotFoundError):
        c.compliance.get_report("+449999999")
    c.close()


def test_generate_pdf_url(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/compliance-reports/%2B441234/pdf",
        method="POST",
        json={"url": "https://s3/...presigned"},
    )
    c = client()
    r = c.compliance.generate_pdf_url("+441234", regulation_key="eu-ai-act")
    assert "presigned" in r.url
    req = httpx_mock.get_requests()[0]
    assert "/testing/compliance-reports/%2B441234/pdf" in str(req.url)
    assert json.loads(req.content) == {"regulationKey": "eu-ai-act"}
    c.close()


def test_download_report_pdf(httpx_mock: HTTPXMock):
    pdf_bytes = b"%PDF-1.4 fake"
    # First call: API to generate the URL.
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/compliance-reports/%2B441234/pdf",
        method="POST",
        json={"url": "https://s3.example/file.pdf"},
    )
    # Second call: raw S3 download. pytest_httpx mocks the same httpx client,
    # which is what the resource uses for the presigned-URL fetch.
    httpx_mock.add_response(
        url="https://s3.example/file.pdf",
        method="GET",
        content=pdf_bytes,
        headers={"content-type": "application/pdf"},
    )
    c = client()
    out = c.compliance.download_report_pdf("+441234")
    assert out == pdf_bytes
    c.close()


def test_rerun_posts_to_rerun(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/compliance-runs/mt_old/rerun",
        method="POST",
        json={
            "id": "mt_3",
            "kind": "compliance",
            "status": "queued",
            "workspaceId": "w",
            "sector": "i",
            "mission": "m",
            "acceptance": "a",
            "profile": {"phoneNumber": "+44"},
            "createdAt": "",
            "updatedAt": "",
        },
    )
    c = client()
    c.compliance.rerun("mt_old")
    req = httpx_mock.get_requests()[0]
    assert req.url.path == "/testing/compliance-runs/mt_old/rerun"
    assert req.method == "POST"
    c.close()
