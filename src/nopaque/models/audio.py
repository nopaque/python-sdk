"""Models for /audio endpoints."""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

AudioCategory = Literal["test", "map", "voice", "transcript"]


def _audio_file_alias(name: str) -> str:
    return {
        "content_type": "contentType",
        "size_bytes": "sizeBytes",
        "duration_secs": "durationSecs",
        "sample_rate": "sampleRate",
        "associated_id": "associatedId",
        "created_at": "createdAt",
        "created_by": "createdBy",
    }.get(name, name)


def _upload_url_alias(name: str) -> str:
    return {
        "upload_url": "uploadUrl",
        "audio_id": "audioId",
        "s3_key": "s3Key",
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
    #: Wire name is ``filename``, all lowercase — not ``fileName``.
    filename: str
    content_type: str
    category: Optional[AudioCategory] = None
    associated_id: Optional[str] = None
    size_bytes: Optional[int] = None
    duration_secs: Optional[float] = None
    format: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None


class AudioUploadURL(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_upload_url_alias,
    )

    upload_url: str
    audio_id: str
    s3_key: Optional[str] = None
    expires_in: int


class AudioDownloadURL(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_download_url_alias,
    )

    download_url: str
    expires_in: int
