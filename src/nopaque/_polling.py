"""Generic wait_for helpers used by resource-level wait_for_complete methods.

Strategy (see design spec 9.1):
- Initial interval defaults to 5.0s.
- Interval softens exponentially toward cap (default 15s) to avoid hammering
  on long jobs.
- Deadline raises NopaqueTimeoutError; the job itself is NOT cancelled.
- on_update callback (if given) is invoked with each fetched document.
"""
from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable
from typing import Callable, TypeVar

from ._errors import NopaqueTimeoutError

T = TypeVar("T")

DEFAULT_TIMEOUT = 600.0
DEFAULT_INITIAL_INTERVAL = 5.0
DEFAULT_INTERVAL_CAP = 15.0


def poll_interval_curve(
    step: int, *, base: float = DEFAULT_INITIAL_INTERVAL, cap: float = DEFAULT_INTERVAL_CAP
) -> float:
    """Return the interval for poll number `step` (0-indexed).

    Softens: base, base, base*1.2, base*1.5, base*2, cap, cap, ...
    """
    if step < 2:
        return base
    soft = base * (1.2 ** (step - 1))
    return min(cap, soft)


def wait_for_sync(
    *,
    fetch: Callable[[], T],
    is_terminal: Callable[[T], bool],
    timeout: float = DEFAULT_TIMEOUT,
    initial_interval: float = DEFAULT_INITIAL_INTERVAL,
    interval_cap: float = DEFAULT_INTERVAL_CAP,
    on_update: Callable[[T], None] | None = None,
) -> T:
    """Poll `fetch` until `is_terminal` returns True or the deadline is exceeded."""
    deadline = time.monotonic() + timeout
    step = 0
    while True:
        doc = fetch()
        if on_update:
            try:
                on_update(doc)
            except Exception:
                pass
        if is_terminal(doc):
            return doc
        now = time.monotonic()
        if now >= deadline:
            raise NopaqueTimeoutError(
                f"wait_for timed out after {timeout:.1f}s"
            )
        interval = poll_interval_curve(
            step, base=initial_interval, cap=interval_cap
        )
        # clamp so we don't sleep past the deadline
        interval = min(interval, max(0.0, deadline - now))
        time.sleep(interval)
        step += 1


async def wait_for_async(
    *,
    fetch: Callable[[], Awaitable[T]],
    is_terminal: Callable[[T], bool],
    timeout: float = DEFAULT_TIMEOUT,
    initial_interval: float = DEFAULT_INITIAL_INTERVAL,
    interval_cap: float = DEFAULT_INTERVAL_CAP,
    on_update: Callable[[T], None] | None = None,
) -> T:
    """Async variant of wait_for_sync."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    step = 0
    while True:
        doc = await fetch()
        if on_update:
            try:
                on_update(doc)
            except Exception:
                pass
        if is_terminal(doc):
            return doc
        now = loop.time()
        if now >= deadline:
            raise NopaqueTimeoutError(
                f"wait_for timed out after {timeout:.1f}s"
            )
        interval = poll_interval_curve(
            step, base=initial_interval, cap=interval_cap
        )
        interval = min(interval, max(0.0, deadline - now))
        await asyncio.sleep(interval)
        step += 1
