import pytest
from nopaque._errors import (
    NopaqueError,
    NopaqueAPIError,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    ValidationError,
    ConflictError,
    RateLimitError,
    ServerError,
    APIConnectionError,
    APITimeoutError,
    NopaqueConfigError,
    NopaqueTimeoutError,
    classify_status,
)


def test_hierarchy():
    assert issubclass(NopaqueAPIError, NopaqueError)
    assert issubclass(AuthenticationError, NopaqueAPIError)
    assert issubclass(PermissionError, NopaqueAPIError)
    assert issubclass(NotFoundError, NopaqueAPIError)
    assert issubclass(ValidationError, NopaqueAPIError)
    assert issubclass(ConflictError, NopaqueAPIError)
    assert issubclass(RateLimitError, NopaqueAPIError)
    assert issubclass(ServerError, NopaqueAPIError)
    assert issubclass(APIConnectionError, NopaqueError)
    assert issubclass(APITimeoutError, NopaqueError)
    assert issubclass(NopaqueConfigError, NopaqueError)
    assert issubclass(NopaqueTimeoutError, NopaqueError)


def test_api_error_carries_metadata():
    err = NopaqueAPIError(
        status=404,
        code="mapping_not_found",
        message="Job not found",
        details={"id": "x"},
        request_id="req_123",
        response=None,
    )
    assert err.status == 404
    assert err.code == "mapping_not_found"
    assert err.details == {"id": "x"}
    assert err.request_id == "req_123"
    assert str(err) == "Job not found"


def test_rate_limit_error_retry_after():
    err = RateLimitError(
        status=429,
        code=None,
        message="rate limit exceeded",
        details=None,
        request_id=None,
        response=None,
        retry_after=12.5,
    )
    assert err.retry_after == 12.5


@pytest.mark.parametrize("status,cls", [
    (400, ValidationError),
    (401, AuthenticationError),
    (403, PermissionError),
    (404, NotFoundError),
    (409, ConflictError),
    (429, RateLimitError),
    (500, ServerError),
    (502, ServerError),
    (503, ServerError),
    (504, ServerError),
])
def test_classify_status(status, cls):
    assert classify_status(status) is cls


def test_classify_status_unknown_falls_back_to_api_error():
    assert classify_status(418) is NopaqueAPIError
