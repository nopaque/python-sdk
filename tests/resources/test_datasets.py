from pytest_httpx import HTTPXMock

from nopaque import Nopaque


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_create_dataset(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/datasets",
        method="POST",
        json={"id": "ds_1", "name": "UK"},
    )
    c = client()
    d = c.datasets.create(name="UK")
    assert d.id == "ds_1"
    c.close()


def test_list_datasets(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/datasets",
        json={"datasets": [{"id": "ds_1", "name": "UK"}]},
    )
    c = client()
    out = list(c.datasets.list())
    assert out[0].id == "ds_1"
    c.close()


def test_get_dataset(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/datasets/ds_1",
        json={"id": "ds_1", "name": "UK", "itemCount": 5},
    )
    c = client()
    d = c.datasets.get("ds_1")
    assert d.item_count == 5
    c.close()


def test_update_dataset(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/datasets/ds_1",
        method="PUT",
        json={"id": "ds_1", "name": "EU"},
    )
    c = client()
    d = c.datasets.update("ds_1", name="EU")
    assert d.name == "EU"
    c.close()


def test_delete_dataset(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/datasets/ds_1",
        method="DELETE",
        json={"message": "ok"},
    )
    c = client()
    c.datasets.delete("ds_1")
    c.close()


def test_resolve_dataset(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/datasets/ds_1/resolve",
        json={
            "datasetId": "ds_1",
            "resolvedEntries": [
                {"phoneNumber": "+44123", "name": "A"},
            ],
        },
    )
    c = client()
    r = c.datasets.resolve("ds_1")
    assert r.dataset_id == "ds_1"
    assert r.resolved_entries[0].phone_number == "+44123"
    c.close()
