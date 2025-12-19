"""Extra unit tests for gmuse.config to improve coverage.

Covers:
- XDG config path handling
- TOML error handling and missing tomllib
- Validation helpers raising ConfigError on bad input
- Unknown keys warning
"""

from __future__ import annotations

from pathlib import Path

import os
import sys
import textwrap
import pytest

from gmuse import config
from gmuse.exceptions import ConfigError


def test_get_config_path_uses_xdg(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    got = config.get_config_path()
    assert got == tmp_path / "gmuse" / "config.toml"


def test_load_config_invalid_toml(tmp_path: Path) -> None:
    bad = tmp_path / "bad.toml"
    bad.write_text("this is not = valid toml [")

    with pytest.raises(ConfigError) as exc:
        config.load_config(config_path=bad)
    assert "Invalid TOML syntax" in str(exc.value)


def test_load_config_requires_tomli_when_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Simulate environment where tomllib isn't available (Python <3.11 scenario)
    # Ensure we hit the explicit ConfigError about installing tomli
    good = tmp_path / "good.toml"
    good.write_text(
        textwrap.dedent("""
        model = "gpt-4"
    """)
    )

    monkeypatch.setattr(config, "tomllib", None)

    with pytest.raises(ConfigError) as exc:
        config.load_config(config_path=good)

    assert "tomli package is required" in str(exc.value)


@pytest.mark.parametrize(
    "cfg",
    [
        {"history_depth": "a"},
        {"history_depth": -1},
    ],
)
def test_validate_config_history_depth_errors(cfg: dict) -> None:
    with pytest.raises(ConfigError):
        config.validate_config(cfg)


@pytest.mark.parametrize(
    "cfg",
    [
        {"format": 1},
        {"format": "nonsense"},
        {"provider": 123},
    ],
)
def test_validate_config_string_choices_errors(cfg: dict) -> None:
    with pytest.raises(ConfigError):
        config.validate_config(cfg)


@pytest.mark.parametrize(
    "cfg", [{"copy_to_clipboard": "yes"}, {"learning_enabled": "true"}]
)
def test_validate_config_boolean_errors(cfg: dict) -> None:
    with pytest.raises(ConfigError):
        config.validate_config(cfg)


def test_validate_config_optional_string_errors() -> None:
    with pytest.raises(ConfigError):
        config.validate_config({"model": 123})


def test_validate_config_unknown_keys_logged(caplog) -> None:
    caplog.clear()
    config.validate_config({"foo": "bar"})
    assert "Unknown config keys" in caplog.text
