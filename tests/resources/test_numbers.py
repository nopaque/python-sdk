"""Tests for the numbers resource."""
import json

import pytest
from pytest_httpx import HTTPXMock

from nopaque import AsyncNopaque, Nopaque, PhoneNumber

BASE = "https://api.nopaque.co.uk"

NUMBER = {
    "numberId": "n1",
    "orderId": "o1",
    "e164": "+447700900123",
    "countryIso2": "GB",
    "phoneNumberType": "mobile",
    "capabilities": ["voice", "sms"],
    "type": "survey",
    "uses": ["survey"],
    "isDefault": False,
    "state": "ordering",
    "requirementsStatus": "requirement-info-under-review",
    "monthlyRateUsd": 2.0,
    "createdAt": "2026-11-12T09:00:00Z",
}


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_list(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/numbers",
        json={
            "numbers": [NUMBER],
            "allowance": {
                "used": 1,
                "max": 5,
                "remaining": 4,
                "unlimited": False,
                "source": "tier",
                "tier": "pro",
            },
        },
    )
    c = client()
    out = c.numbers.list()
    assert out.numbers[0].number_id == "n1"
    assert out.numbers[0].country_iso2 == "GB"
    assert out.numbers[0].monthly_rate_usd == 2.0
    assert out.allowance is not None and out.allowance.remaining == 4
    c.close()


def test_list_empty_without_allowance(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/numbers", json={"numbers": []})
    c = client()
    out = c.numbers.list()
    assert out.numbers == [] and out.allowance is None
    c.close()


def test_available_sends_only_given_params(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/numbers/available?country=GB&numberType=outbound&limit=5",
        json={
            "country": "GB",
            "phoneNumberType": "national",
            "phoneNumberTypes": ["national", "local"],
            "numberType": "outbound",
            "numbers": [
                {
                    "e164": "+442039000000",
                    "fromPool": True,
                    "phoneNumberType": "national",
                    "capabilities": ["voice"],
                    "monthlyRateUsd": 1.0,
                    "upfrontRateUsd": 0,
                    "selfServe": True,
                    "currency": "USD",
                    "immediateActivation": True,
                }
            ],
        },
    )
    c = client()
    out = c.numbers.list_available(country="GB", number_type="outbound", limit=5)
    assert out.phone_number_types == ["national", "local"]
    assert out.numbers[0].from_pool is True
    assert out.numbers[0].immediate_activation is True
    c.close()


def test_requirements(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/numbers/requirements?country=GB&phoneNumberType=mobile",
        json={
            "country": "GB",
            "phoneNumberType": "mobile",
            "requirements": [
                {
                    "id": "r1",
                    "name": "Proof of address",
                    "fieldType": "document",
                    "satisfiedBy": "nopaque",
                }
            ],
        },
    )
    c = client()
    out = c.numbers.get_requirements(country="GB", phone_number_type="mobile")
    assert out.requirements[0].field_type == "document"
    assert out.requirements[0].satisfied_by == "nopaque"
    c.close()


def test_order_body_and_pending_activation(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/numbers/orders",
        method="POST",
        status_code=202,
        json={
            "number": NUMBER,
            "orderId": "o1",
            "activation": {"immediate": False, "message": "About a day"},
            "requirementsSubmitted": True,
            "upfrontChargedUsd": 1.5,
            "monthlyRateUsd": 2.0,
        },
    )
    c = client()
    out = c.numbers.order(e164="+447700900123", number_type="survey", country="GB")
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {"e164": "+447700900123", "numberType": "survey", "country": "GB"}
    assert out.order_id == "o1"
    assert out.number.state == "ordering"
    assert out.activation is not None and out.activation.immediate is False
    c.close()


def test_order_sends_phone_number_type(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/numbers/orders",
        method="POST",
        status_code=201,
        json={"number": {**NUMBER, "state": "live"}, "fromPool": True, "activation": {}},
    )
    c = client()
    out = c.numbers.order(
        e164="+447700900123", number_type="outbound", country="GB", phone_number_type="local"
    )
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["phoneNumberType"] == "local"
    assert out.order_id is None and out.from_pool is True
    c.close()


def test_get_order(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/numbers/orders/o1",
        json={
            "orderId": "o1",
            "number": NUMBER,
            "progress": {
                "total": 6,
                "approved": 5,
                "awaitingOn": 1,
                "outstanding": [
                    {"requirementId": "r6", "name": "Address", "fieldType": "address", "status": "pending"}
                ],
                "waitingOn": "telnyx",
                "complete": False,
                "customerMustAct": False,
            },
        },
    )
    c = client()
    out = c.numbers.get_order("o1")
    assert out.progress.awaiting_on == 1
    assert out.progress.outstanding[0].requirement_id == "r6"
    assert out.progress.waiting_on == "telnyx"
    c.close()


def test_update_unwraps_number(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/numbers/n1",
        method="PATCH",
        json={"number": {**NUMBER, "uses": ["load"], "isDefault": True}},
    )
    c = client()
    out = c.numbers.update("n1", uses=["load"], is_default=True)
    assert json.loads(httpx_mock.get_requests()[0].content) == {
        "uses": ["load"],
        "isDefault": True,
    }
    assert isinstance(out, PhoneNumber)
    assert out.uses == ["load"] and out.is_default is True
    c.close()


def test_update_needs_a_field():
    c = client()
    with pytest.raises(ValueError):
        c.numbers.update("n1")
    c.close()


def test_release(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{BASE}/numbers/n1/release",
        method="POST",
        json={"released": True, "message": "Released"},
    )
    c = client()
    out = c.numbers.release("n1")
    assert out.released is True
    c.close()


async def test_async_numbers(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{BASE}/numbers", json={"numbers": [NUMBER]})
    httpx_mock.add_response(
        url=f"{BASE}/numbers/orders",
        method="POST",
        status_code=202,
        json={"number": NUMBER, "orderId": "o1", "activation": {"immediate": False}},
    )
    httpx_mock.add_response(
        url=f"{BASE}/numbers/n1", method="PATCH", json={"number": {**NUMBER, "uses": ["outbound"]}}
    )
    httpx_mock.add_response(
        url=f"{BASE}/numbers/n1/release", method="POST", status_code=202, json={"released": False}
    )
    httpx_mock.add_response(
        url=f"{BASE}/numbers/available?country=GB",
        json={"country": "GB", "numbers": []},
    )
    httpx_mock.add_response(
        url=f"{BASE}/numbers/requirements?country=GB",
        json={"country": "GB", "requirements": []},
    )
    httpx_mock.add_response(
        url=f"{BASE}/numbers/orders/o1",
        json={
            "orderId": "o1",
            "number": NUMBER,
            "progress": {
                "total": 1,
                "approved": 1,
                "awaitingOn": 0,
                "outstanding": [],
                "waitingOn": "nobody",
                "complete": True,
            },
        },
    )
    c = AsyncNopaque(api_key="k", max_retries=0)
    assert (await c.numbers.list()).numbers[0].e164 == "+447700900123"
    assert (await c.numbers.order(e164="+1", number_type="survey", country="GB")).order_id == "o1"
    assert (await c.numbers.update("n1", uses=["outbound"])).uses == ["outbound"]
    assert (await c.numbers.release("n1")).released is False
    assert (await c.numbers.list_available(country="GB")).numbers == []
    assert (await c.numbers.get_requirements(country="GB")).requirements == []
    assert (await c.numbers.get_order("o1")).progress.complete is True
    await c.aclose()
