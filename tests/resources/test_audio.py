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


def test_upload_does_presign_then_put(httpx_mock: HTTPXMock, tmp_path):
    # Step A: presign call
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio/upload-url",
        method="POST",
        json={
            "uploadUrl": "https://s3.example.com/signed",
            "audioId": "aud_xyz",
            "expiresIn": 3600,
        },
    )
    # Step B: S3 PUT
    httpx_mock.add_response(
        url="https://s3.example.com/signed",
        method="PUT",
        status_code=200,
    )
    # Step C: fetch metadata after upload
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio/aud_xyz",
        json={"id": "aud_xyz", "fileName": "a.wav", "contentType": "audio/wav"},
    )

    f = tmp_path / "a.wav"
    f.write_bytes(b"RIFF...WAVEfmt ")
    c = client()
    audio = c.audio.upload(file=str(f), content_type="audio/wav")
    assert audio.id == "aud_xyz"
    c.close()


def test_upload_accepts_bytes(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio/upload-url",
        method="POST",
        json={"uploadUrl": "https://s3.example.com/x", "audioId": "aud_1", "expiresIn": 60},
    )
    httpx_mock.add_response(url="https://s3.example.com/x", method="PUT")
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio/aud_1",
        json={"id": "aud_1", "fileName": "clip.wav", "contentType": "audio/wav"},
    )
    c = client()
    audio = c.audio.upload(file=b"RIFF...", content_type="audio/wav", name="clip.wav")
    assert audio.id == "aud_1"
    c.close()


def test_upload_s3_put_failure_surfaces_as_connection_error(httpx_mock: HTTPXMock):
    from nopaque._errors import APIConnectionError
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio/upload-url",
        method="POST",
        json={"uploadUrl": "https://s3.example.com/x", "audioId": "aud_1", "expiresIn": 60},
    )
    httpx_mock.add_response(
        url="https://s3.example.com/x",
        method="PUT",
        status_code=403,
        text="<Error>access denied</Error>",
    )
    c = client()
    with pytest.raises(APIConnectionError):
        c.audio.upload(file=b"RIFF", content_type="audio/wav", name="x.wav")
    c.close()


def test_download_returns_bytes(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio/download-url?audioId=aud_1",
        json={"downloadUrl": "https://s3.example.com/dl", "expiresIn": 60},
    )
    httpx_mock.add_response(
        url="https://s3.example.com/dl",
        content=b"WAVE_BYTES",
    )
    c = client()
    data = c.audio.download("aud_1")
    assert data == b"WAVE_BYTES"
    c.close()


def test_download_writes_to_path(httpx_mock: HTTPXMock, tmp_path):
    httpx_mock.add_response(
        url="https://api.nopaque.co.uk/audio/download-url?audioId=aud_1",
        json={"downloadUrl": "https://s3.example.com/dl", "expiresIn": 60},
    )
    httpx_mock.add_response(
        url="https://s3.example.com/dl",
        content=b"BYTES",
    )
    dest = tmp_path / "out.wav"
    c = client()
    c.audio.download("aud_1", to=str(dest))
    assert dest.read_bytes() == b"BYTES"
    c.close()
