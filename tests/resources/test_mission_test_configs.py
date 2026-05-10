"""Tests for the mission_test_configs resource."""
import json

import pytest
from pytest_httpx import HTTPXMock

from nopaque import Nopaque, NotFoundError


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_create_sends_expected_body(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-test-configs",
        method="POST",
        json={
            "id": "cfg_1",
            "name": "qa",
            "sector": "insurance",
            "mission": "m",
            "acceptance": "a",
            "profileId": "p_1",
            "workspaceId": "w",
            "createdAt": "",
            "updatedAt": "",
        },
    )
    c = client()
    cfg = c.mission_test_configs.create(
        name="qa",
        sector="insurance",
        mission="m",
        acceptance="a",
        profile_id="p_1",
    )
    assert cfg.id == "cfg_1"
    req = httpx_mock.get_requests()[0]
    assert json.loads(req.content) == {
        "name": "qa",
        "sector": "insurance",
        "mission": "m",
        "acceptance": "a",
        "profileId": "p_1",
    }
    c.close()


def test_list_returns_paginator(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-test-configs",
        json={
            "items": [
                {
                    "id": "cfg_1",
                    "name": "qa",
                    "sector": "i",
                    "mission": "m",
                    "acceptance": "a",
                    "profileId": "p",
                    "workspaceId": "w",
                    "createdAt": "",
                    "updatedAt": "",
                }
            ],
            "nextToken": None,
        },
    )
    c = client()
    ids = [cfg.id for cfg in c.mission_test_configs.list()]
    assert ids == ["cfg_1"]
    c.close()


def test_get_returns_config(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-test-configs/cfg_1",
        json={
            "id": "cfg_1",
            "name": "qa",
            "sector": "i",
            "mission": "m",
            "acceptance": "a",
            "profileId": "p",
            "workspaceId": "w",
            "createdAt": "",
            "updatedAt": "",
        },
    )
    c = client()
    cfg = c.mission_test_configs.get("cfg_1")
    assert cfg.name == "qa"
    c.close()


def test_delete(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-test-configs/cfg_1",
        method="DELETE",
        json={"message": "ok"},
    )
    c = client()
    c.mission_test_configs.delete("cfg_1")
    c.close()


def test_run_launches_a_mission_test(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-test-configs/cfg_1/runs",
        method="POST",
        json={
            "id": "mt_2",
            "kind": "freeform",
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
    run = c.mission_test_configs.run("cfg_1")
    assert run.id == "mt_2"
    req = httpx_mock.get_requests()[0]
    assert req.url.path == "/testing/mission-test-configs/cfg_1/runs"
    assert req.method == "POST"
    c.close()


def test_get_cross_workspace_raises_not_found(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-test-configs/cfg_other",
        status_code=404,
        json={"error": "not found"},
    )
    c = client()
    with pytest.raises(NotFoundError):
        c.mission_test_configs.get("cfg_other")
    c.close()
