"""Unit tests for branch-related configuration options."""

import os
from unittest import mock

import pytest

from gmuse.config import (
    BRANCH_MAX_LENGTH_MAX,
    BRANCH_MAX_LENGTH_MIN,
    DEFAULTS,
    get_env_config,
    validate_config,
)
from gmuse.exceptions import ConfigError


class TestBranchConfigDefaults:
    """Tests for branch configuration defaults."""

    def test_include_branch_default(self) -> None:
        """Test that include_branch defaults to False."""
        assert DEFAULTS["include_branch"] is False

    def test_branch_max_length_default(self) -> None:
        """Test that branch_max_length defaults to 60."""
        assert DEFAULTS["branch_max_length"] == 60


class TestValidateBranchConfig:
    """Tests for branch configuration validation."""

    def test_validate_include_branch_true(self) -> None:
        """Test validation succeeds for include_branch=True."""
        config = {"include_branch": True}
        validate_config(config)  # Should not raise

    def test_validate_include_branch_false(self) -> None:
        """Test validation succeeds for include_branch=False."""
        config = {"include_branch": False}
        validate_config(config)  # Should not raise

    def test_validate_include_branch_wrong_type(self) -> None:
        """Test validation fails for non-boolean include_branch."""
        with pytest.raises(ConfigError, match="include_branch must be a boolean"):
            validate_config({"include_branch": "yes"})

    def test_validate_branch_max_length_valid(self) -> None:
        """Test validation succeeds for valid branch_max_length."""
        config = {"branch_max_length": 60}
        validate_config(config)  # Should not raise

    def test_validate_branch_max_length_min(self) -> None:
        """Test validation succeeds for minimum branch_max_length."""
        config = {"branch_max_length": BRANCH_MAX_LENGTH_MIN}
        validate_config(config)  # Should not raise

    def test_validate_branch_max_length_max(self) -> None:
        """Test validation succeeds for maximum branch_max_length."""
        config = {"branch_max_length": BRANCH_MAX_LENGTH_MAX}
        validate_config(config)  # Should not raise

    def test_validate_branch_max_length_too_small(self) -> None:
        """Test validation fails for branch_max_length below minimum."""
        with pytest.raises(
            ConfigError, 
            match=f"branch_max_length must be between {BRANCH_MAX_LENGTH_MIN} and {BRANCH_MAX_LENGTH_MAX}"
        ):
            validate_config({"branch_max_length": BRANCH_MAX_LENGTH_MIN - 1})

    def test_validate_branch_max_length_too_large(self) -> None:
        """Test validation fails for branch_max_length above maximum."""
        with pytest.raises(
            ConfigError, 
            match=f"branch_max_length must be between {BRANCH_MAX_LENGTH_MIN} and {BRANCH_MAX_LENGTH_MAX}"
        ):
            validate_config({"branch_max_length": BRANCH_MAX_LENGTH_MAX + 1})

    def test_validate_branch_max_length_wrong_type(self) -> None:
        """Test validation fails for non-integer branch_max_length."""
        with pytest.raises(ConfigError, match="branch_max_length must be an integer"):
            validate_config({"branch_max_length": "60"})

    def test_validate_complete_branch_config(self) -> None:
        """Test validation succeeds for complete branch configuration."""
        config = {
            "include_branch": True,
            "branch_max_length": 80,
            "model": "gpt-4",
            "format": "conventional",
        }
        validate_config(config)  # Should not raise


class TestEnvBranchConfig:
    """Tests for branch configuration from environment variables."""

    def test_env_include_branch_true(self) -> None:
        """Test loading include_branch=true from environment."""
        with mock.patch.dict(os.environ, {"GMUSE_INCLUDE_BRANCH": "true"}):
            config = get_env_config()
            assert config["include_branch"] is True

    def test_env_include_branch_1(self) -> None:
        """Test loading include_branch=1 from environment."""
        with mock.patch.dict(os.environ, {"GMUSE_INCLUDE_BRANCH": "1"}):
            config = get_env_config()
            assert config["include_branch"] is True

    def test_env_include_branch_yes(self) -> None:
        """Test loading include_branch=yes from environment."""
        with mock.patch.dict(os.environ, {"GMUSE_INCLUDE_BRANCH": "yes"}):
            config = get_env_config()
            assert config["include_branch"] is True

    def test_env_include_branch_false(self) -> None:
        """Test loading include_branch=false from environment."""
        with mock.patch.dict(os.environ, {"GMUSE_INCLUDE_BRANCH": "false"}):
            config = get_env_config()
            assert config["include_branch"] is False

    def test_env_include_branch_0(self) -> None:
        """Test loading include_branch=0 from environment."""
        with mock.patch.dict(os.environ, {"GMUSE_INCLUDE_BRANCH": "0"}):
            config = get_env_config()
            assert config["include_branch"] is False

    def test_env_branch_max_length(self) -> None:
        """Test loading branch_max_length from environment."""
        with mock.patch.dict(os.environ, {"GMUSE_BRANCH_MAX_LENGTH": "100"}):
            config = get_env_config()
            assert config["branch_max_length"] == 100

    def test_env_branch_max_length_invalid(self) -> None:
        """Test handling invalid branch_max_length from environment."""
        with mock.patch.dict(os.environ, {"GMUSE_BRANCH_MAX_LENGTH": "invalid"}):
            config = get_env_config()
            assert "branch_max_length" not in config

    def test_env_both_branch_options(self) -> None:
        """Test loading both branch options from environment."""
        with mock.patch.dict(
            os.environ,
            {
                "GMUSE_INCLUDE_BRANCH": "true",
                "GMUSE_BRANCH_MAX_LENGTH": "80",
            },
        ):
            config = get_env_config()
            assert config["include_branch"] is True
            assert config["branch_max_length"] == 80
