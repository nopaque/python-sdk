"""Audio resource - CRUD + upload/download helpers."""
from __future__ import annotations

from typing import Optional

from .._pagination import AsyncPaginator, Page, SyncPaginator
from .._request_options import RequestOptions
from .._resource import AsyncResource, SyncResource
from ..models.audio import AudioDownloadURL, AudioFile, AudioUploadURL


class AudioResource(SyncResource):
    """Synchronous /audio endpoints."""

    def list(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
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
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
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
        self, audio_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> AudioFile:
        raw = self._transport.request(
            "GET", f"/audio/{audio_id}", request_options=request_options
        )
        return AudioFile.model_validate(raw)

    def delete(
        self, audio_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> None:
        self._transport.request(
            "DELETE", f"/audio/{audio_id}", request_options=request_options
        )

    def create_upload_url(
        self,
        *,
        file_name: str,
        content_type: str,
        request_options: Optional[RequestOptions] = None,
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
        request_options: Optional[RequestOptions] = None,
    ) -> AudioDownloadURL:
        raw = self._transport.request(
            "GET",
            "/audio/download-url",
            params={"audioId": audio_id},
            request_options=request_options,
        )
        return AudioDownloadURL.model_validate(raw)


class AsyncAudioResource(AsyncResource):
    """Asynchronous /audio endpoints."""

    def list(
        self,
        *,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
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
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
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
        self, audio_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> AudioFile:
        raw = await self._transport.request(
            "GET", f"/audio/{audio_id}", request_options=request_options
        )
        return AudioFile.model_validate(raw)

    async def delete(
        self, audio_id: str, *, request_options: Optional[RequestOptions] = None
    ) -> None:
        await self._transport.request(
            "DELETE", f"/audio/{audio_id}", request_options=request_options
        )

    async def create_upload_url(
        self,
        *,
        file_name: str,
        content_type: str,
        request_options: Optional[RequestOptions] = None,
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
        request_options: Optional[RequestOptions] = None,
    ) -> AudioDownloadURL:
        raw = await self._transport.request(
            "GET",
            "/audio/download-url",
            params={"audioId": audio_id},
            request_options=request_options,
        )
        return AudioDownloadURL.model_validate(raw)
