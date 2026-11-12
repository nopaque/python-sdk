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


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(word.capitalize() for word in rest)


#: Delivery emotion for an Ultra voice.
SpeechEmotion = Literal[
    "neutral", "happy", "sad", "angry", "fearful", "disgusted", "surprised"
]


class SpeechSettings(BaseModel):
    """Delivery settings for ``audio.generate``. Ultra voices only.

    ``speed`` is 0.6-1.5 (above 1 is faster); ``volume`` is 0.5-2.0.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    speed: Optional[float] = None
    volume: Optional[float] = None
    emotion: Optional[SpeechEmotion] = None


class GeneratedSpeech(BaseModel):
    """Response for ``POST /audio/generate``: the stored voice clip.

    ``url`` is a presigned GET URL valid for ``expires_in_secs``.
    ``characters`` is what was billed.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=_camel,
    )

    audio_id: str
    url: str
    expires_in_secs: Optional[int] = None
    characters: Optional[int] = None
    size_bytes: Optional[int] = None
    duration_secs: Optional[float] = None
    voice_id: Optional[str] = None
    name: Optional[str] = None
