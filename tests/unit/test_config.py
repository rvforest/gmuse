"""Unit tests for gmuse.config module."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from gmuse.config import (
    ALLOWED_CONFIG_KEYS,
    DEFAULTS,
    get_config_path,
    get_env_config,
    load_config,
    load_config_raw,
    merge_config,
    parse_config_value,
    validate_config,
)
from gmuse.exceptions import ConfigError


class TestGetConfigPath:
    """Tests for get_config_path function."""

    def test_default_path_without_xdg(self) -> None:
        """Test default config path when XDG_CONFIG_HOME is not set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            if "XDG_CONFIG_HOME" in os.environ:
                del os.environ["XDG_CONFIG_HOME"]
            path = get_config_path()
            assert path == Path.home() / ".config" / "gmuse" / "config.toml"

    def test_custom_xdg_path(self) -> None:
        """Test config path respects XDG_CONFIG_HOME."""
        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}):
            path = get_config_path()
            assert path == Path("/custom/config/gmuse/config.toml")


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_nonexistent_file(self) -> None:
        """Test loading config when file doesn't exist returns empty dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.toml"
            config = load_config(config_path)
            assert config == {}

    def test_load_valid_config(self) -> None:
        """Test loading valid TOML config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write('model = "gpt-4"\n')
            f.write("history_depth = 10\n")
            f.write('format = "conventional"\n')
            f.flush()
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert config["model"] == "gpt-4"
            assert config["history_depth"] == 10
            assert config["format"] == "conventional"
        finally:
            config_path.unlink()

    def test_load_invalid_toml_syntax(self) -> None:
        """Test loading config with invalid TOML syntax raises ConfigError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("invalid toml [[[")
            f.flush()
            config_path = Path(f.name)

        try:
            with pytest.raises(ConfigError, match="Invalid TOML syntax"):
                load_config(config_path)
        finally:
            config_path.unlink()


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_validate_empty_config(self) -> None:
        """Test validating empty config succeeds."""
        validate_config({})  # Should not raise

    def test_validate_valid_config(self) -> None:
        """Test validating valid config succeeds."""
        config = {
            "model": "gpt-4",
            "copy_to_clipboard": True,
            "learning_enabled": False,
            "history_depth": 10,
            "format": "conventional",
            "timeout": 60,
        }
        validate_config(config)  # Should not raise

    def test_validate_history_depth_negative(self) -> None:
        """Test validation fails for negative history_depth."""
        with pytest.raises(ConfigError, match="history_depth must be between 0 and 50"):
            validate_config({"history_depth": -1})

    def test_validate_history_depth_too_large(self) -> None:
        """Test validation fails for history_depth > 50."""
        with pytest.raises(ConfigError, match="history_depth must be between 0 and 50"):
            validate_config({"history_depth": 100})

    def test_validate_history_depth_wrong_type(self) -> None:
        """Test validation fails for non-integer history_depth."""
        with pytest.raises(ConfigError, match="history_depth must be an integer"):
            validate_config({"history_depth": "10"})

    def test_validate_invalid_format(self) -> None:
        """Test validation fails for invalid format."""
        with pytest.raises(ConfigError, match="format must be one of"):
            validate_config({"format": "invalid"})

    def test_validate_timeout_out_of_range(self) -> None:
        """Test validation fails for timeout out of range."""
        with pytest.raises(ConfigError, match="timeout must be between 5 and 300"):
            validate_config({"timeout": 1000})

    def test_validate_boolean_wrong_type(self) -> None:
        """Test validation fails for non-boolean flags."""
        with pytest.raises(ConfigError, match="copy_to_clipboard must be a boolean"):
            validate_config({"copy_to_clipboard": "yes"})

    def test_validate_model_wrong_type(self) -> None:
        """Test validation fails for non-string model."""
        with pytest.raises(ConfigError, match="model must be a string"):
            validate_config({"model": 123})

    def test_validate_provider_invalid(self) -> None:
        """Test validation fails for invalid provider value."""
        with pytest.raises(ConfigError, match="provider must be one of"):
            validate_config({"provider": "invalid-provider"})


class TestMergeConfig:
    """Tests for merge_config function."""

    def test_merge_defaults_only(self) -> None:
        """Test merging with no overrides returns defaults."""
        result = merge_config()
        assert result == DEFAULTS

    def test_merge_cli_overrides_all(self) -> None:
        """Test CLI args have highest priority."""
        cli_args = {"model": "cli-model", "provider": "openai"}
        config_file = {"model": "file-model"}
        env_vars = {"model": "env-model"}

        result = merge_config(
            cli_args=cli_args, config_file=config_file, env_vars=env_vars
        )
        assert result["model"] == "cli-model"

    def test_merge_env_overrides_config_file(self) -> None:
        """Test environment variables override config file."""
        config_file = {"model": "file-model", "provider": "gemini"}
        env_vars = {"model": "env-model"}

        result = merge_config(config_file=config_file, env_vars=env_vars)
        assert result["model"] == "env-model"

    def test_merge_env_overrides_defaults(self) -> None:
        """Test environment variables override defaults."""
        env_vars = {"model": "env-model", "provider": "openai"}

        result = merge_config(env_vars=env_vars)
        assert result["model"] == "env-model"

    def test_merge_preserves_unset_defaults(self) -> None:
        """Test merging preserves default values for unset keys."""
        cli_args = {"model": "gpt-4"}

        result = merge_config(cli_args=cli_args)
        assert result["model"] == "gpt-4"
        assert result["history_depth"] == DEFAULTS["history_depth"]
        assert result["format"] == DEFAULTS["format"]

    def test_merge_ignores_none_values(self) -> None:
        """Test merging ignores None values."""
        cli_args = {"model": None}

        result = merge_config(cli_args=cli_args)
        assert result["model"] == DEFAULTS["model"]

    def test_merge_provider_works(self) -> None:
        """Test provider from env/config/cli is used based on priority."""
        env_vars = {"provider": "gemini"}
        config_file = {"provider": "anthropic"}
        cli_args = {"provider": "openai"}

        result = merge_config(
            cli_args=cli_args, config_file=config_file, env_vars=env_vars
        )
        assert result["provider"] == "openai"


class TestGetEnvConfig:
    """Tests for get_env_config function."""

    def test_get_env_config_empty(self) -> None:
        """Test getting env config when no vars are set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = get_env_config()
            assert config == {}

    def test_get_env_config_model(self) -> None:
        """Test getting model from GMUSE_MODEL."""
        with mock.patch.dict(os.environ, {"GMUSE_MODEL": "gpt-4"}):
            config = get_env_config()
            assert config["model"] == "gpt-4"

    def test_get_env_config_format(self) -> None:
        """Test getting format from GMUSE_FORMAT."""
        with mock.patch.dict(os.environ, {"GMUSE_FORMAT": "conventional"}):
            config = get_env_config()
            assert config["format"] == "conventional"

    def test_get_env_config_history_depth(self) -> None:
        """Test getting history_depth from GMUSE_HISTORY_DEPTH."""
        with mock.patch.dict(os.environ, {"GMUSE_HISTORY_DEPTH": "10"}):
            config = get_env_config()
            assert config["history_depth"] == 10

    def test_get_env_config_invalid_integer(self) -> None:
        """Test invalid integer in env var is ignored."""
        with mock.patch.dict(os.environ, {"GMUSE_HISTORY_DEPTH": "invalid"}):
            config = get_env_config()
            assert "history_depth" not in config

    def test_get_env_config_boolean_true(self) -> None:
        """Test parsing boolean env vars as true."""
        with mock.patch.dict(os.environ, {"GMUSE_COPY": "1"}):
            config = get_env_config()
            assert config["copy_to_clipboard"] is True

    def test_get_env_config_boolean_false(self) -> None:
        """Test parsing boolean env vars as false."""
        with mock.patch.dict(os.environ, {"GMUSE_COPY": "0"}):
            config = get_env_config()
            assert config["copy_to_clipboard"] is False

        with mock.patch.dict(os.environ, {"GMUSE_COPY": "no"}):
            config = get_env_config()
            assert config["copy_to_clipboard"] is False


