import pytest

from nopaque._errors import NopaqueTimeoutError
from nopaque._polling import poll_interval_curve, wait_for_async, wait_for_sync


def test_poll_interval_curve_starts_at_base_and_softens():
    curve = [poll_interval_curve(i, base=5.0, cap=15.0) for i in range(10)]
    assert curve[0] == 5.0
    assert curve[1] >= 5.0
    assert all(c <= 15.0 for c in curve)
    assert curve[-1] == 15.0


def test_wait_for_sync_returns_when_terminal():
    states = iter(["running", "running", "completed"])

    def fetch():
        return {"status": next(states)}

    def is_terminal(doc):
        return doc["status"] in ("completed", "failed")

    out = wait_for_sync(
        fetch=fetch,
        is_terminal=is_terminal,
        timeout=5.0,
        initial_interval=0.01,
    )
    assert out["status"] == "completed"


def test_wait_for_sync_raises_on_timeout():
    def fetch():
        return {"status": "running"}

    with pytest.raises(NopaqueTimeoutError):
        wait_for_sync(
            fetch=fetch,
            is_terminal=lambda d: False,
            timeout=0.05,
            initial_interval=0.01,
        )


def test_wait_for_sync_on_update_fires_each_poll():
    states = iter(["running", "completed"])
    seen = []

    def fetch():
        return {"status": next(states)}

    wait_for_sync(
        fetch=fetch,
        is_terminal=lambda d: d["status"] == "completed",
        timeout=5.0,
        initial_interval=0.01,
        on_update=seen.append,
    )
    assert len(seen) == 2
    assert seen[-1]["status"] == "completed"


@pytest.mark.asyncio
async def test_wait_for_async_returns_when_terminal():
    states = iter(["running", "completed"])

    async def fetch():
        return {"status": next(states)}

    out = await wait_for_async(
        fetch=fetch,
        is_terminal=lambda d: d["status"] == "completed",
        timeout=5.0,
        initial_interval=0.01,
    )
    assert out["status"] == "completed"


@pytest.mark.asyncio
async def test_wait_for_async_raises_on_timeout():
    async def fetch():
        return {"status": "running"}

    with pytest.raises(NopaqueTimeoutError):
        await wait_for_async(
            fetch=fetch,
            is_terminal=lambda d: False,
            timeout=0.05,
            initial_interval=0.01,
        )
