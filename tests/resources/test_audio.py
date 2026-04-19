import pytest
from pytest_httpx import HTTPXMock
from nopaque import Nopaque
from nopaque._errors import NotFoundError


def client():
    return Nopaque(api_key="k", max_retries=0)


def test_list_audio(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio",
        json={
            "items": [
                {"id": "aud_1", "fileName": "a.wav", "contentType": "audio/wav"},
                {"id": "aud_2", "fileName": "b.wav", "contentType": "audio/wav"},
            ],
            "nextToken": None,
        },
    )
    c = client()
    files = list(c.audio.list())
    assert [f.id for f in files] == ["aud_1", "aud_2"]
    assert files[0].file_name == "a.wav"
    c.close()


def test_list_audio_paginates(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio",
        match_json=None,
        json={
            "items": [{"id": "aud_1", "fileName": "a", "contentType": "audio/wav"}],
            "nextToken": "t1",
        },
    )
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio?nextToken=t1",
        json={
            "items": [{"id": "aud_2", "fileName": "b", "contentType": "audio/wav"}],
            "nextToken": None,
        },
    )
    c = client()
    files = list(c.audio.list())
    assert [f.id for f in files] == ["aud_1", "aud_2"]
    c.close()


def test_get_audio(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio/aud_1",
        json={"id": "aud_1", "fileName": "a.wav", "contentType": "audio/wav", "sizeBytes": 1024},
    )
    c = client()
    f = c.audio.get("aud_1")
    assert f.id == "aud_1"
    assert f.size_bytes == 1024
    c.close()


def test_get_audio_not_found(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio/missing",
        status_code=404,
        json={"error": "not found"},
    )
    c = client()
    with pytest.raises(NotFoundError):
        c.audio.get("missing")
    c.close()


def test_delete_audio(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio/aud_1",
        method="DELETE",
        json={"message": "deleted"},
    )
    c = client()
    c.audio.delete("aud_1")
    c.close()


def test_create_upload_url(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio/upload-url",
        method="POST",
        json={
            "uploadUrl": "https://s3.example.com/signed",
            "audioId": "aud_xyz",
            "expiresIn": 3600,
        },
    )
    c = client()
    res = c.audio.create_upload_url(file_name="a.wav", content_type="audio/wav")
    assert res.upload_url == "https://s3.example.com/signed"
    assert res.audio_id == "aud_xyz"
    c.close()


def test_create_download_url(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio/download-url?audioId=aud_1",
        json={"downloadUrl": "https://s3.example.com/dl", "expiresIn": 3600},
    )
    c = client()
    res = c.audio.create_download_url("aud_1")
    assert res.download_url == "https://s3.example.com/dl"
    c.close()
