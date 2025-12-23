"""Unit tests for global config write helpers."""

from __future__ import annotations

import pytest

from gmuse.config import parse_config_value
from gmuse.exceptions import ConfigError


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("false", False),
        ("0", False),
        ("no", False),
    ],
)
def test_parse_config_value_bool(raw: str, expected: bool) -> None:
    assert parse_config_value("include_branch", raw) is expected


def test_parse_config_value_int() -> None:
    assert parse_config_value("history_depth", "10") == 10


def test_parse_config_value_float() -> None:
    assert parse_config_value("temperature", "0.3") == 0.3


@pytest.mark.parametrize("raw", ["null", "none", "NULL", " None "])
def test_parse_config_value_optional_string_null(raw: str) -> None:
    assert parse_config_value("model", raw) is None


def test_parse_config_value_optional_string_value() -> None:
    assert parse_config_value("model", "gpt-4o-mini") == "gpt-4o-mini"


def test_parse_config_value_unknown_key_errors() -> None:
    with pytest.raises(ConfigError, match="Unknown configuration key"):
        parse_config_value("unknown_key", "value")


def test_parse_config_value_invalid_int_errors() -> None:
    with pytest.raises(ConfigError, match="Cannot parse 'abc' as integer"):
        parse_config_value("history_depth", "abc")


def test_parse_config_value_invalid_float_errors() -> None:
    with pytest.raises(ConfigError, match="Cannot parse 'abc' as number"):
        parse_config_value("temperature", "abc")


def test_parse_config_value_invalid_bool_errors() -> None:
    with pytest.raises(ConfigError, match="must be a boolean"):
        parse_config_value("copy_to_clipboard", "maybe")
