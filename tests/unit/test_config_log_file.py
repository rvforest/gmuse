"""Tests for GMUSE_LOG_FILE integration in config loading.

Covers:
- `get_env_config` reads `GMUSE_LOG_FILE` into `log_file`
- `merge_config` preserves `log_file` when provided via env_vars
- `gmuse.cli.main._load_config` picks up `GMUSE_LOG_FILE` from the environment
"""

from __future__ import annotations

import os

import pytest

from gmuse import config


def test_get_env_config_reads_log_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GMUSE_LOG_FILE", "/tmp/gmuse-env.log")
    env = config.get_env_config()
    assert env.get("log_file") == "/tmp/gmuse-env.log"


def test_merge_config_includes_log_file_from_env() -> None:
    env_vars = {"log_file": "/tmp/gmuse-merged.log"}
    merged = config.merge_config(cli_args={}, config_file={}, env_vars=env_vars)
    assert merged.get("log_file") == "/tmp/gmuse-merged.log"


def test__load_config_includes_log_file_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure top-level loader picks up the env var and returns it in final config
    monkeypatch.setenv("GMUSE_LOG_FILE", "/tmp/gmuse-main.log")

    # Avoid reading any real config file
    import gmuse.cli.main as main_mod

    monkeypatch.setattr(main_mod, "load_config", lambda: {})

    cfg = main_mod._load_config()
    assert cfg.get("log_file") == "/tmp/gmuse-main.log"
    # Clean up
    monkeypatch.delenv("GMUSE_LOG_FILE", raising=False)
