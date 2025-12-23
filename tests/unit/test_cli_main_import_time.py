"""Unit tests for import-time behaviors in gmuse.cli.main.

These are hard to hit through normal imports because the behavior runs at
module import time and depends on sys.argv and environment variables.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest


def _exec_cli_main_module(tmp_name: str, module_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(tmp_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def test_import_time_suppresses_debug_env_for_completions_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When running git-completions-run without GMUSE_LOG_FILE, debug env is stripped."""

    monkeypatch.setenv("GMUSE_DEBUG", "1")
    monkeypatch.setenv("GMUSE_LOG_LEVEL", "DEBUG")
    monkeypatch.delenv("GMUSE_LOG_FILE", raising=False)

    monkeypatch.setattr(sys, "argv", ["gmuse", "git-completions-run", "--shell", "zsh"])

    module_path = Path(__file__).parents[2] / "src" / "gmuse" / "cli" / "main.py"
    _exec_cli_main_module("gmuse_cli_main_import_test_1", module_path)

    assert "GMUSE_DEBUG" not in os.environ
    assert "GMUSE_LOG_LEVEL" not in os.environ


def test_import_time_does_not_suppress_when_log_file_is_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When GMUSE_LOG_FILE is set, debug env is preserved even for completions-run."""

    monkeypatch.setenv("GMUSE_DEBUG", "1")
    monkeypatch.setenv("GMUSE_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("GMUSE_LOG_FILE", "/tmp/gmuse.log")

    monkeypatch.setattr(sys, "argv", ["gmuse", "git-completions-run", "--shell", "zsh"])

    module_path = Path(__file__).parents[2] / "src" / "gmuse" / "cli" / "main.py"
    _exec_cli_main_module("gmuse_cli_main_import_test_2", module_path)

    assert os.environ.get("GMUSE_DEBUG") == "1"
    assert os.environ.get("GMUSE_LOG_LEVEL") == "DEBUG"
