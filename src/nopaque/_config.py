"""Runtime configuration for Nopaque clients."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable

from ._errors import NopaqueConfigError

DEFAULT_BASE_URL = "https://api.nopaque.co.uk"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 3


@dataclass(frozen=True)
class NopaqueConfig:
    """Immutable client configuration.

    api_key is resolved in this order:
        1. explicit argument
        2. NOPAQUE_API_KEY environment variable
        3. raise NopaqueConfigError
    """

    api_key: str = ""
    base_url: str = ""
    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    default_headers: dict = field(default_factory=dict)
    on_retry: Callable[[int, Any, float], None] | None = None

    def __post_init__(self) -> None:
        resolved_key = self.api_key or os.environ.get("NOPAQUE_API_KEY", "")
        if not resolved_key:
            raise NopaqueConfigError(
                "No API key provided. Pass api_key=... or set NOPAQUE_API_KEY."
            )
        resolved_base = (
            self.base_url or os.environ.get("NOPAQUE_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        object.__setattr__(self, "api_key", resolved_key)
        object.__setattr__(self, "base_url", resolved_base)