class TestNewConfigParameters:
    """Tests for new LLM and prompt configuration parameters."""

    def test_validate_temperature_valid(self) -> None:
        """Test validation succeeds for valid temperature."""
        validate_config({"temperature": 0.5})
        validate_config({"temperature": 0.0})
        validate_config({"temperature": 2.0})


class TestConfigHelpers:
    """Tests for new helper utilities used by the global config CLI."""

    def test_allowed_config_keys_contains_defaults(self) -> None:
        assert set(ALLOWED_CONFIG_KEYS) == set(DEFAULTS.keys())

    def test_load_config_raw_nonexistent_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing.toml"
            assert load_config_raw(missing) is None

    def test_load_config_requires_tomli(self) -> None:
        """If tomllib is not available, loading should raise a helpful error."""
        import importlib
        import gmuse.config as cfg

        # Simulate running under Python < 3.11 without tomli package
        orig_tomllib = cfg.tomllib
        cfg.tomllib = None  # type: ignore[assignment]
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".toml", delete=False
            ) as f:
                f.write('model = "gpt-4"\n')
                f.flush()
                config_path = Path(f.name)

            try:
                with pytest.raises(ConfigError, match="tomli package is required"):
                    load_config(config_path)
            finally:
                config_path.unlink()
        finally:
            cfg.tomllib = orig_tomllib

    def test_load_config_raw_unreadable_raises(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write('model = "gpt-4"\n')
            f.flush()
            config_path = Path(f.name)

        try:
            # Make read_text raise OSError
            original = Path.read_text

            def fake_read_text(self: Path, *args, **kwargs):  # type: ignore[no-untyped-def]
                if self == config_path:
                    raise OSError("Boom")
                return original(self, *args, **kwargs)

            try:
                with tempfile.TemporaryDirectory():
                    import gmuse.config as cfg

                    monkeypatch = pytest.MonkeyPatch()
                    monkeypatch.setattr(Path, "read_text", fake_read_text)
                    try:
                        with pytest.raises(
                            ConfigError, match="Cannot read config file"
                        ):
                            load_config_raw(config_path)
                    finally:
                        monkeypatch.undo()
            finally:
                pass
        finally:
            config_path.unlink()

    def test_parse_env_int_and_float_warn_on_invalid(self, caplog) -> None:
        from gmuse.config import _parse_env_int, _parse_env_float

        with mock.patch.dict(os.environ, {"GMUSE_TIMEOUT": "notanint"}):
            caplog.clear()
            res = _parse_env_int("GMUSE_TIMEOUT", "timeout")
            assert res is None
            assert any("Invalid GMUSE_TIMEOUT" in rec.message for rec in caplog.records)

        with mock.patch.dict(os.environ, {"GMUSE_TEMPERATURE": "notafloat"}):
            caplog.clear()
            res = _parse_env_float("GMUSE_TEMPERATURE", "temperature")
            assert res is None
            assert any(
                "Invalid GMUSE_TEMPERATURE" in rec.message for rec in caplog.records
            )

    def test_get_env_config_branch_max_length_invalid_warn(self, caplog) -> None:
        with mock.patch.dict(os.environ, {"GMUSE_BRANCH_MAX_LENGTH": "invalid"}):
            caplog.clear()
            cfg = get_env_config()
            assert "branch_max_length" not in cfg
            assert any(
                "Invalid GMUSE_BRANCH_MAX_LENGTH" in rec.message
                for rec in caplog.records
            )

    def test_tomli_import_fallback_when_running_py310(self, monkeypatch) -> None:
        """Ensure module gracefully handles absent tomli on Python 3.10 by setting tomllib=None."""
        import importlib
        import sys
        import builtins

        # Prepare environment to simulate Python 3.10
        monkeypatch.setattr(sys, "version_info", (3, 10))

        real_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "tomli":
                raise ImportError("no tomli")
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        # Reload module under simulated conditions
        original_modules = dict(sys.modules)
        if "gmuse.config" in sys.modules:
            del sys.modules["gmuse.config"]
        try:
            cfg = importlib.import_module("gmuse.config")
            assert cfg.tomllib is None
        finally:
            # Restore safely
            sys.modules.clear()
            sys.modules.update(original_modules)
            monkeypatch.setattr(builtins, "__import__", real_import)

    def test_atomic_write_text_cleanup_on_unlink_error(
        self, tmp_path, monkeypatch
    ) -> None:
        from gmuse.config import _atomic_write_text

        path = tmp_path / "config.toml"

        # Force os.replace to raise so we go into the OSError handling branch
        def fake_replace(src, dst):
            raise OSError("replace failed")

        monkeypatch.setattr(__import__("gmuse").config.os, "replace", fake_replace)

        # Make Path.unlink raise when called to hit the final except path
        def fake_unlink(self):
            raise OSError("unlink failed")

        monkeypatch.setattr(__import__("pathlib").Path, "unlink", fake_unlink)

        with pytest.raises(ConfigError, match="Cannot write config file"):
            _atomic_write_text(path, "text")

    def test_parse_config_value_bool(self) -> None:
        assert parse_config_value("copy_to_clipboard", "true") is True
        assert parse_config_value("copy_to_clipboard", "no") is False

    def test_parse_config_value_int_error(self) -> None:
        with pytest.raises(ConfigError, match="Cannot parse 'abc' as integer"):
            parse_config_value("history_depth", "abc")

    def test_validate_temperature_out_of_range(self) -> None:
        """Test validation fails for temperature out of range."""
        with pytest.raises(
            ConfigError, match="temperature must be between 0.0 and 2.0"
        ):
            validate_config({"temperature": -0.1})

        with pytest.raises(
            ConfigError, match="temperature must be between 0.0 and 2.0"
        ):
            validate_config({"temperature": 2.5})

    def test_validate_temperature_wrong_type(self) -> None:
        """Test validation fails for non-numeric temperature."""
        with pytest.raises(ConfigError, match="temperature must be a number"):
            validate_config({"temperature": "0.7"})

    def test_validate_max_tokens_valid(self) -> None:
        """Test validation succeeds for valid max_tokens."""
        validate_config({"max_tokens": 100})
        validate_config({"max_tokens": 1})
        validate_config({"max_tokens": 10000})

    def test_validate_max_tokens_out_of_range(self) -> None:
        """Test validation fails for max_tokens out of range."""
        with pytest.raises(ConfigError, match="max_tokens must be between"):
            validate_config({"max_tokens": 0})

        with pytest.raises(ConfigError, match="max_tokens must be between"):
            validate_config({"max_tokens": 10000001})

    def test_validate_max_tokens_wrong_type(self) -> None:
        """Test validation fails for non-integer max_tokens."""
        with pytest.raises(ConfigError, match="max_tokens must be an integer"):
            validate_config({"max_tokens": "500"})

    def test_validate_max_diff_bytes_valid(self) -> None:
        """Test validation succeeds for valid max_diff_bytes."""
        validate_config({"max_diff_bytes": 20000})
        validate_config({"max_diff_bytes": 1000})

    def test_validate_max_diff_bytes_out_of_range(self) -> None:
        """Test validation fails for max_diff_bytes out of range."""
        with pytest.raises(ConfigError, match="max_diff_bytes must be between"):
            validate_config({"max_diff_bytes": 100})

        with pytest.raises(ConfigError, match="max_diff_bytes must be between"):
            validate_config({"max_diff_bytes": 20000000})

    def test_validate_max_message_length_valid(self) -> None:
        """Test validation succeeds for valid max_message_length."""
        validate_config({"max_message_length": 1000})
        validate_config({"max_message_length": 10})

    def test_validate_max_message_length_out_of_range(self) -> None:
        """Test validation fails for max_message_length out of range."""
        with pytest.raises(ConfigError, match="max_message_length must be between"):
            validate_config({"max_message_length": 5})

        with pytest.raises(ConfigError, match="max_message_length must be between"):
            validate_config({"max_message_length": 15000})

    def test_validate_chars_per_token_valid(self) -> None:
        """Test validation succeeds for valid chars_per_token."""
        validate_config({"chars_per_token": 4})
        validate_config({"chars_per_token": 1})
        validate_config({"chars_per_token": 10})

    def test_validate_chars_per_token_out_of_range(self) -> None:
        """Test validation fails for chars_per_token out of range."""
        with pytest.raises(ConfigError, match="chars_per_token must be between"):
            validate_config({"chars_per_token": 0})

        with pytest.raises(ConfigError, match="chars_per_token must be between"):
            validate_config({"chars_per_token": 11})

    def test_get_env_config_temperature(self) -> None:
        """Test getting temperature from GMUSE_TEMPERATURE."""
        with mock.patch.dict(os.environ, {"GMUSE_TEMPERATURE": "0.3"}):
            config = get_env_config()
            assert config["temperature"] == 0.3

    def test_get_env_config_invalid_temperature(self) -> None:
        """Test invalid temperature in env var is ignored."""
        with mock.patch.dict(os.environ, {"GMUSE_TEMPERATURE": "invalid"}):
            config = get_env_config()
            assert "temperature" not in config

    def test_get_env_config_max_tokens(self) -> None:
        """Test getting max_tokens from GMUSE_MAX_TOKENS."""
        with mock.patch.dict(os.environ, {"GMUSE_MAX_TOKENS": "200"}):
            config = get_env_config()
            assert config["max_tokens"] == 200

    def test_get_env_config_max_diff_bytes(self) -> None:
        """Test getting max_diff_bytes from GMUSE_MAX_DIFF_BYTES."""
        with mock.patch.dict(os.environ, {"GMUSE_MAX_DIFF_BYTES": "30000"}):
            config = get_env_config()
            assert config["max_diff_bytes"] == 30000

    def test_get_env_config_max_message_length(self) -> None:
        """Test getting max_message_length from GMUSE_MAX_MESSAGE_LENGTH."""
        with mock.patch.dict(os.environ, {"GMUSE_MAX_MESSAGE_LENGTH": "500"}):
            config = get_env_config()
            assert config["max_message_length"] == 500

    def test_get_env_config_chars_per_token(self) -> None:
        """Test getting chars_per_token from GMUSE_CHARS_PER_TOKEN."""
        with mock.patch.dict(os.environ, {"GMUSE_CHARS_PER_TOKEN": "3"}):
            config = get_env_config()
            assert config["chars_per_token"] == 3

    def test_defaults_include_new_parameters(self) -> None:
        """Test that DEFAULTS dict includes new parameters."""
        assert "temperature" in DEFAULTS
        assert "max_tokens" in DEFAULTS
        assert "max_diff_bytes" in DEFAULTS
        assert "max_message_length" in DEFAULTS
        assert "chars_per_token" in DEFAULTS
        assert DEFAULTS["temperature"] == 0.7
        assert DEFAULTS["max_tokens"] == 500
        assert DEFAULTS["max_diff_bytes"] == 20000
        assert DEFAULTS["max_message_length"] == 1000
        assert DEFAULTS["chars_per_token"] == 4

    def test_merge_config_with_new_parameters(self) -> None:
        """Test merging configuration with new parameters."""
        cli_args = {"temperature": 0.3, "max_tokens": 200}
        config_file = {"temperature": 0.5, "max_diff_bytes": 30000}
        env_vars = {"temperature": 0.9, "max_tokens": 300, "max_message_length": 500}

        result = merge_config(
            cli_args=cli_args, config_file=config_file, env_vars=env_vars
        )
        # CLI should win
        assert result["temperature"] == 0.3
        assert result["max_tokens"] == 200
        # Config file should override env
        assert result["max_diff_bytes"] == 30000
        # Env should override default
        assert result["max_message_length"] == 500
        # Default should be used
        assert result["chars_per_token"] == 4
