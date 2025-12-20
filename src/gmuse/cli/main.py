"""CLI interface for gmuse.

This module provides the command-line interface using Typer. It handles:

- Argument parsing and validation
- Configuration loading and merging
- Error handling and user feedback
- Clipboard operations

Commands:
    msg: Generate a commit message from staged changes.
    info: Display resolved configuration for debugging.
    git-completions: Shell completion utilities.
    git-completions-run: Runtime helper for shell completions.

Example:
    >>> # From command line:
    >>> # gmuse msg --hint "security fix" --copy
"""

import os
import sys
from typing import Any, Optional

# Handle debug logging for completion runtime
# The zsh completion script redirects stderr to stdout (2>&1) to capture errors,
# which would mix debug logs with JSON output and break parsing.
# Solution: Debug logging for completions only works if log_file is configured via GMUSE_LOG_FILE.
# Otherwise, debug output is suppressed to prevent JSON pollution.
if "git-completions-run" in " ".join(sys.argv) and not os.getenv("GMUSE_LOG_FILE"):
    # No log file configured - suppress debug to keep JSON clean
    if "GMUSE_DEBUG" in os.environ:
        del os.environ["GMUSE_DEBUG"]
    if "GMUSE_LOG_LEVEL" in os.environ:
        del os.environ["GMUSE_LOG_LEVEL"]

import typer

from gmuse import __version__  # noqa: E402
from gmuse.config import (
    ConfigDict,
    get_env_config,
    load_config,
    merge_config,
    validate_config,
)
from gmuse.exceptions import (
    ConfigError,
    InvalidMessageError,
    LLMError,
    NoStagedChangesError,
    NotAGitRepositoryError,
)
from gmuse.commit import generate_message, gather_context
from gmuse.logging import get_logger
from gmuse.prompts import build_prompt
from gmuse.cli.completions import completions_app, completions_run_command

logger = get_logger(__name__)

# =============================================================================
# CLI Application Setup
# =============================================================================

app = typer.Typer(
    help="gmuse: AI generated commit messages.",
    no_args_is_help=True,
)

# Register git-completions subcommand group
app.add_typer(completions_app, name="git-completions")

# Register git-completions-run as a top-level command
app.command(name="git-completions-run")(completions_run_command)


# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------


def version_callback(value: bool) -> None:
    """Show version and exit.

    Args:
        value: True if --version flag was passed.

    Raises:
        typer.Exit: Always exits after printing version.
    """
    if value:
        print(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        help="Show the version and exit.",
        is_eager=True,
        callback=version_callback,
    ),
) -> None:
    """gmuse: AI generated commit messages.

    Generate commit messages from staged changes using AI.

    Use 'gmuse msg' to create a commit message from your staged changes.

    Examples:
        gmuse msg                           # Generate message
        gmuse msg --hint "breaking change"  # With hint
        gmuse msg --format conventional     # Conventional commits
        gmuse msg --copy                    # Copy to clipboard
        gmuse info                          # Show configuration

    For more information, visit: https://gmuse.readthedocs.io
    """
    pass


# -----------------------------------------------------------------------------
# Commands
# -----------------------------------------------------------------------------


@app.command()
def info() -> None:
    """Print resolved LLM configuration and environment values for debugging.

    Useful for diagnosing provider selection and which credentials are being used.
    """
    # Resolve configuration similarly to `generate` without performing network calls
    try:
        config_file = load_config()
    except Exception:
        config_file = {}

    env_config = get_env_config()
    # Merge but don't raise errors here
    config = merge_config(cli_args={}, config_file=config_file, env_vars=env_config)

    provider = None
    try:
        from gmuse.llm import detect_provider

        provider = detect_provider()
    except Exception:
        provider = None

    typer.echo(f"Resolved model: {config.get('model')}")
    typer.echo(f"Detected provider heuristics: {provider}")
    typer.echo(f"Configured provider in merged config: {config.get('provider')}")

    typer.echo("Environment vars:")
    typer.echo(f"  OPENAI_API_KEY set: {'OPENAI_API_KEY' in os.environ}")
    typer.echo(f"  ANTHROPIC_API_KEY set: {'ANTHROPIC_API_KEY' in os.environ}")
    typer.echo(f"  GEMINI_API_KEY set: {'GEMINI_API_KEY' in os.environ}")
    typer.echo(f"  GOOGLE_API_KEY set: {'GOOGLE_API_KEY' in os.environ}")
    typer.echo(f"  GMUSE_MODEL env var: {os.getenv('GMUSE_MODEL')}")
    typer.echo(f"  GMUSE_TIMEOUT env var: {os.getenv('GMUSE_TIMEOUT')}")


