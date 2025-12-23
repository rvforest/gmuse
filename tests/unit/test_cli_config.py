"""Unit tests for `gmuse config` CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from gmuse.cli.main import app
from gmuse.config import parse_config_value, DEFAULTS

runner = CliRunner(mix_stderr=False)


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
    # The CLI should include an example hint for integer-like keys
    assert "Example: gmuse config set history_depth 10" in result.stderr


def test_config_set_update_config_key_raises_shows_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    # Force update_config_key to raise a ConfigError
    import gmuse.cli.config as cli_cfg

    def fake_update(key, value):
        raise __import__("gmuse").exceptions.ConfigError("Nope")

    monkeypatch.setattr(cli_cfg, "update_config_key", fake_update)

    result = runner.invoke(app, ["config", "set", "format", "conventional"])

    assert result.exit_code == 1
    assert "Check directory permissions and try again." in result.stderr


def test_config_set_invalid_format_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "set", "format", "invalid-format"])

    assert result.exit_code == 1
    assert "Invalid format: 'invalid-format'" in result.stderr
    assert "freeform, conventional, gitmoji" in result.stderr


def test_config_set_invalid_provider_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "set", "provider", "nope"])

    assert result.exit_code == 1
    assert "Invalid provider: 'nope'" in result.stderr
    # Ensure providers list is present
    assert "openai" in result.stderr


def test_config_set_temperature_out_of_range_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    # Provide a numeric value that is out of the allowed float range
    result = runner.invoke(app, ["config", "set", "temperature", "100"])

    assert result.exit_code == 1
    assert "temperature must be between" in result.stderr
    assert "Allowed range: 0.0-2.0" in result.stderr


def test_parse_config_value_none_and_bool_variants_and_unknown_and_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # None values for optional strings
    assert parse_config_value("model", "none") is None
    assert parse_config_value("model", "Null") is None

    # Boolean variants
    assert parse_config_value("copy_to_clipboard", "1") is True
    assert parse_config_value("copy_to_clipboard", "yes") is True

    # Unknown key errors
    from gmuse.exceptions import ConfigError

    with pytest.raises(ConfigError, match="Unknown configuration key"):
        parse_config_value("not-a-key", "value")

    # Unsupported configuration type (hack by temporarily injecting a list default)
    monkeypatch.setitem(DEFAULTS, "weird", [])
    try:
        with pytest.raises(ConfigError, match="Unsupported configuration type"):
            parse_config_value("weird", "x")
    finally:
        del DEFAULTS["weird"]


def test_config_set_timeout_and_max_tokens_parse_examples_and_timeout_out_of_range(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    # Timeout parse error example
    result = runner.invoke(app, ["config", "set", "timeout", "notanumber"])
    assert result.exit_code == 1
    assert "Cannot parse 'notanumber' as integer" in result.stderr
    assert "Example: gmuse config set timeout 10" in result.stderr

    # max_tokens parse error example
    result = runner.invoke(app, ["config", "set", "max_tokens", "notanumber"])
    assert result.exit_code == 1
    assert "Cannot parse 'notanumber' as integer" in result.stderr
    assert "Example: gmuse config set max_tokens 10" in result.stderr

    # Timeout out of range should include allowed range hint
    result = runner.invoke(app, ["config", "set", "timeout", "1000"])
    assert result.exit_code == 1
    assert "Allowed range: 5-300" in result.stderr
