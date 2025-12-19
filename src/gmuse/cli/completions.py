"""CLI commands for shell completions.

This module provides shell completion support for gmuse, including:

- A command to emit shell-specific completion scripts
- A runtime helper that generates AI suggestions for commit messages

Commands:
    git-completions: Group command for completion-related subcommands
    git-completions zsh: Emit the zsh completion script to stdout
    git-completions-run: Runtime helper called by shell completion functions

Example:
    >>> # Add to ~/.zshrc:
    >>> # eval "$(gmuse git-completions zsh)"
"""

import json
import os
import time
from dataclasses import dataclass
from enum import Enum
from importlib import resources as _importlib_resources

import typer

from gmuse.commit import GenerationContext, generate_message
from gmuse.config import get_env_config, load_config, merge_config
from gmuse.exceptions import LLMError, NoStagedChangesError, NotAGitRepositoryError
from gmuse.git import get_staged_diff
from gmuse.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# CLI Application Setup
# =============================================================================

completions_app = typer.Typer(
    help="Shell completion utilities.",
    no_args_is_help=True,
)


# =============================================================================
# Data Structures
# =============================================================================


class CompletionStatus(str, Enum):
    """Status codes for completion responses.

    Attributes:
        OK: Suggestion generated successfully.
        TIMEOUT: Generation timed out.
        OFFLINE: Network unavailable or credentials missing.
        NO_STAGED_CHANGES: No staged changes found.
        ERROR: Internal error.
    """

    OK = "ok"
    TIMEOUT = "timeout"
    OFFLINE = "offline"
    NO_STAGED_CHANGES = "no_staged_changes"
    ERROR = "error"


@dataclass(slots=True)
class CompletionRequest:
    """Represents the input context for generating a commit message.

    Attributes:
        staged_diff: The staged changes from git diff --staged.
        timeout: Timeout in seconds for the generation.
    """

    staged_diff: str
    timeout: float = 3.0


@dataclass(slots=True)
class CompletionResponse:
    """Represents the output from the runtime helper.

    Attributes:
        suggestion: The generated commit message (empty if error).
        status: Status code indicating success or failure mode.
        metadata: Additional info such as truncated flag and elapsed time.
    """

    suggestion: str
    status: CompletionStatus
    metadata: dict[str, object]

    def to_json(self) -> str:
        """Serialize response to JSON string.

        Returns:
            JSON string representation of the response.
        """

        return json.dumps(
            {
                "suggestion": self.suggestion,
                "status": self.status.value,
                "metadata": self.metadata,
            }
        )


# =============================================================================
# Zsh Completion Script Template


def _load_zsh_template() -> str:
    """Load the zsh completion template from package resources.

    Raises:
        RuntimeError: If the template cannot be read.
    """

    try:
        return (
            _importlib_resources.files("gmuse")
            .joinpath("templates", "zsh_completion.zsh")
            .read_text(encoding="utf-8")
        )
    except Exception as exc:  # pragma: no cover - error path tested
        raise RuntimeError(
            "zsh completion template is missing or cannot be read; reinstall gmuse or check packaging."
        ) from exc


# =============================================================================
# Commands
# =============================================================================


@completions_app.command(name="zsh")
def completions_zsh() -> None:
    """Emit the zsh completion script to stdout.

    The script provides AI-generated commit message suggestions when completing
    'git commit -m'. Add to your ~/.zshrc using eval.

    Example:
        eval "$(gmuse git-completions zsh)"
    """
    try:
        template = _load_zsh_template()
    except RuntimeError as exc:
        # Provide a clear error and exit non-zero so callers (and CI) notice
        typer.secho(str(exc), err=True)
        raise typer.Exit(code=1)

    typer.echo(template)


# =============================================================================
# Runtime Helper Command (top-level, not under completions group)
# =============================================================================


