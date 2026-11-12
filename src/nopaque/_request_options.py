"""Per-call request options."""
from __future__ import annotations

from typing import TypedDict


class RequestOptions(TypedDict, total=False):
    """Per-call overrides for timeout, retries, headers, and cancellation.

    Pass to any resource method:

        client.mapping.get(id, request_options={"timeout": 5.0, "max_retries": 0})
    """

    timeout: float
    max_retries: int
    headers: dict
    idempotency_key: str  # reserved for future use


def merge_options(
    defaults: RequestOptions | None, overrides: RequestOptions | None
) -> RequestOptions:
    base: RequestOptions = dict(defaults) if defaults else {}  # type: ignore[assignment]
    if overrides:
        headers = {**(base.get("headers") or {}), **(overrides.get("headers") or {})}
        base.update(overrides)  # type: ignore[typeddict-item]
        if headers:
            base["headers"] = headers
    return base


def without_retries(options: RequestOptions | None) -> RequestOptions:
    """Default ``max_retries`` to 0, keeping any value the caller passed.

    For POSTs that spend money (a number order, a speech generation, a batch
    re-run): even a retry the transport judges safe is not worth the risk of
    a second charge, so these are never retried unless the caller asks.
    """
    merged: RequestOptions = dict(options) if options else {}  # type: ignore[assignment]
    merged.setdefault("max_retries", 0)
    return merged
