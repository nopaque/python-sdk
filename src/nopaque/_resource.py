"""Base class for resource modules.

Each resource (MappingResource, AudioResource, etc.) holds a reference to the
transport and exposes one method per endpoint. Sync and async flavors are
separate classes because their method bodies differ.
"""
from __future__ import annotations

from ._transport import AsyncTransport, SyncTransport


class SyncResource:
    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport


class AsyncResource:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport
