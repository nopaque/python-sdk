"""Compose the User-Agent header."""
from __future__ import annotations

import platform

import httpx

from ._version import __version__


def compose_user_agent() -> str:
    """Build a stable User-Agent string.

    Format: nopaque-python/<ver> (python/<X.Y>; httpx/<Z>)
    """
    py_ver = f"{platform.python_version()}"
    return (
        f"nopaque-python/{__version__} "
        f"(python/{py_ver}; httpx/{httpx.__version__})"
    )
