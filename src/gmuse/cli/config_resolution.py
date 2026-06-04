"""Shared CLI configuration loading helpers.

This module centralizes the common load, merge, and optional validation
behavior used by the CLI entrypoints while allowing each command to keep its
own failure policy.
"""

from typing import Optional

from gmuse.config import (
    ConfigDict,
    get_env_config,
    load_config,
    merge_config,
    validate_config,
)


def resolve_config(
    cli_args: Optional[ConfigDict] = None,
    *,
    tolerate_load_errors: bool = False,
    validate: bool = False,
) -> ConfigDict:
    """Load, merge, and optionally validate CLI configuration.

    Args:
        cli_args: Command-specific CLI overrides.
        tolerate_load_errors: If True, unreadable config files fall back to
            an empty config instead of raising.
        validate: If True, validate the merged config before returning it.

    Returns:
        The merged configuration dictionary.
    """
    try:
        config_file = load_config()
    except Exception:
        if not tolerate_load_errors:
            raise
        config_file = {}

    env_config = get_env_config()
    config = merge_config(
        cli_args=cli_args or {},
        config_file=config_file,
        env_vars=env_config,
    )

    if validate:
        validate_config(config)

    return config
