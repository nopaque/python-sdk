"""Tests for the mission_test_configs resource."""
import json

import pytest
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque, NotFoundError


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


# --- v0.3.0: tags, update (PATCH), filtered slim list ---

def test_create_with_tags(httpx_mock: HTTPXMock):
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
            "tags": ["compliance-eu"],
        },
    )
    c = client()
    cfg = c.mission_test_configs.create(
        name="qa",
        sector="insurance",
        mission="m",
        acceptance="a",
        profile_id="p_1",
        tags=["compliance-eu"],
        description="desc",
        phone_number="+441234567890",
    )
    assert cfg.tags == ["compliance-eu"]
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["tags"] == ["compliance-eu"]
    assert body["description"] == "desc"
    assert body["phoneNumber"] == "+441234567890"
    c.close()


def test_update_sends_patch_body(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-test-configs/cfg_1",
        method="PATCH",
        json={"id": "cfg_1", "name": "new", "sector": "i", "mission": "m", "acceptance": "a", "profileId": "p"},
    )
    c = client()
    cfg = c.mission_test_configs.update("cfg_1", name="new", tags=["x"])
    assert cfg.name == "new"
    req = httpx_mock.get_requests()[0]
    assert req.method == "PATCH"
    assert json.loads(req.content) == {"name": "new", "tags": ["x"]}
    c.close()


def test_update_can_clear_description_and_tags(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-test-configs/cfg_1",
        method="PATCH",
        json={"id": "cfg_1", "name": "n", "sector": "i", "mission": "m", "acceptance": "a", "profileId": "p"},
    )
    c = client()
    c.mission_test_configs.update("cfg_1", description=None, tags=None)
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {"description": None, "tags": None}
    c.close()


def test_update_requires_at_least_one_field():
    c = client()
    with pytest.raises(ValueError):
        c.mission_test_configs.update("cfg_1")
    c.close()


def test_list_sends_filters_and_returns_slim_items(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-test-configs?sector=insurance&tag=eu&limit=10",
        json={
            "items": [
                {
                    "id": "cfg_1",
                    "workspaceId": "w",
                    "name": "qa",
                    "sector": "insurance",
                    "profileId": "p",
                    "phoneNumber": "+441",
                    "tags": ["eu"],
                    "createdAt": "",
                    "updatedAt": "",
                }
            ],
            "nextCursor": None,
        },
    )
    c = client()
    items = list(c.mission_test_configs.list(sector="insurance", tag="eu", limit=10))
    assert items[0].id == "cfg_1"
    assert items[0].tags == ["eu"]
    assert items[0].sector == "insurance"
    c.close()


async def test_async_update(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/testing/mission-test-configs/cfg_1",
        method="PATCH",
        json={"id": "cfg_1", "name": "n2", "sector": "i", "mission": "m", "acceptance": "a", "profileId": "p"},
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    cfg = await c.mission_test_configs.update("cfg_1", name="n2")
    assert cfg.name == "n2"
    await c.aclose()


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
