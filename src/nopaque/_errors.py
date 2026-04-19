"""Error hierarchy for the Nopaque SDK."""
from __future__ import annotations


class NopaqueError(Exception):
    """Base class for all SDK errors."""


class NopaqueConfigError(NopaqueError):
    """Raised when the client is constructed with invalid configuration."""
