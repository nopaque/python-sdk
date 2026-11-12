"""Tests for the digital_testing connector and connector-type methods."""
import json

from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque

BASE = "https://api.nopaque.co.uk"

CONNECTOR = {
    "id": "c1",
    "workspaceId": "w1",
    "userId": "u1",
    "name": "Support bot",
    "type": "http-json",
    "targetRef": "support-bot",
    "config": {"url": "https://bot.example/chat"},
    "typeUpdatedAt": "http-json#2026-11-12T09:00:00Z",
    "createdAt": "2026-11-12T09:00:00Z",
    "updatedAt": "2026-11-12T09:00:00Z",
}


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_list_filters_and_follows_cursor(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/connectors?type=http-json",
        json={"connectors": [CONNECTOR], "nextCursor": "abc"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/connectors?type=http-json&cursor=abc",
        json={"connectors": [{**CONNECTOR, "id": "c2"}]},
    )
    c = client()
    out = list(c.digital_testing.list_connectors(type="http-json"))
    assert [x.id for x in out] == ["c1", "c2"]
    assert out[0].target_ref == "support-bot"
    assert out[0].config == {"url": "https://bot.example/chat"}
    c.close()


def test_list_page(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/connectors?limit=1",
        json={"connectors": [CONNECTOR], "nextCursor": "abc"},
    )
    c = client()
    page = c.digital_testing.list_connectors_page(limit=1)
    assert page.items[0].id == "c1" and page.next_token == "abc"
    c.close()


def test_crud(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/connectors", method="POST", status_code=201, json=CONNECTOR
    )
    httpx_mock.add_response(url=f"{BASE}/digital-testing/connectors/c1", json=CONNECTOR)
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/connectors/c1",
        method="PATCH",
        json={**CONNECTOR, "name": "Renamed"},
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/connectors/c1",
        method="DELETE",
        json={"message": "Connector deleted"},
    )
    c = client()
    created = c.digital_testing.create_connector(
        name="Support bot",
        type="http-json",
        target_ref="support-bot",
        config={"url": "https://bot.example/chat"},
    )
    assert json.loads(httpx_mock.get_requests()[0].content) == {
        "name": "Support bot",
        "type": "http-json",
        "targetRef": "support-bot",
        "config": {"url": "https://bot.example/chat"},
    }
    assert created.workspace_id == "w1"
    assert c.digital_testing.get_connector("c1").type == "http-json"
    updated = c.digital_testing.update_connector("c1", name="Renamed")
    assert json.loads(httpx_mock.get_requests()[2].content) == {"name": "Renamed"}
    assert updated.name == "Renamed"
    assert c.digital_testing.delete_connector("c1") is None
    c.close()


def test_connector_types(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/connector-types",
        json={
            "types": [
                {
                    "type": "lex-v2",
                    "label": "Amazon Lex V2",
                    "hint": "A Lex bot in your account",
                    "formFields": [
                        {"name": "botId", "label": "Bot ID", "type": "text", "required": True}
                    ],
                    "crossAccount": {
                        "principalArn": "arn:aws:iam::1:role/x",
                        "roleNamePrefix": "nopaque-",
                        "actions": ["lex:RecognizeText"],
                        "externalId": "ext",
                    },
                }
            ]
        },
    )
    c = client()
    types = c.digital_testing.list_connector_types()
    assert types[0].form_fields[0].required is True
    assert types[0].cross_account is not None
    assert types[0].cross_account.role_name_prefix == "nopaque-"
    c.close()


async def test_async_connectors(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/connectors", json={"connectors": [CONNECTOR]}
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/connectors?limit=2", json={"connectors": [CONNECTOR]}
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/connectors", method="POST", json=CONNECTOR
    )
    httpx_mock.add_response(url=f"{BASE}/digital-testing/connectors/c1", json=CONNECTOR)
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/connectors/c1", method="PATCH", json=CONNECTOR
    )
    httpx_mock.add_response(
        url=f"{BASE}/digital-testing/connectors/c1", method="DELETE", json={"message": "ok"}
    )
    httpx_mock.add_response(url=f"{BASE}/digital-testing/connector-types", json={"types": []})
    c = AsyncNopaque(api_key="k", max_retries=0)
    dt = c.digital_testing
    assert [x.id async for x in dt.list_connectors()] == ["c1"]
    assert (await dt.list_connectors_page(limit=2)).items[0].id == "c1"
    created = await dt.create_connector(
        name="n", type="web-widget", target_ref="t", config={}, description="d"
    )
    assert created.id == "c1"
    assert json.loads(httpx_mock.get_requests()[2].content)["description"] == "d"
    assert (await dt.get_connector("c1")).id == "c1"
    assert (await dt.update_connector("c1", config={"a": 1})).id == "c1"
    assert await dt.delete_connector("c1") is None
    assert await dt.list_connector_types() == []
    await c.aclose()


def test_dot_and_empty_ids_are_rejected():
    import pytest

    c = client()
    for bad in (".", "..", ""):
        with pytest.raises(ValueError):
            c.digital_testing.get_connector(bad)
    c.close()
