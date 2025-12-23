"""Global configuration CLI commands.

This module implements the `gmuse config` command group.

Commands:
    view: Display global config file contents and effective configuration.
    set: Persist a validated configuration key/value into the global config file.
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any, NoReturn

import typer

from gmuse.config import (
    ALLOWED_CONFIG_KEYS,
    DEFAULTS,
    ENV_VAR_BY_KEY,
    VALID_PROVIDERS,
    get_config_path,
    get_env_config,
    load_config,
    load_config_raw,
    merge_config,
    parse_config_value,
    update_config_key,
    validate_config,
)
from gmuse.exceptions import ConfigError

config_app = typer.Typer(
    help=(
        "Manage gmuse global configuration.\n\n"
        "View and modify settings stored in ~/.config/gmuse/config.toml.\n"
        "These settings apply across all repositories unless overridden\n"
        "by environment variables or CLI flags."
    ),
    no_args_is_help=True,
)


def _format_value(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _format_valid_keys(keys: list[str]) -> str:
    return textwrap.fill(
        ", ".join(keys),
        width=79,
        initial_indent="Valid keys: ",
        subsequent_indent="            ",
    )


def _exit_with_error(message: str, *, hint: str | None = None) -> NoReturn:
    typer.echo(f"Error: {message}", err=True)
    if hint:
        typer.echo("", err=True)
        typer.echo(hint, err=True)
    raise typer.Exit(code=1)


@config_app.command("view")
def view() -> None:
    """Display current global configuration."""
    config_path = get_config_path()
    typer.echo(f"Global config file: {config_path}")
    typer.echo("")

    config_file: dict[str, Any] = {}

    raw_text = None
    try:
        raw_text = load_config_raw(config_path)
    except ConfigError as e:
        _exit_with_error(
            str(e),
            hint="Check file permissions and try again.",
        )

    if raw_text is None:
        typer.echo("No global configuration file found.")
        typer.echo("Create one with: gmuse config set <key> <value>")
        typer.echo("")
    else:
        typer.echo("--- File Contents ---")
        typer.echo(raw_text.rstrip("\n"))
        typer.echo("")
        try:
            config_file = load_config(config_path)
        except ConfigError as e:
            _exit_with_error(
                str(e),
                hint="Fix the syntax error or delete the file to start fresh.",
            )

    env_config = get_env_config()
    effective = merge_config(cli_args={}, config_file=config_file, env_vars=env_config)

    typer.echo("--- Effective Configuration ---")
    typer.echo(f"{'Key':<18} {'Value':<22} Source")
    typer.echo("─" * 60)

    for key in sorted(DEFAULTS.keys()):
        value = effective.get(key)
        in_file = key in config_file
        in_env = key in env_config

        if in_env:
            env_var = ENV_VAR_BY_KEY.get(key, "GMUSE_*")
            source = f"env ({env_var})"
            if in_file:
                source += " ⚠ overrides file"
        elif in_file:
            source = "config file"
        else:
            source = "default"

        typer.echo(f"{key:<18} {_format_value(value):<22} {source}")


@config_app.command("set")
def set_value(key: str = typer.Argument(...), value: str = typer.Argument(...)) -> None:
    """Set a global configuration value."""
    normalized_key = key.strip()
    if normalized_key not in ALLOWED_CONFIG_KEYS:
        valid_keys = sorted(ALLOWED_CONFIG_KEYS)
        _exit_with_error(
            f"Unknown configuration key: '{normalized_key}'",
            hint=_format_valid_keys(valid_keys),
        )

    parsed: str | None = None
    try:
        parsed = parse_config_value(normalized_key, value)
    except ConfigError as e:
        example = None
        if normalized_key in {"history_depth", "timeout", "max_tokens"}:
            example = f"Example: gmuse config set {normalized_key} 10"
        _exit_with_error(str(e), hint=example)

    try:
        validate_config({normalized_key: parsed})
    except ConfigError as e:
        if normalized_key == "format" and isinstance(parsed, str):
            _exit_with_error(
                f"Invalid format: '{parsed}'. Must be one of: freeform, conventional, gitmoji"
            )
        if normalized_key == "provider" and isinstance(parsed, str):
            providers = ", ".join(sorted(VALID_PROVIDERS))
            _exit_with_error(
                f"Invalid provider: '{parsed}'. Must be one of: {providers}"
            )
        hint = None
        if normalized_key == "history_depth":
            hint = "Allowed range: 0-50"
        elif normalized_key == "timeout":
            hint = "Allowed range: 5-300"
        elif normalized_key == "temperature":
            hint = "Allowed range: 0.0-2.0"
        _exit_with_error(str(e), hint=hint)

    config_path = None
    try:
        config_path = update_config_key(normalized_key, parsed)
    except ConfigError as e:
        _exit_with_error(
            str(e),
            hint="Check directory permissions and try again.",
        )
    if config_path is None:
        _exit_with_error("Failed to determine config file path after update.")

    assert config_path is not None  # for type checker
    typer.echo(
        f"Set '{normalized_key}' to '{_format_value(parsed)}' in {Path(config_path)}"
    )
