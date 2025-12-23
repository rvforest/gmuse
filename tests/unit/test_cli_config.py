"""Unit tests for `gmuse config` CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from gmuse.cli.main import app

runner = CliRunner()


def test_config_view_no_file_shows_location_and_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 0
    assert "Global config file:" in result.stdout
    assert "No global configuration file found." in result.stdout
    assert "--- Effective Configuration ---" in result.stdout


def test_config_view_invalid_toml_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = tmp_path / "gmuse" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("invalid toml [[[\n", encoding="utf-8")

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 1
    assert "Error: Invalid TOML syntax" in result.stderr
    assert "Fix the syntax error" in result.stderr


def test_config_set_unknown_key_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "set", "unknown_key", "value"])

    assert result.exit_code == 1
    assert "Error: Unknown configuration key" in result.stderr
    assert "Valid keys:" in result.stderr


def test_config_set_type_parse_error_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "set", "history_depth", "abc"])

    assert result.exit_code == 1
    assert "Cannot parse 'abc' as integer" in result.stderr
