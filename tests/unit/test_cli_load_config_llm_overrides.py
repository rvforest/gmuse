"""Tests for `_load_config` CLI overrides.

These specifically exercise the CLI argument-to-config merge behavior for
LLM-related parameters that are optional (only applied when not None).
"""

from __future__ import annotations

import pytest


def test__load_config_applies_temperature_and_max_tokens_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import gmuse.cli.main as main_mod
    from gmuse.cli import config_resolution as cli_config

    # Avoid reading any real config file or environment variables.
    monkeypatch.setattr(cli_config, "load_config", lambda: {})
    monkeypatch.setattr(cli_config, "get_env_config", lambda: {})

    cfg = main_mod._load_config(temperature=0.8, max_tokens=500)

    assert cfg["temperature"] == 0.8
    assert cfg["max_tokens"] == 500


def test__load_config_applies_max_diff_bytes_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import gmuse.cli.main as main_mod
    from gmuse.cli import config_resolution as cli_config

    # Avoid reading any real config file or environment variables.
    monkeypatch.setattr(cli_config, "load_config", lambda: {})
    monkeypatch.setattr(cli_config, "get_env_config", lambda: {})

    cfg = main_mod._load_config(max_diff_bytes=5000)

    assert cfg["max_diff_bytes"] == 5000
