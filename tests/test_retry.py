import random

import pytest
from nopaque._retry import (
    compute_backoff,
    should_retry,
    RetryContext,
)
from nopaque._errors import (
    APIConnectionError,
    APITimeoutError,
    RateLimitError,
    ServerError,
    ConflictError,
    NotFoundError,
    ValidationError,
    AuthenticationError,
)


def test_backoff_monotonic_ignoring_jitter(monkeypatch):
    # Force the random multiplier to its upper bound so the test is deterministic
    # and only measures the raw exponential growth, ignoring jitter noise.
    monkeypatch.setattr(random, "uniform", lambda a, b: b)
    d0 = compute_backoff(0, base=0.5, cap=8.0, jitter=1.5)
    d1 = compute_backoff(1, base=0.5, cap=8.0, jitter=1.5)
    d2 = compute_backoff(2, base=0.5, cap=8.0, jitter=1.5)
    d3 = compute_backoff(3, base=0.5, cap=8.0, jitter=1.5)
    assert d0 <= d1 <= d2 <= d3


def test_backoff_capped():
    # very high attempt should still be capped
    d = compute_backoff(20, base=0.5, cap=8.0, jitter=1.0)
    assert d <= 8.0


def _api_err(cls, status):
    return cls(status=status, code=None, message="x", details=None, request_id=None, response=None)


def test_get_retries_on_429_5xx_connection_timeout():
    for err in [
        _api_err(RateLimitError, 429),
        _api_err(ServerError, 500),
        _api_err(ServerError, 502),
        _api_err(ServerError, 503),
        _api_err(ServerError, 504),
        APIConnectionError("x"),
        APITimeoutError("x"),
    ]:
        assert should_retry(method="GET", error=err, before_send=False), err


def test_get_does_not_retry_4xx_except_429():
    for err in [
        _api_err(ConflictError, 409),
        _api_err(NotFoundError, 404),
        _api_err(ValidationError, 400),
        _api_err(AuthenticationError, 401),
    ]:
        assert not should_retry(method="GET", error=err, before_send=False), err


def test_post_retries_429_and_pre_send_connection_only():
    # Yes
    assert should_retry(method="POST", error=_api_err(RateLimitError, 429), before_send=False)
    assert should_retry(method="POST", error=APIConnectionError("x"), before_send=True)
    # No
    assert not should_retry(method="POST", error=_api_err(ServerError, 500), before_send=False)
    assert not should_retry(method="POST", error=APIConnectionError("x"), before_send=False)
    assert not should_retry(method="POST", error=APITimeoutError("x"), before_send=False)
    assert not should_retry(method="POST", error=_api_err(ConflictError, 409), before_send=False)


def test_retry_context_tracks_attempts():
    ctx = RetryContext(max_retries=3)
    assert ctx.remaining() == 3
    ctx.record_attempt()
    assert ctx.remaining() == 2
    ctx.record_attempt()
    ctx.record_attempt()
    assert ctx.remaining() == 0
    assert ctx.exhausted()


def test_rate_limit_delay_uses_retry_after():
    err = RateLimitError(
        status=429, code=None, message="x", details=None,
        request_id=None, response=None, retry_after=5.0,
    )
    from nopaque._retry import delay_for
    d = delay_for(attempt=0, error=err, base=0.5, cap=8.0, jitter=1.0)
    assert d == 5.0


def test_delay_for_falls_back_to_backoff_if_no_retry_after():
    err = RateLimitError(
        status=429, code=None, message="x", details=None,
        request_id=None, response=None, retry_after=None,
    )
    from nopaque._retry import delay_for
    d = delay_for(attempt=0, error=err, base=0.5, cap=8.0, jitter=1.0)
    assert 0 < d <= 1.0  # base * 2^0 * jitter in [0.5, 1.5] -> [0.5, 0.75]
