"""Unit tests for gmuse.config module."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from gmuse.config import (
    DEFAULTS,
    get_config_path,
    get_env_config,
    load_config,
    merge_config,
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

        result = merge_config(cli_args=cli_args, config_file=config_file, env_vars=env_vars)
        assert result["model"] == "cli-model"

    def test_merge_config_file_overrides_env(self) -> None:
        """Test config file overrides environment variables."""
        config_file = {"model": "file-model", "provider": "gemini"}
        env_vars = {"model": "env-model"}

        result = merge_config(config_file=config_file, env_vars=env_vars)
        assert result["model"] == "file-model"

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

        result = merge_config(cli_args=cli_args, config_file=config_file, env_vars=env_vars)
        assert result["provider"] == "openai"


class TestGetEnvConfig:
    """Tests for get_env_config function."""

    def test_get_env_config_empty(self) -> None:
        """Test getting env config when no vars are set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = get_env_config()
            assert config == {}

    def test_get_env_config_provider(self) -> None:
        """Test provider read from GMUSE_PROVIDER env var."""
        with mock.patch.dict(os.environ, {"GMUSE_PROVIDER": "gemini"}):
            config = get_env_config()
            assert config["provider"] == "gemini"

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

