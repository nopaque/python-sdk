"""Tests for the mission_tests resource."""
import json

import pytest
from pytest_httpx import HTTPXMock

from nopaque import Nopaque, NotFoundError, ServerError


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_create_sends_expected_body(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests",
        method="POST",
        json={
            "id": "mt_1",
            "workspaceId": "w",
            "kind": "freeform",
            "sector": "insurance",
            "mission": "Buy a policy",
            "acceptance": "Bot offers a quote",
            "profile": {"phoneNumber": "+441234"},
            "status": "queued",
            "createdAt": "",
            "updatedAt": "",
        },
    )
    c = client()
    run = c.mission_tests.create(
        sector="insurance",
        mission="Buy a policy",
        acceptance="Bot offers a quote",
        profile={"phone_number": "+441234"},
    )
    assert run.id == "mt_1"
    assert run.kind == "freeform"
    req = httpx_mock.get_requests()[0]
    assert json.loads(req.content) == {
        "sector": "insurance",
        "mission": "Buy a policy",
        "acceptance": "Bot offers a quote",
        "profile": {"phoneNumber": "+441234"},
    }
    c.close()


def test_list_returns_paginator(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests",
        json={
            "items": [
                {
                    "id": "mt_1",
                    "kind": "freeform",
                    "status": "completed",
                    "workspaceId": "w",
                    "sector": "i",
                    "mission": "m",
                    "acceptance": "a",
                    "profile": {"phoneNumber": "+44"},
                    "createdAt": "",
                    "updatedAt": "",
                }
            ],
            "nextToken": None,
        },
    )
    c = client()
    ids = [r.id for r in c.mission_tests.list()]
    assert ids == ["mt_1"]
    c.close()


def test_get_defaults_returns_defaults(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests/defaults",
        json={
            "sector": "insurance",
            "mission": "m",
            "acceptance": "a",
            "catalogueVersion": "v1",
        },
    )
    c = client()
    d = c.mission_tests.get_defaults()
    assert d.catalogue_version == "v1"
    c.close()


def test_get_defaults_surfaces_catalog_not_ready(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests/defaults",
        status_code=503,
        json={"error": "not ready", "code": "CATALOG_NOT_READY"},
    )
    c = client()
    with pytest.raises(ServerError) as exc:
        c.mission_tests.get_defaults()
    assert exc.value.code == "CATALOG_NOT_READY"
    c.close()


def test_get_returns_a_run(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests/mt_1",
        json={
            "id": "mt_1",
            "kind": "freeform",
            "status": "running",
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
    run = c.mission_tests.get("mt_1")
    assert run.status == "running"
    c.close()


def test_get_cross_workspace_raises_not_found(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests/mt_other",
        status_code=404,
        json={"error": "not found"},
    )
    c = client()
    with pytest.raises(NotFoundError):
        c.mission_tests.get("mt_other")
    c.close()


def test_cancel_posts_to_cancel(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-tests/mt_1/cancel",
        method="POST",
        json={
            "id": "mt_1",
            "kind": "freeform",
            "status": "cancelled",
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
    r = c.mission_tests.cancel("mt_1")
    assert r.status == "cancelled"
    req = httpx_mock.get_requests()[0]
    assert req.url.path == "/testing/mission-tests/mt_1/cancel"
    assert req.method == "POST"
    c.close()
