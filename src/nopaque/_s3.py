"""S3 helpers for presigned URL uploads and downloads.

S3 PUT/GET goes directly between the SDK and S3 - it does NOT go through the
Nopaque API. Failures on these operations surface as APIConnectionError, with
the S3 status and body attached for debugging.
"""
from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any, BinaryIO, Optional, Tuple, Union

import httpx

from ._errors import APIConnectionError

FileSource = Union[str, Path, bytes, BinaryIO]


def _read_bytes(source: Any) -> Tuple[bytes, Optional[str]]:
    """Return (bytes, inferred_name) from any supported source type."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        return path.read_bytes(), path.name
    if isinstance(source, (bytes, bytearray)):
        return bytes(source), None
    if hasattr(source, "read"):
        data = source.read()
        if isinstance(data, str):
            raise TypeError("file must be opened in binary mode")
        name = getattr(source, "name", None)
        inferred = os.path.basename(name) if isinstance(name, str) else None
        return data, inferred
    raise TypeError(f"unsupported file source: {type(source)!r}")


def sniff_content_type(
    name: Optional[str], fallback: str = "application/octet-stream"
) -> str:
    if not name:
        return fallback
    guessed, _ = mimetypes.guess_type(name)
    return guessed or fallback


def s3_put_sync(url: str, data: bytes, *, content_type: str) -> None:
    try:
        with httpx.Client() as c:
            resp = c.put(url, content=data, headers={"Content-Type": content_type})
    except httpx.HTTPError as e:
        raise APIConnectionError(f"S3 PUT failed: {e}", cause=e) from e
    if resp.status_code >= 400:
        raise APIConnectionError(
            f"S3 PUT returned {resp.status_code}: {resp.text[:200]}"
        )


def s3_get_sync(url: str) -> bytes:
    try:
        with httpx.Client() as c:
            resp = c.get(url)
    except httpx.HTTPError as e:
        raise APIConnectionError(f"S3 GET failed: {e}", cause=e) from e
    if resp.status_code >= 400:
        raise APIConnectionError(
            f"S3 GET returned {resp.status_code}: {resp.text[:200]}"
        )
    return resp.content


async def s3_put_async(url: str, data: bytes, *, content_type: str) -> None:
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.put(url, content=data, headers={"Content-Type": content_type})
    except httpx.HTTPError as e:
        raise APIConnectionError(f"S3 PUT failed: {e}", cause=e) from e
    if resp.status_code >= 400:
        raise APIConnectionError(
            f"S3 PUT returned {resp.status_code}: {resp.text[:200]}"
        )


async def s3_get_async(url: str) -> bytes:
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.get(url)
    except httpx.HTTPError as e:
        raise APIConnectionError(f"S3 GET failed: {e}", cause=e) from e
    if resp.status_code >= 400:
        raise APIConnectionError(
            f"S3 GET returned {resp.status_code}: {resp.text[:200]}"
        )
    return resp.content
