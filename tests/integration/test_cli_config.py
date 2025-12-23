"""Integration tests for `gmuse config` commands."""

from __future__ import annotations

import builtins
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

import gmuse.config as gmuse_config
from gmuse.cli.main import app

runner = CliRunner()


def _config_path(xdg_home: Path) -> Path:
    return xdg_home / "gmuse" / "config.toml"


def test_config_view_no_config_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 0
    assert str(_config_path(tmp_path)) in result.stdout
    assert "No global configuration file found." in result.stdout
    assert "--- Effective Configuration ---" in result.stdout


def test_config_view_existing_config_file_shows_contents_and_merged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        'model = "gpt-4o-mini"\nformat = "conventional"\n', encoding="utf-8"
    )

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 0
    assert "--- File Contents ---" in result.stdout
    assert 'model = "gpt-4o-mini"' in result.stdout
    assert "--- Effective Configuration ---" in result.stdout
    assert "model" in result.stdout
    assert "config file" in result.stdout


def test_config_view_invalid_toml_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("invalid toml [[[\n", encoding="utf-8")

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 1
    assert "Error: Invalid TOML syntax" in result.stderr


def test_config_view_unreadable_file_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('model = "gpt-4"\n', encoding="utf-8")

    # Simulate permission error for both raw-view and tomllib load.
    original_read_text = Path.read_text

    def fake_read_text(self: Path, *args, **kwargs):  # type: ignore[no-untyped-def]
        if self == config_path:
            raise PermissionError("Permission denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    original_open = builtins.open

    def fake_open(file, mode="r", *args, **kwargs):  # type: ignore[no-untyped-def]
        if Path(file) == config_path and "r" in mode:
            raise PermissionError("Permission denied")
        return original_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 1
    assert "Error: Cannot read config file" in result.stderr


def test_config_set_creates_directories_and_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "set", "format", "conventional"])

    assert result.exit_code == 0
    assert _config_path(tmp_path).exists()
    assert "Set 'format'" in result.stdout


def test_config_set_then_view_persists_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    set_result = runner.invoke(app, ["config", "set", "history_depth", "15"])
    assert set_result.exit_code == 0

    view_result = runner.invoke(app, ["config", "view"])
    assert view_result.exit_code == 0
    assert "history_depth = 15" in view_result.stdout


def test_config_set_unknown_key_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "set", "unknown_key", "value"])

    assert result.exit_code == 1
    assert "Unknown configuration key" in result.stderr


def test_config_set_invalid_value_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "set", "history_depth", "100"])

    assert result.exit_code == 1
    assert "history_depth must be between" in result.stderr
    assert "Allowed range: 0-50" in result.stderr


def test_config_set_unwritable_file_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    # Ensure the directory exists; then force writes to fail.
    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    def fake_replace(src, dst):  # type: ignore[no-untyped-def]
        raise PermissionError("Permission denied")

    monkeypatch.setattr(gmuse_config.os, "replace", fake_replace)

    result = runner.invoke(app, ["config", "set", "format", "conventional"])

    assert result.exit_code == 1
    assert "Error: Cannot write config file" in result.stderr


def test_config_view_highlights_env_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("GMUSE_INCLUDE_BRANCH", "true")

    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("include_branch = false\n", encoding="utf-8")

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 0
    assert "⚠ overrides file" in result.stdout


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="Platform-specific permission semantics"
)
def test_config_set_preserves_unrelated_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        '# comment\n[section]\nother = 1\nformat = "freeform"\n',
        encoding="utf-8",
    )

    set_result = runner.invoke(app, ["config", "set", "format", "conventional"])
    assert set_result.exit_code == 0

    text = config_path.read_text(encoding="utf-8")
    assert "[section]" in text
    assert "other = 1" in text
