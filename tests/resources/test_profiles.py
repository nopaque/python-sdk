import pytest
from pytest_httpx import HTTPXMock

from nopaque import Nopaque
from nopaque._errors import NotFoundError


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_create_profile(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/profiles",
        method="POST",
        json={"id": "p1", "name": "Customer"},
    )
    c = client()
    p = c.profiles.create(name="Customer")
    assert p.id == "p1"
    c.close()


def test_list_profiles(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/profiles",
        json={"profiles": [{"id": "p1", "name": "A"}], "count": 1},
    )
    c = client()
    out = list(c.profiles.list())
    assert out[0].id == "p1"
    c.close()


def test_get_profile(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/profiles/p1",
        json={"id": "p1", "name": "A", "items": []},
    )
    c = client()
    p = c.profiles.get("p1")
    assert p.id == "p1"
    c.close()


def test_get_profile_not_found(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/profiles/missing",
        status_code=404,
        json={"error": "not found"},
    )
    c = client()
    with pytest.raises(NotFoundError):
        c.profiles.get("missing")
    c.close()


def test_update_profile(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/profiles/p1",
        method="PUT",
        json={"id": "p1", "name": "Premium"},
    )
    c = client()
    p = c.profiles.update("p1", name="Premium")
    assert p.name == "Premium"
    c.close()


def test_delete_profile(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/profiles/p1",
        method="DELETE",
        json={"message": "ok"},
    )
    c = client()
    c.profiles.delete("p1")
    c.close()


def test_add_item(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/profiles/p1/items",
        method="POST",
        json={"id": "it1", "profileId": "p1", "label": "account", "value": "123"},
    )
    c = client()
    item = c.profiles.add_item("p1", label="account", value="123")
    assert item.id == "it1"
    assert item.value == "123"
    c.close()


def test_update_item(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/profiles/p1/items/it1",
        method="PUT",
        json={"id": "it1", "label": "account", "value": "999"},
    )
    c = client()
    item = c.profiles.update_item("p1", "it1", value="999")
    assert item.value == "999"
    c.close()


def test_delete_item(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/profiles/p1/items/it1",
        method="DELETE",
        json={"message": "ok"},
    )
    c = client()
    c.profiles.delete_item("p1", "it1")
    c.close()


def test_list_parameters(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/profiles/parameters",
        json={"parameters": ["account_number", "postcode"]},
    )
    c = client()
    out = c.profiles.list_parameters()
    assert out.parameters == ["account_number", "postcode"]
    c.close()


def test_find_by_parameters(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/profiles/by-parameters?labels=account_number%2Cpostcode",
        json={"profiles": [{"id": "p1", "name": "A", "matchedLabels": ["account_number", "postcode"]}], "count": 1},
    )
    c = client()
    matches = c.profiles.find_by_parameters(labels=["account_number", "postcode"])
    assert matches[0].id == "p1"
    assert matches[0].matched_labels == ["account_number", "postcode"]
    c.close()
