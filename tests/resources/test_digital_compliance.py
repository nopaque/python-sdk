"""Tests for the digital compliance resource."""
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque

BASE = "https://api.nopaque.co.uk"


def client():
    return Nopaque(api_key="k", max_retries=0)


AUDIT = {
    "targetRef": "acme/billing-bot",
    "lastRunAt": "2026-08-12T00:00:00Z",
    "runCount": 4,
    "catalogueTestIds": ["M-001"],
}


def test_list_audits_unwraps_envelope(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/compliance-audits", json={"audits": [AUDIT]}
    )
    c = client()
    r = c.digital_compliance.list_audits()
    assert len(r) == 1
    assert r[0].run_count == 4
    assert r[0].target_ref == "acme/billing-bot"
    c.close()


def test_list_audits_returns_empty_when_key_absent(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/digital-testing/compliance-audits", json={})
    c = client()
    assert c.digital_compliance.list_audits() == []
    c.close()


def test_get_report_sends_target_ref_as_query_never_path(httpx_mock: HTTPXMock):
    """A targetRef contains slashes, so it cannot be a path segment."""
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/compliance-audits/report?targetRef=acme%2Fbilling-bot",
        json={"targetRef": "acme/billing-bot"},
    )
    c = client()
    c.digital_compliance.get_report(target_ref="acme/billing-bot")
    url = str(httpx_mock.get_requests()[0].url)
    assert "/digital-testing/compliance-audits/report" in url
    assert "targetRef=acme%2Fbilling-bot" in url
    assert "report/acme" not in url
    c.close()


def test_get_report_includes_sector_when_given(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/compliance-audits/report"
        "?targetRef=acme%2Fbilling-bot&sector=utilities",
        json={},
    )
    c = client()
    c.digital_compliance.get_report(target_ref="acme/billing-bot", sector="utilities")
    assert "sector=utilities" in str(httpx_mock.get_requests()[0].url)
    c.close()


def test_get_report_omits_sector_when_not_given(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/compliance-audits/report?targetRef=acme%2Fbot",
        json={},
    )
    c = client()
    c.digital_compliance.get_report(target_ref="acme/bot")
    assert "sector" not in str(httpx_mock.get_requests()[0].url)
    c.close()


async def test_list_audits_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/compliance-audits", json={"audits": [AUDIT]}
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    r = await c.digital_compliance.list_audits()
    assert r[0].run_count == 4
    await c.aclose()
