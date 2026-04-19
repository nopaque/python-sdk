"""Models for /audio endpoints."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


def _audio_file_alias(name: str) -> str:
    return {
        "file_name": "fileName",
        "content_type": "contentType",
        "size_bytes": "sizeBytes",
        "created_at": "createdAt",
    }.get(name, name)


def _upload_url_alias(name: str) -> str:
    return {
        "upload_url": "uploadUrl",
        "audio_id": "audioId",
        "expires_in": "expiresIn",
    }.get(name, name)


def _download_url_alias(name: str) -> str:
    return {
        "download_url": "downloadUrl",
        "expires_in": "expiresIn",
    }.get(name, name)


class AudioFile(BaseModel):
    """Metadata for an uploaded audio file."""

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_audio_file_alias,
    )

    id: str
    file_name: str
    content_type: str
    size_bytes: Optional[int] = None
    created_at: Optional[str] = None


class AudioUploadURL(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_upload_url_alias,
    )

    upload_url: str
    audio_id: str
    expires_in: int


class AudioDownloadURL(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_download_url_alias,
    )

    download_url: str
    expires_in: int
