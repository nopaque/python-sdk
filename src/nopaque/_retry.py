"""Retry policy and backoff math.

Rules (from the design spec 8):
- GET / PUT / PATCH / DELETE: retry on 429, 5xx, connection/timeout errors.
  Do NOT retry on 400, 401, 403, 404, 409.
- POST: retry only on 429 and pre-flight connection errors.
  Do NOT retry on 5xx, in-flight timeouts, or 409.
- 429 with Retry-After: honor the header; otherwise fall back to backoff.
- Backoff: delay = min(cap, base * 2**attempt) * uniform(0.5, jitter).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from ._errors import (
    APIConnectionError,
    APITimeoutError,
    NopaqueAPIError,
    NopaqueError,
    RateLimitError,
    ServerError,
)


def compute_backoff(
    attempt: int, *, base: float = 0.5, cap: float = 8.0, jitter: float = 1.5
) -> float:
    """Return a backoff delay in seconds for the given attempt number (0-indexed).

    attempt=0 corresponds to the first retry (after the initial failed request).
    """
    raw = min(cap, base * (2 ** attempt))
    multiplier = random.uniform(0.5, jitter)
    return raw * multiplier


def delay_for(
    *,
    attempt: int,
    error: NopaqueError,
    base: float = 0.5,
    cap: float = 8.0,
    jitter: float = 1.5,
) -> float:
    """Compute the delay before the next retry.

    For 429 with a Retry-After header, use that. Otherwise, use exponential backoff.
    """
    if isinstance(error, RateLimitError) and error.retry_after is not None:
        return error.retry_after
    return compute_backoff(attempt, base=base, cap=cap, jitter=jitter)


def should_retry(*, method: str, error: NopaqueError, before_send: bool) -> bool:
    """Decide whether to retry a failed request.

    before_send=True means the error happened before any bytes were sent to the
    server (DNS, TCP connect). Only relevant for POST.
    """
    method = method.upper()

    if isinstance(error, RateLimitError):
        return True  # always retry 429 regardless of method

    if method == "POST":
        if isinstance(error, APIConnectionError) and before_send:
            return True
        return False  # do NOT retry POST on 5xx, in-flight timeouts, etc.

    # Idempotent methods
    if isinstance(error, (APIConnectionError, APITimeoutError, ServerError)):
        return True
    if isinstance(error, NopaqueAPIError):
        return False
    return False


@dataclass
class RetryContext:
    """Tracks retry attempts for a single logical request."""

    max_retries: int
    attempts_used: int = field(default=0)

    def record_attempt(self) -> None:
        self.attempts_used += 1

    def remaining(self) -> int:
        return max(0, self.max_retries - self.attempts_used)

    def exhausted(self) -> bool:
        return self.remaining() == 0