@app.command()
def msg(
    hint: Optional[str] = typer.Option(
        None,
        "--hint",
        "-h",
        help="Additional guidance for message generation (e.g., 'emphasize security')",
    ),
    copy: bool = typer.Option(
        False,
        "--copy",
        "-c",
        help="Copy generated message to clipboard",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="LLM model to use (e.g., 'gpt-4', 'claude-3-opus')",
    ),
    format: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Message format: 'freeform' (default), 'conventional', or 'gitmoji'",
    ),
    history_depth: Optional[int] = typer.Option(
        None,
        "--history-depth",
        help="Number of recent commits to use for style context (0-50)",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        help="Explicit provider override (e.g., 'openai', 'gemini', 'anthropic')",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the assembled prompt without calling the LLM provider",
    ),
) -> None:
    """Generate a commit message from staged changes.

    This command analyzes your staged git changes and generates an appropriate
    commit message using AI. The message is printed to stdout and can optionally
    be copied to your clipboard.

    Examples:
        gmuse msg                        # Basic usage
        gmuse msg --hint "security fix"  # Add context hint
        gmuse msg --format conventional  # Use conventional commits format
        gmuse msg --copy                 # Auto-copy to clipboard
        gmuse msg --model claude-3-opus  # Use specific model
        gmuse msg --dry-run              # Preview prompt without calling LLM
    """
    try:
        # Load and merge configuration
        config = _load_config(
            model=model,
            copy=copy,
            format=format,
            history_depth=history_depth,
            provider=provider,
        )

        # Gather context and generate message
        context = gather_context(history_depth=config.get("history_depth", 5))

        # Warn if diff was truncated
        if context.diff_was_truncated:
            typer.secho(
                "Warning: Large diff truncated to fit token limits.",
                fg=typer.colors.YELLOW,
                err=True,
            )

        # --dry-run path: build prompt and print it, then exit
        if dry_run:
            effective_format = config.get("format", "freeform")
            system_prompt, user_prompt = build_prompt(
                diff=context.diff,
                format=effective_format,
                commit_history=context.history,
                repo_instructions=context.repo_instructions,
                user_hint=hint,
                learning_examples=None,
            )
            output = _format_dry_run_output(
                model=config.get("model"),
                format=effective_format,
                truncated=context.diff_was_truncated,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            typer.echo(output)
            raise typer.Exit(code=0)

        # Generate the commit message
        result = generate_message(config=config, hint=hint, context=context)

        # Output message to stdout
        typer.echo(result.message)

        # Copy to clipboard if requested
        if config.get("copy_to_clipboard"):
            _copy_to_clipboard(result.message)

    except ConfigError as e:
        _error_exit(str(e), code=1)

    except NotAGitRepositoryError as e:
        _error_exit(
            str(e),
            hint="Run this command inside a git repository.\nTo initialize a new repository: git init",
            code=1,
        )

    except NoStagedChangesError as e:
        _error_exit(
            str(e),
            hint="Stage your changes first:\n  git add <files>",
            code=1,
        )

    except LLMError as e:
        _error_exit(str(e), code=2)

    except InvalidMessageError as e:
        _error_exit(
            f"Generated message is invalid: {e}",
            hint="This is likely a temporary issue. Try again.",
            code=2,
        )

    except KeyboardInterrupt:
        typer.echo("\n\nInterrupted by user", err=True)
        raise typer.Exit(code=130)


# =============================================================================
# Private Helper Functions
# =============================================================================


def _load_config(
    model: Optional[str] = None,
    copy: bool = False,
    format: Optional[str] = None,
    history_depth: Optional[int] = None,
    provider: Optional[str] = None,
) -> ConfigDict:
    """Load and merge configuration from all sources.

    Configuration is loaded from multiple sources with the following
    precedence (highest to lowest):

    1. CLI arguments (passed to this function)
    2. Environment variables (GMUSE_*)
    3. Configuration file (.gmuse.toml or pyproject.toml)
    4. Built-in defaults

    Args:
        model: CLI model override.
        copy: CLI copy to clipboard flag.
        format: CLI format override.
        history_depth: CLI history depth override.
        provider: CLI provider override.

    Returns:
        Merged and validated configuration dictionary.

    Raises:
        ConfigError: If the merged configuration is invalid.
    """
    # Build CLI args dict (only non-None values)
    cli_args: dict[str, Any] = {}
    if model is not None:
        cli_args["model"] = model
    if copy:
        cli_args["copy_to_clipboard"] = copy
    if format is not None:
        cli_args["format"] = format
    if history_depth is not None:
        cli_args["history_depth"] = history_depth
    if provider is not None:
        cli_args["provider"] = provider

    # Load and merge from all sources
    config_file = load_config()
    env_config = get_env_config()
    config = merge_config(
        cli_args=cli_args,
        config_file=config_file,
        env_vars=env_config,
    )

    # Validate merged config
    validate_config(config)
    logger.debug(f"Configuration loaded: {config}")

    return config


def _copy_to_clipboard(message: str) -> None:
    """Copy message to clipboard with user feedback.

    Attempts to copy using pyperclip. Displays success message or
    warning if pyperclip is not installed or clipboard operation fails.

    Args:
        message: The text to copy to clipboard.
    """
    try:
        import pyperclip  # type: ignore

        pyperclip.copy(message)
        typer.secho("✓ Copied to clipboard", fg=typer.colors.GREEN, err=True)
    except ImportError:
        typer.secho(
            "Warning: pyperclip not installed. Install with: pip install 'gmuse[clipboard]'",
            fg=typer.colors.YELLOW,
            err=True,
        )
    except Exception as e:
        typer.secho(
            f"Warning: Could not copy to clipboard: {e}",
            fg=typer.colors.YELLOW,
            err=True,
        )


def _error_exit(message: str, code: int = 1, hint: Optional[str] = None) -> None:
    """Display error message and exit with specified code.

    Args:
        message: The error message to display.
        code: Exit code (default: 1).
        hint: Optional helpful hint to display after the error.

    Raises:
        typer.Exit: Always raises to exit the application.
    """
    typer.secho(f"Error: {message}", fg=typer.colors.RED, err=True)
    if hint:
        typer.echo(f"\n{hint}", err=True)
    raise typer.Exit(code=code)


def _format_dry_run_output(
    model: Optional[str],
    format: str,
    truncated: bool,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Format the dry-run output for CLI display.

    Produces a plain-text block containing a metadata header and labeled
    SYSTEM PROMPT / USER PROMPT sections so the user can inspect what
    would be sent to the LLM provider.

    Args:
        model: Resolved model name (or None if not configured).
        format: Message format (freeform, conventional, gitmoji).
        truncated: Whether the staged diff was truncated.
        system_prompt: The system prompt that would be sent.
        user_prompt: The user prompt that would be sent.

    Returns:
        Formatted string suitable for printing to stdout.

    Example:
        >>> output = _format_dry_run_output(
        ...     model="gpt-4",
        ...     format="conventional",
        ...     truncated=False,
        ...     system_prompt="You are a commit helper.",
        ...     user_prompt="Diff: ...",
        ... )
        >>> print(output)
        MODEL: gpt-4
        FORMAT: conventional
        TRUNCATED: false
        <BLANKLINE>
        SYSTEM PROMPT:
        You are a commit helper.
        <BLANKLINE>
        USER PROMPT:
        Diff: ...
    """
    model_str = model or "none"
    truncated_str = "true" if truncated else "false"
    return (
        f"MODEL: {model_str}\n"
        f"FORMAT: {format}\n"
        f"TRUNCATED: {truncated_str}\n"
        "\n"
        "SYSTEM PROMPT:\n"
        f"{system_prompt}\n"
        "\n"
        "USER PROMPT:\n"
        f"{user_prompt}"
    )