def completions_run_command(
    shell: str = typer.Option(
        ...,
        "--shell",
        help="The target shell (e.g., zsh)",
    ),
    for_command: str = typer.Option(
        ...,
        "--for",
        help="The command being completed (e.g., 'git commit -m')",
    ),
    timeout: float = typer.Option(
        3.0,
        "--timeout",
        help="Timeout in seconds",
    ),
) -> None:
    """Runtime helper for shell completions.

    This command is called by shell completion functions to generate
    AI-powered commit message suggestions. It outputs JSON to stdout.

    Args:
        shell: The target shell. Currently only "zsh" is supported.
        for_command: The command being completed. Expected to contain "git commit".
        timeout: Timeout in seconds for LLM generation.

    The output format is:
        {"suggestion": "...", "status": "ok|timeout|offline|no_staged_changes|error", "metadata": {...}}
    """
    start_time = time.time()

    # Validate shell parameter
    if shell != "zsh":
        response = CompletionResponse(
            suggestion="",
            status=CompletionStatus.ERROR,
            metadata={
                "error": f"Unsupported shell: {shell}. Only 'zsh' is currently supported.",
                "elapsed_ms": int((time.time() - start_time) * 1000),
            },
        )
        typer.echo(response.to_json())
        return

    # Validate for_command parameter
    if "git commit" not in for_command.lower():
        response = CompletionResponse(
            suggestion="",
            status=CompletionStatus.ERROR,
            metadata={
                "error": f"Invalid command: {for_command}. Expected a 'git commit' command.",
                "elapsed_ms": int((time.time() - start_time) * 1000),
            },
        )
        typer.echo(response.to_json())
        return

    # Override timeout from environment if set
    env_timeout = os.getenv("GMUSE_COMPLETIONS_TIMEOUT")
    if env_timeout:
        try:
            timeout = float(env_timeout)
        except ValueError:
            # Invalid GMUSE_COMPLETIONS_TIMEOUT; ignore and keep the existing timeout value.
            pass

    try:
        # Get staged diff
        try:
            staged_diff = get_staged_diff()
        except NoStagedChangesError:
            response = CompletionResponse(
                suggestion="",
                status=CompletionStatus.NO_STAGED_CHANGES,
                metadata={"elapsed_ms": int((time.time() - start_time) * 1000)},
            )
            typer.echo(response.to_json())
            return
        except NotAGitRepositoryError:
            response = CompletionResponse(
                suggestion="",
                status=CompletionStatus.ERROR,
                metadata={
                    "error": "Not a git repository",
                    "elapsed_ms": int((time.time() - start_time) * 1000),
                },
            )
            typer.echo(response.to_json())
            return

        # Generate commit message using LLM
        try:
            # Load minimal config for completion
            try:
                config_file = load_config()
            except Exception:
                config_file = {}

            env_config = get_env_config()
            config = merge_config(
                cli_args={"timeout": timeout},
                config_file=config_file,
                env_vars=env_config,
            )

            # Create context with just the diff (minimal for speed)
            context = GenerationContext(
                diff=staged_diff,
                history=None,
                repo_instructions=None,
                diff_was_truncated=staged_diff.truncated,
            )

            # Generate message
            result = generate_message(config=config, hint=None, context=context)

            elapsed_ms = int((time.time() - start_time) * 1000)

            response = CompletionResponse(
                suggestion=result.message,
                status=CompletionStatus.OK,
                metadata={
                    "elapsed_ms": elapsed_ms,
                    "truncated": staged_diff.truncated,
                },
            )
            typer.echo(response.to_json())

        except LLMError as e:
            error_msg = str(e).lower()
            if (
                "api key" in error_msg
                or "auth" in error_msg
                or "credential" in error_msg
            ):
                status = CompletionStatus.OFFLINE
            elif "timeout" in error_msg:
                status = CompletionStatus.TIMEOUT
            else:
                status = CompletionStatus.ERROR

            response = CompletionResponse(
                suggestion="",
                status=status,
                metadata={
                    "error": str(e),
                    "elapsed_ms": int((time.time() - start_time) * 1000),
                },
            )
            typer.echo(response.to_json())

    except Exception as e:
        # Catch-all for any unexpected errors
        response = CompletionResponse(
            suggestion="",
            status=CompletionStatus.ERROR,
            metadata={
                "error": str(e),
                "elapsed_ms": int((time.time() - start_time) * 1000),
            },
        )
        typer.echo(response.to_json())
