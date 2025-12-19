"""Tests for top-level env var handling in `gmuse.cli.main`.

These ensure that when `git-completions-run` is present in argv and no
`GMUSE_LOG_FILE` is configured, debug-related env vars are removed to avoid
polluting JSON output from the completion helper.
"""

from __future__ import annotations

import importlib
import os
import sys

import pytest


def _reload_main_module() -> None:
    # Import and reload the module so top-level logic is executed
    import gmuse.cli.main as main_mod

    importlib.reload(main_mod)


def test_git_completions_run_removes_debug_env_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GMUSE_DEBUG", "1")
    monkeypatch.setenv("GMUSE_LOG_LEVEL", "DEBUG")
    monkeypatch.delenv("GMUSE_LOG_FILE", raising=False)

    monkeypatch.setattr(sys, "argv", ["gmuse", "git-completions-run"])

    _reload_main_module()

    assert "GMUSE_DEBUG" not in os.environ
    assert "GMUSE_LOG_LEVEL" not in os.environ


def test_git_completions_run_keeps_debug_env_when_log_file_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # If GMUSE_LOG_FILE is set we should not delete the debug env vars
    monkeypatch.setenv("GMUSE_DEBUG", "1")
    monkeypatch.setenv("GMUSE_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("GMUSE_LOG_FILE", "/tmp/gmuse.log")

    monkeypatch.setattr(sys, "argv", ["gmuse", "git-completions-run"])

    _reload_main_module()

    assert os.environ.get("GMUSE_DEBUG") == "1"
    assert os.environ.get("GMUSE_LOG_LEVEL") == "DEBUG"
