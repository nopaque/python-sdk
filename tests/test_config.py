import pytest

from nopaque._config import NopaqueConfig
from nopaque._errors import NopaqueConfigError


def test_config_uses_explicit_api_key():
    cfg = NopaqueConfig(api_key="nop_live_abc")
    assert cfg.api_key == "nop_live_abc"


def test_config_reads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("NOPAQUE_API_KEY", "nop_live_env")
    cfg = NopaqueConfig()
    assert cfg.api_key == "nop_live_env"


def test_config_explicit_key_overrides_env(monkeypatch):
    monkeypatch.setenv("NOPAQUE_API_KEY", "env_value")
    cfg = NopaqueConfig(api_key="explicit_value")
    assert cfg.api_key == "explicit_value"


def test_config_raises_if_no_api_key(monkeypatch):
    monkeypatch.delenv("NOPAQUE_API_KEY", raising=False)
    with pytest.raises(NopaqueConfigError):
        NopaqueConfig()


def test_config_default_base_url(monkeypatch):
    monkeypatch.delenv("NOPAQUE_BASE_URL", raising=False)
    cfg = NopaqueConfig(api_key="k")
    assert cfg.base_url == "https://api.nopaque.co.uk"


def test_config_base_url_from_env(monkeypatch):
    monkeypatch.setenv("NOPAQUE_BASE_URL", "https://api.dev.nopaque.co.uk")
    cfg = NopaqueConfig(api_key="k")
    assert cfg.base_url == "https://api.dev.nopaque.co.uk"


def test_config_trailing_slash_stripped():
    cfg = NopaqueConfig(api_key="k", base_url="https://api.nopaque.co.uk/")
    assert cfg.base_url == "https://api.nopaque.co.uk"


def test_config_defaults():
    cfg = NopaqueConfig(api_key="k")
    assert cfg.timeout == 60.0
    assert cfg.max_retries == 3
    assert cfg.default_headers == {}
