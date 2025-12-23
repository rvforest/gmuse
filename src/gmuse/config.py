"""Configuration management for gmuse.

This module handles loading, validation, and merging of configuration from multiple sources:

- CLI flags (highest priority)
- config.toml file
- Environment variables
- Defaults (lowest priority)

The configuration is represented as a dictionary (ConfigDict) with string keys and
values of various types depending on the setting.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Final, Optional

# Use tomllib (3.11+) or tomli (3.10)
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore[assignment]

from gmuse.exceptions import ConfigError
from gmuse.logging import get_logger

logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# Type Aliases
# -----------------------------------------------------------------------------

ConfigDict = Dict[str, Any]
"""Type alias for configuration dictionaries."""

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

VALID_FORMATS: Final[frozenset[str]] = frozenset(
    {"freeform", "conventional", "gitmoji"}
)
"""Allowed values for the 'format' configuration option."""

VALID_PROVIDERS: Final[frozenset[str]] = frozenset(
    {"openai", "anthropic", "cohere", "azure", "gemini", "bedrock", "huggingface"}
)
"""Allowed values for the 'provider' configuration option."""

HISTORY_DEPTH_MIN: Final[int] = 0
HISTORY_DEPTH_MAX: Final[int] = 50
"""Valid range for history_depth configuration."""

TIMEOUT_MIN: Final[int] = 5
TIMEOUT_MAX: Final[int] = 300
"""Valid range for timeout configuration (in seconds)."""

TEMPERATURE_MIN: Final[float] = 0.0
TEMPERATURE_MAX: Final[float] = 2.0
"""Valid range for temperature configuration."""

MAX_TOKENS_MIN: Final[int] = 1
MAX_TOKENS_MAX: Final[int] = 100000
"""Valid range for max_tokens configuration."""

MAX_DIFF_BYTES_MIN: Final[int] = 1000
MAX_DIFF_BYTES_MAX: Final[int] = 10000000
"""Valid range for max_diff_bytes configuration."""

MAX_MESSAGE_LENGTH_MIN: Final[int] = 10
MAX_MESSAGE_LENGTH_MAX: Final[int] = 10000
"""Valid range for max_message_length configuration."""

CHARS_PER_TOKEN_MIN: Final[int] = 1
CHARS_PER_TOKEN_MAX: Final[int] = 10
"""Valid range for chars_per_token configuration."""
BRANCH_MAX_LENGTH_MIN: Final[int] = 20
BRANCH_MAX_LENGTH_MAX: Final[int] = 200
"""Valid range for branch_max_length configuration."""

DEFAULTS: Final[ConfigDict] = {
    "model": None,  # Auto-detect from environment
    "copy_to_clipboard": False,
    "learning_enabled": False,
    "history_depth": 5,
    "format": "freeform",
    "timeout": 30,
    "provider": None,
    "log_file": None,  # Optional path to log file for debug output
    "temperature": 0.7,  # LLM sampling temperature
    "max_tokens": 500,  # Maximum tokens in LLM response
    "max_diff_bytes": 20000,  # Maximum diff size before truncation (~5000 tokens)
    "max_message_length": 1000,  # Maximum commit message length
    "chars_per_token": 4,  # Characters per token heuristic for estimation
    "include_branch": False,  # Include branch name as context
    "branch_max_length": 60,  # Maximum length for branch summary
}
"""Default configuration values used when no override is provided."""


ALLOWED_CONFIG_KEYS: Final[frozenset[str]] = frozenset(DEFAULTS.keys())
"""Allowlist of configuration keys that can be set via the CLI."""


ENV_VAR_BY_KEY: Final[dict[str, str]] = {
    "model": "GMUSE_MODEL",
    "format": "GMUSE_FORMAT",
    "history_depth": "GMUSE_HISTORY_DEPTH",
    "timeout": "GMUSE_TIMEOUT",
    "copy_to_clipboard": "GMUSE_COPY",
    "learning_enabled": "GMUSE_LEARNING",
    "provider": "GMUSE_PROVIDER",
    "log_file": "GMUSE_LOG_FILE",
    "temperature": "GMUSE_TEMPERATURE",
    "max_tokens": "GMUSE_MAX_TOKENS",
    "max_diff_bytes": "GMUSE_MAX_DIFF_BYTES",
    "max_message_length": "GMUSE_MAX_MESSAGE_LENGTH",
    "chars_per_token": "GMUSE_CHARS_PER_TOKEN",
    "include_branch": "GMUSE_INCLUDE_BRANCH",
    "branch_max_length": "GMUSE_BRANCH_MAX_LENGTH",
}
"""Mapping from config keys to their overriding environment variables."""


def get_config_path() -> Path:
    """Get the path to the configuration file using XDG Base Directory specification.

    Returns:
        Path to config.toml (e.g., ~/.config/gmuse/config.toml)

    Example:
        >>> config_path = get_config_path()
        >>> print(config_path)
        /home/user/.config/gmuse/config.toml
    """
    # XDG_CONFIG_HOME defaults to ~/.config if not set
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        config_dir = Path(xdg_config_home)
    else:
        config_dir = Path.home() / ".config"

    return config_dir / "gmuse" / "config.toml"


def load_config(config_path: Optional[Path] = None) -> ConfigDict:
    """Load configuration from TOML file.

    Args:
        config_path: Path to config file, defaults to XDG location

    Returns:
        Dictionary of configuration values (empty if file doesn't exist)

    Raises:
        ConfigError: If TOML file is invalid or cannot be read

    Example:
        >>> config = load_config()
        >>> print(config.get("model"))
        gpt-4
    """
    if config_path is None:
        config_path = get_config_path()

    if not config_path.exists():
        logger.debug(f"Config file not found: {config_path}")
        return {}

    if tomllib is None:
        raise ConfigError(
            "tomli package is required for Python 3.10. "
            "Install with: pip install gmuse[all]"
        )

    try:
        logger.debug(f"Loading config from: {config_path}")
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        logger.debug(f"Loaded config: {config}")
        return config
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Invalid TOML syntax in {config_path}: {e}") from e
    except OSError as e:
        raise ConfigError(f"Cannot read config file {config_path}: {e}") from e


def load_config_raw(config_path: Optional[Path] = None) -> str | None:
    """Load raw config file contents as text.

    This is used by `gmuse config view` to display the file contents verbatim
    while still providing clear errors for unreadable files.

    Args:
        config_path: Path to config file, defaults to XDG location.

    Returns:
        The file contents if the file exists, otherwise None.

    Raises:
        ConfigError: If the file exists but cannot be read.
    """
    if config_path is None:
        config_path = get_config_path()

    if not config_path.exists():
        return None

    try:
        return config_path.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigError(f"Cannot read config file {config_path}: {e}") from e


def parse_config_value(key: str, raw: str) -> Any:
    """Parse a CLI-provided raw value according to the expected key type.

    Args:
        key: Configuration key (must be in DEFAULTS).
        raw: Raw user-provided value string.

    Returns:
        Parsed Python value.

    Raises:
        ConfigError: If the key is unknown or the value cannot be parsed.
    """
    if key not in DEFAULTS:
        raise ConfigError(f"Unknown configuration key: '{key}'")

    expected_default = DEFAULTS[key]
    raw_normalized = raw.strip()
    lower = raw_normalized.lower()

    if isinstance(expected_default, bool):
        if lower in {"true", "1", "yes"}:
            return True
        if lower in {"false", "0", "no"}:
            return False
        raise ConfigError(f"{key} must be a boolean (true/false), got '{raw}'")

    if isinstance(expected_default, int):
        try:
            return int(raw_normalized)
        except ValueError as e:
            raise ConfigError(f"Cannot parse '{raw}' as integer for '{key}'") from e

    if isinstance(expected_default, float):
        try:
            return float(raw_normalized)
        except ValueError as e:
            raise ConfigError(f"Cannot parse '{raw}' as number for '{key}'") from e

    # Optional string keys use a None default.
    if expected_default is None:
        if lower in {"null", "none"}:
            return None
        return raw_normalized

    # Plain strings.
    if isinstance(expected_default, str):
        return raw_normalized

    raise ConfigError(f"Unsupported configuration type for '{key}'")


def _validate_integer_range(
    config: ConfigDict,
    key: str,
    min_val: int,
    max_val: int,
) -> None:
    """Validate an integer config value is within the allowed range.

    Args:
        config: Configuration dictionary
        key: Configuration key to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)

    Raises:
        ConfigError: If value is not an integer or out of range
    """
    if key not in config:
        return

    value = config[key]
    if not isinstance(value, int):
        raise ConfigError(f"{key} must be an integer, got {type(value).__name__}")
    if not (min_val <= value <= max_val):
        raise ConfigError(f"{key} must be between {min_val} and {max_val}, got {value}")


def _validate_float_range(
    config: ConfigDict,
    key: str,
    min_val: float,
    max_val: float,
) -> None:
    """Validate a float config value is within the allowed range.

    Args:
        config: Configuration dictionary
        key: Configuration key to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)

    Raises:
        ConfigError: If value is not a number or out of range
    """
    if key not in config:
        return

    value = config[key]
    if not isinstance(value, (int, float)):
        raise ConfigError(f"{key} must be a number, got {type(value).__name__}")
    if not (min_val <= value <= max_val):
        raise ConfigError(f"{key} must be between {min_val} and {max_val}, got {value}")


def _validate_string_choice(
    config: ConfigDict,
    key: str,
    valid_choices: frozenset[str],
    allow_none: bool = False,
) -> None:
    """Validate a string config value is one of the allowed choices.

    Args:
        config: Configuration dictionary
        key: Configuration key to validate
        valid_choices: Set of allowed string values
        allow_none: Whether None is a valid value

    Raises:
        ConfigError: If value is not a string or not in valid choices
    """
    if key not in config:
        return

    value = config[key]
    if value is None and allow_none:
        return

    if not isinstance(value, str):
        expected = "a string or null" if allow_none else "a string"
        raise ConfigError(f"{key} must be {expected}, got {type(value).__name__}")

    if value not in valid_choices:
        raise ConfigError(f"{key} must be one of {set(valid_choices)}, got '{value}'")


def _validate_boolean(config: ConfigDict, key: str) -> None:
    """Validate a config value is a boolean.

    Args:
        config: Configuration dictionary
        key: Configuration key to validate

    Raises:
        ConfigError: If value is not a boolean
    """
    if key not in config:
        return

    value = config[key]
    if not isinstance(value, bool):
        raise ConfigError(f"{key} must be a boolean, got {type(value).__name__}")


def _validate_optional_string(config: ConfigDict, key: str) -> None:
    """Validate a config value is a string or None.

    Args:
        config: Configuration dictionary
        key: Configuration key to validate

    Raises:
        ConfigError: If value is not a string or None
    """
    if key not in config:
        return

    value = config[key]
    if value is not None and not isinstance(value, str):
        raise ConfigError(f"{key} must be a string or null, got {type(value).__name__}")


def _parse_env_int(env_var: str, config_key: str) -> tuple[str, int] | None:
    """Parse an integer environment variable.

    Args:
        env_var: Environment variable name (e.g., "GMUSE_TIMEOUT")
        config_key: Configuration key name (e.g., "timeout")

    Returns:
        Tuple of (config_key, parsed_value) if valid, None otherwise
    """
    if value := os.getenv(env_var):
        try:
            return (config_key, int(value))
        except ValueError:
            logger.warning(f"Invalid {env_var}: {value}")
    return None


def _parse_env_float(env_var: str, config_key: str) -> tuple[str, float] | None:
    """Parse a float environment variable.

    Args:
        env_var: Environment variable name (e.g., "GMUSE_TEMPERATURE")
        config_key: Configuration key name (e.g., "temperature")

    Returns:
        Tuple of (config_key, parsed_value) if valid, None otherwise
    """
    if value := os.getenv(env_var):
        try:
            return (config_key, float(value))
        except ValueError:
            logger.warning(f"Invalid {env_var}: {value}")
    return None


def validate_config(config: ConfigDict) -> None:
    """Validate configuration values.

    Checks that all configuration values are of the correct type and within
    valid ranges. Unknown keys are logged as warnings but do not cause errors.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigError: If any configuration value is invalid

    Example:
        >>> config = {"history_depth": 5, "format": "conventional"}
        >>> validate_config(config)  # No error
        >>> config = {"history_depth": -1}
        >>> validate_config(config)  # Raises ConfigError
    """
    # Validate integer ranges
    _validate_integer_range(
        config, "history_depth", HISTORY_DEPTH_MIN, HISTORY_DEPTH_MAX
    )
    _validate_integer_range(config, "timeout", TIMEOUT_MIN, TIMEOUT_MAX)
    _validate_integer_range(config, "max_tokens", MAX_TOKENS_MIN, MAX_TOKENS_MAX)
    _validate_integer_range(
        config, "max_diff_bytes", MAX_DIFF_BYTES_MIN, MAX_DIFF_BYTES_MAX
    )
    _validate_integer_range(
        config, "max_message_length", MAX_MESSAGE_LENGTH_MIN, MAX_MESSAGE_LENGTH_MAX
    )
    _validate_integer_range(
        config, "chars_per_token", CHARS_PER_TOKEN_MIN, CHARS_PER_TOKEN_MAX
    )

    # Validate float ranges
    _validate_float_range(config, "temperature", TEMPERATURE_MIN, TEMPERATURE_MAX)
    _validate_integer_range(
        config, "branch_max_length", BRANCH_MAX_LENGTH_MIN, BRANCH_MAX_LENGTH_MAX
    )

    # Validate string choices
    _validate_string_choice(config, "format", VALID_FORMATS)
    _validate_string_choice(config, "provider", VALID_PROVIDERS, allow_none=True)

    # Validate boolean fields
    _validate_boolean(config, "copy_to_clipboard")
    _validate_boolean(config, "learning_enabled")
    _validate_boolean(config, "include_branch")

    # Validate optional string fields
    _validate_optional_string(config, "model")

    # Warn about unknown keys
    known_keys = set(DEFAULTS.keys())
    unknown_keys = set(config.keys()) - known_keys
    if unknown_keys:
        logger.warning(f"Unknown config keys (will be ignored): {unknown_keys}")


def merge_config(
    cli_args: Optional[ConfigDict] = None,
    config_file: Optional[ConfigDict] = None,
    env_vars: Optional[ConfigDict] = None,
) -> ConfigDict:
    """Merge configuration from multiple sources with priority.

    Priority (highest to lowest):
    1. CLI arguments (cli_args)
    2. Environment variables (env_vars)
    3. Config file (config_file)
    4. Defaults (DEFAULTS)

    Args:
        cli_args: Configuration from CLI flags
        config_file: Configuration from config.toml
        env_vars: Configuration from environment variables

    Returns:
        Merged configuration dictionary

    Example:
        >>> cli = {"model": "gpt-4"}
        >>> file = {"model": "claude-3", "format": "conventional"}
        >>> merged = merge_config(cli_args=cli, config_file=file)
        >>> print(merged["model"])  # CLI wins
        gpt-4
        >>> print(merged["format"])  # File value used
        conventional
    """
    # Start with defaults
    result = DEFAULTS.copy()

    # Apply config file
    if config_file:
        for key, value in config_file.items():
            if key in DEFAULTS and value is not None:
                result[key] = value

    # Apply environment variables
    if env_vars:
        for key, value in env_vars.items():
            if value is not None:
                result[key] = value

    # Apply CLI args (highest priority)
    if cli_args:
        for key, value in cli_args.items():
            if value is not None:
                result[key] = value

    return result


def _load_toml_document(config_path: Path):
    """Load a TOML document for round-trip editing.

    Raises:
        ConfigError: If the file cannot be read or TOML is invalid.
    """
    import tomlkit
    from tomlkit.exceptions import ParseError

    if not config_path.exists():
        return tomlkit.document()

    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigError(f"Cannot read config file {config_path}: {e}") from e

    try:
        return tomlkit.parse(text)
    except ParseError as e:
        raise ConfigError(f"Invalid TOML syntax in {config_path}: {e}") from e


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path: Path | None = None
    try:
        fd, tmp_name = tempfile.mkstemp(
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        tmp_path = Path(tmp_name)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except OSError as e:
        raise ConfigError(f"Cannot write config file {path}: {e}") from e
    finally:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError as e:
                # Best-effort cleanup: failure to remove the temporary file is non-fatal.
                logger.debug("Failed to remove temporary config temp file %s: %s", tmp_path, e)


def update_config_key(key: str, value: Any, config_path: Optional[Path] = None) -> Path:
    """Update (or remove) a single key in the global config file.

    This preserves unrelated settings and comments by using tomlkit round-trip
    editing and writes the file atomically.

    Args:
        key: Config key to set.
        value: Parsed value.
        config_path: Optional path override (defaults to XDG location).

    Returns:
        The path that was written.

    Raises:
        ConfigError: On read/write errors or invalid TOML.
    """
    if config_path is None:
        config_path = get_config_path()

    if key not in ALLOWED_CONFIG_KEYS:
        raise ConfigError(f"Unknown configuration key: '{key}'")

    doc = _load_toml_document(config_path)

    # Treat None as 'unset' for optional string keys.
    if value is None and DEFAULTS.get(key) is None:
        if key in doc:
            del doc[key]
    else:
        doc[key] = value

    import tomlkit

    rendered = tomlkit.dumps(doc)
    if rendered and not rendered.endswith("\n"):
        rendered += "\n"

    _atomic_write_text(config_path, rendered)
    return config_path


def get_env_config() -> ConfigDict:
    """Load configuration from environment variables.

    Environment variables:
        - GMUSE_MODEL: Model name
        - GMUSE_FORMAT: Message format
        - GMUSE_HISTORY_DEPTH: Number of commits for context
        - GMUSE_TIMEOUT: Request timeout in seconds
        - GMUSE_COPY: Copy to clipboard (true/false)
        - GMUSE_LEARNING: Enable learning mode (true/false)
        - GMUSE_PROVIDER: LLM provider
        - GMUSE_LOG_FILE: Log file path
        - GMUSE_TEMPERATURE: LLM sampling temperature
        - GMUSE_MAX_TOKENS: Maximum tokens in response
        - GMUSE_MAX_DIFF_BYTES: Maximum diff size before truncation
        - GMUSE_MAX_MESSAGE_LENGTH: Maximum commit message length
        - GMUSE_CHARS_PER_TOKEN: Characters per token heuristic
        - GMUSE_INCLUDE_BRANCH: Include branch name as context (1/true/yes)
        - GMUSE_BRANCH_MAX_LENGTH: Maximum length for branch summary

    Returns:
        Configuration dictionary from environment variables

    Example:
        >>> os.environ["GMUSE_MODEL"] = "gpt-4"
        >>> config = get_env_config()
        >>> print(config["model"])
        gpt-4
    """
    config: ConfigDict = {}

    # String values
    if model := os.getenv("GMUSE_MODEL"):
        config["model"] = model

    if fmt := os.getenv("GMUSE_FORMAT"):
        config["format"] = fmt

    # Integer values - use helper function
    int_params = [
        ("GMUSE_HISTORY_DEPTH", "history_depth"),
        ("GMUSE_TIMEOUT", "timeout"),
        ("GMUSE_MAX_TOKENS", "max_tokens"),
        ("GMUSE_MAX_DIFF_BYTES", "max_diff_bytes"),
        ("GMUSE_MAX_MESSAGE_LENGTH", "max_message_length"),
        ("GMUSE_CHARS_PER_TOKEN", "chars_per_token"),
    ]
    for env_var, config_key in int_params:
        int_result = _parse_env_int(env_var, config_key)
        if int_result:
            config[int_result[0]] = int_result[1]

    # Float values - use helper function
    float_result = _parse_env_float("GMUSE_TEMPERATURE", "temperature")
    if float_result:
        config[float_result[0]] = float_result[1]

    # Boolean values
    if copy := os.getenv("GMUSE_COPY"):
        config["copy_to_clipboard"] = copy.lower() in ("1", "true", "yes")

    if learning := os.getenv("GMUSE_LEARNING"):
        config["learning_enabled"] = learning.lower() in ("1", "true", "yes")

    if include_branch := os.getenv("GMUSE_INCLUDE_BRANCH"):
        config["include_branch"] = include_branch.lower() in ("1", "true", "yes")

    # Log file override
    if log_file := os.getenv("GMUSE_LOG_FILE"):
        config["log_file"] = log_file

    # Branch max length
    if branch_max := os.getenv("GMUSE_BRANCH_MAX_LENGTH"):
        try:
            config["branch_max_length"] = int(branch_max)
        except ValueError:
            logger.warning(f"Invalid GMUSE_BRANCH_MAX_LENGTH: {branch_max}")

    return config
