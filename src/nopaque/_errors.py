"""Error hierarchy for the Nopaque SDK."""
from __future__ import annotations

from typing import Any, Dict, Optional, Type


class NopaqueError(Exception):
    """Base class for all SDK errors."""


class NopaqueConfigError(NopaqueError):
    """Raised when the client is constructed with invalid configuration."""


class NopaqueTimeoutError(NopaqueError):
    """Raised when a wait_for_complete helper exceeds its deadline."""


class APIConnectionError(NopaqueError):
    """Raised when the SDK cannot reach the API (DNS, TCP reset, etc.)."""

    def __init__(self, message: str, *, cause: Optional[BaseException] = None) -> None:
        super().__init__(message)
        self.__cause__ = cause


class APITimeoutError(NopaqueError):
    """Raised when an HTTP request exceeds its per-request timeout."""


class NopaqueAPIError(NopaqueError):
    """Raised when the API returns a non-2xx HTTP response.

    Subclasses correspond to specific status codes; this base class catches
    unknown statuses (e.g. 418).
    """

    def __init__(
        self,
        *,
        status: int,
        code: Optional[str],
        message: str,
        details: Optional[dict] = None,
        request_id: Optional[str] = None,
        response: Any = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details
        self.request_id = request_id
        self.response = response


class ValidationError(NopaqueAPIError):
    """400 Bad Request - the server rejected the request body or params."""


class AuthenticationError(NopaqueAPIError):
    """401 Unauthorized - missing or invalid API key."""


class PermissionError(NopaqueAPIError):
    """403 Forbidden - API key lacks permission for this operation."""


class NotFoundError(NopaqueAPIError):
    """404 Not Found."""


class ConflictError(NopaqueAPIError):
    """409 Conflict - business-state conflict (e.g. job already running)."""


class RateLimitError(NopaqueAPIError):
    """429 Too Many Requests. Carries retry_after when the server provides it."""

    def __init__(
        self,
        *,
        status: int,
        code: Optional[str],
        message: str,
        details: Optional[dict] = None,
        request_id: Optional[str] = None,
        response: Any = None,
        retry_after: Optional[float] = None,
    ) -> None:
        super().__init__(
            status=status,
            code=code,
            message=message,
            details=details,
            request_id=request_id,
            response=response,
        )
        self.retry_after = retry_after


class ServerError(NopaqueAPIError):
    """5xx - server-side failure."""


_STATUS_MAP: Dict[int, Type[NopaqueAPIError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: PermissionError,
    404: NotFoundError,
    409: ConflictError,
    429: RateLimitError,
}


def classify_status(status: int) -> Type[NopaqueAPIError]:
    """Return the most specific NopaqueAPIError subclass for a given HTTP status."""
    if status in _STATUS_MAP:
        return _STATUS_MAP[status]
    if 500 <= status < 600:
        return ServerError
    return NopaqueAPIError
