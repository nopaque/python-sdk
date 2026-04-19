"""Audio resource - CRUD + upload/download helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from .._s3 import (
    _read_bytes,
    s3_get_async,
    s3_get_sync,
    s3_put_async,
    s3_put_sync,
    sniff_content_type,
)
from ..models.audio import AudioDownloadURL, AudioFile, AudioUploadURL


class AudioResource(SyncResource):
    """Synchronous /audio endpoints."""

    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> SyncPaginator[AudioFile]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        def fetch(p: dict) -> dict:
            return self._transport.request(
                "GET", "/audio", params=p, request_options=request_options
            )

        return SyncPaginator(fetch_page=fetch, params=params, model_cls=AudioFile)

    def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[AudioFile]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = self._transport.request(
            "GET", "/audio", params=params, request_options=request_options
        )
        items = [AudioFile.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    def get(
        self, audio_id: str, *, request_options: RequestOptions | None = None
    ) -> AudioFile:
        raw = self._transport.request(
            "GET", f"/audio/{audio_id}", request_options=request_options
        )
        return AudioFile.model_validate(raw)

    def delete(
        self, audio_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        self._transport.request(
            "DELETE", f"/audio/{audio_id}", request_options=request_options
        )

    def create_upload_url(
        self,
        *,
        file_name: str,
        content_type: str,
        request_options: RequestOptions | None = None,
    ) -> AudioUploadURL:
        raw = self._transport.request(
            "POST",
            "/audio/upload-url",
            json={"fileName": file_name, "contentType": content_type},
            request_options=request_options,
        )
        return AudioUploadURL.model_validate(raw)

    def create_download_url(
        self,
        audio_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> AudioDownloadURL:
        raw = self._transport.request(
            "GET",
            "/audio/download-url",
            params={"audioId": audio_id},
            request_options=request_options,
        )
        return AudioDownloadURL.model_validate(raw)

    # ---- Helpers ---------------------------------------------------------

    def upload(
        self,
        *,
        file: Any,
        content_type: str | None = None,
        name: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AudioFile:
        """Upload a local file or bytes to Nopaque in one call.

        `file` may be a path string, Path, bytes, or a file-like object opened
        in binary mode.
        """
        data, inferred_name = _read_bytes(file)
        resolved_name = name or inferred_name or "upload.bin"
        resolved_type = content_type or sniff_content_type(resolved_name)

        presign = self.create_upload_url(
            file_name=resolved_name,
            content_type=resolved_type,
            request_options=request_options,
        )
        s3_put_sync(presign.upload_url, data, content_type=resolved_type)
        return self.get(presign.audio_id, request_options=request_options)

    def download(
        self,
        audio_id: str,
        *,
        to: str | Path | None = None,
        request_options: RequestOptions | None = None,
    ) -> bytes | None:
        """Download an audio file. Returns bytes if `to` is None; otherwise
        writes to the given path and returns None.
        """
        presign = self.create_download_url(audio_id, request_options=request_options)
        data = s3_get_sync(presign.download_url)
        if to is None:
            return data
        Path(to).write_bytes(data)
        return None


class AsyncAudioResource(AsyncResource):
    """Asynchronous /audio endpoints."""

    def list(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AsyncPaginator[AudioFile]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token

        async def fetch(p: dict) -> dict:
            return await self._transport.request(
                "GET", "/audio", params=p, request_options=request_options
            )

        return AsyncPaginator(fetch_page=fetch, params=params, model_cls=AudioFile)

    async def list_page(
        self,
        *,
        limit: int | None = None,
        next_token: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> Page[AudioFile]:
        params: dict = {}
        if limit is not None:
            params["limit"] = limit
        if next_token is not None:
            params["nextToken"] = next_token
        raw = await self._transport.request(
            "GET", "/audio", params=params, request_options=request_options
        )
        items = [AudioFile.model_validate(i) for i in raw.get("items", [])]
        return Page(items=items, next_token=raw.get("nextToken"))

    async def get(
        self, audio_id: str, *, request_options: RequestOptions | None = None
    ) -> AudioFile:
        raw = await self._transport.request(
            "GET", f"/audio/{audio_id}", request_options=request_options
        )
        return AudioFile.model_validate(raw)

    async def delete(
        self, audio_id: str, *, request_options: RequestOptions | None = None
    ) -> None:
        await self._transport.request(
            "DELETE", f"/audio/{audio_id}", request_options=request_options
        )

    async def create_upload_url(
        self,
        *,
        file_name: str,
        content_type: str,
        request_options: RequestOptions | None = None,
    ) -> AudioUploadURL:
        raw = await self._transport.request(
            "POST",
            "/audio/upload-url",
            json={"fileName": file_name, "contentType": content_type},
            request_options=request_options,
        )
        return AudioUploadURL.model_validate(raw)

    async def create_download_url(
        self,
        audio_id: str,
        *,
        request_options: RequestOptions | None = None,
    ) -> AudioDownloadURL:
        raw = await self._transport.request(
            "GET",
            "/audio/download-url",
            params={"audioId": audio_id},
            request_options=request_options,
        )
        return AudioDownloadURL.model_validate(raw)

    # ---- Helpers ---------------------------------------------------------

    async def upload(
        self,
        *,
        file: Any,
        content_type: str | None = None,
        name: str | None = None,
        request_options: RequestOptions | None = None,
    ) -> AudioFile:
        """Async variant of AudioResource.upload."""
        data, inferred_name = _read_bytes(file)
        resolved_name = name or inferred_name or "upload.bin"
        resolved_type = content_type or sniff_content_type(resolved_name)

        presign = await self.create_upload_url(
            file_name=resolved_name,
            content_type=resolved_type,
            request_options=request_options,
        )
        await s3_put_async(presign.upload_url, data, content_type=resolved_type)
        return await self.get(presign.audio_id, request_options=request_options)

    async def download(
        self,
        audio_id: str,
        *,
        to: str | Path | None = None,
        request_options: RequestOptions | None = None,
    ) -> bytes | None:
        """Async variant of AudioResource.download."""
        presign = await self.create_download_url(
            audio_id, request_options=request_options
        )
        data = await s3_get_async(presign.download_url)
        if to is None:
            return data
        Path(to).write_bytes(data)
        return None
