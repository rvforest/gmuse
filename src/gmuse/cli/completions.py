"""CLI commands for shell completions.

This module provides shell completion support for gmuse, including:

- A command to emit shell-specific completion scripts
- A runtime helper that generates AI suggestions for commit messages

Commands:
    completions: Group command for completion-related subcommands
    completions zsh: Emit the zsh completion script to stdout
    completions-run: Runtime helper called by shell completion functions

Example:
    >>> # Add to ~/.zshrc:
    >>> # eval "$(gmuse completions zsh)"
"""

import json
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

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
        hint: Optional partial commit message typed by the user.
        timeout: Timeout in seconds for the generation.
    """

    staged_diff: str
    hint: Optional[str] = None
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
        import json

        return json.dumps(
            {
                "suggestion": self.suggestion,
                "status": self.status.value,
                "metadata": self.metadata,
            }
        )


# =============================================================================
# Zsh Completion Script Template
# =============================================================================

ZSH_COMPLETION_TEMPLATE = r"""#compdef git
#compdef git

# gmuse zsh completion script
# Provides AI-generated commit message suggestions for 'git commit -m'
#
# Installation:
#   Add to your ~/.zshrc:
#     eval "$(gmuse completions zsh)"
#
#   Then restart your shell:
#     exec zsh

# Cache policy for gmuse completions
_gmuse_cache_policy() {
    local cache_ttl="${GMUSE_COMPLETIONS_CACHE_TTL:-30}"
    local -a oldp
    # Invalidate cache if older than cache_ttl seconds
    oldp=( "$1"(Nms+${cache_ttl}) )
    (( $#oldp ))
}

# Main completion function for git commit -m
_gmuse_git_commit_message() {
    # Check if completions are enabled
    if [[ "${GMUSE_COMPLETIONS_ENABLED:-true}" != "true" ]]; then
        return 1
    fi

    local curcontext="$curcontext" state
    local -a suggestions
    local hint="${words[CURRENT]}"
    local timeout="${GMUSE_COMPLETIONS_TIMEOUT:-3.0}"
    local cache_key="gmuse_commit_suggestion"
    local json_output suggestion gmuse_status

    # Try to retrieve from cache first
    if _cache_invalid "$cache_key" || ! _retrieve_cache "$cache_key"; then
        # Call the runtime helper
        json_output=$(gmuse completions-run --shell zsh --for "git commit -m" --hint "$hint" --timeout "$timeout" 2>/dev/null)

        if [[ -z "$json_output" ]]; then
            _message -r "gmuse: Failed to generate suggestion"
            return 1
        fi

        # Parse JSON output using sed (avoiding jq dependency)
        gmuse_status=$(echo "$json_output" | sed -n 's/.*"status"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
        suggestion=$(echo "$json_output" | sed -n 's/.*"suggestion"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')

        # Handle non-ok statuses
        case "$gmuse_status" in
            no_staged_changes)
                _message -r "gmuse: No staged changes detected"
                return 1
                ;;
            timeout)
                _message -r "gmuse: Request timed out"
                return 1
                ;;
            offline)
                _message -r "gmuse: Offline or credentials missing"
                return 1
                ;;
            error)
                _message -r "gmuse: Error generating suggestion"
                return 1
                ;;
            ok)
                if [[ -n "$suggestion" ]]; then
                    suggestions=("$suggestion")
                    _store_cache "$cache_key" suggestions
                fi
                ;;
        esac
    fi

    # Provide the suggestion as a completion
    if [[ -n "${suggestions[1]}" ]]; then
        compadd -Q -S '' -- "${suggestions[@]}"
        return 0
    fi

    return 1
}

# Hook into git completion for commit -m
_git_commit_message_gmuse() {
    # Only activate for git commit -m pattern
    if [[ "${words[1]}" == "git" && "${words[2]}" == "commit" ]]; then
        local i
        for ((i = 3; i <= CURRENT; i++)); do
            if [[ "${words[i]}" == "-m" || "${words[i]}" == "--message" ]]; then
                if [[ $CURRENT -eq $((i + 1)) ]]; then
                    _gmuse_git_commit_message
                    return
                fi
            fi
        done
    fi

    # Fall back to default git completion
    _git "$@"
}

# Register with completion system using zstyle cache policy
zstyle ':completion:*' cache-path "${XDG_CACHE_HOME:-$HOME/.cache}/zsh"
zstyle ":completion:*:*:git:*" use-cache on
zstyle ":completion:*:*:git:*" cache-policy _gmuse_cache_policy

compdef _git_commit_message_gmuse git
"""


# =============================================================================
# Commands
# =============================================================================


@completions_app.command(name="zsh")
def completions_zsh() -> None:
    """Emit the zsh completion script to stdout.

    The script provides AI-generated commit message suggestions when completing
    'git commit -m'. Add to your ~/.zshrc using eval.

    Example:
        eval "$(gmuse completions zsh)"
    """
    typer.echo(ZSH_COMPLETION_TEMPLATE)


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
    hint: Optional[str] = typer.Option(
        None,
        "--hint",
        help="Partial commit message typed by the user",
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

    The output format is:
        {"suggestion": "...", "status": "ok|timeout|offline|no_staged_changes|error", "metadata": {...}}
    """
    start_time = time.time()

    # Override timeout from environment if set
    env_timeout = os.getenv("GMUSE_COMPLETIONS_TIMEOUT")
    if env_timeout:
        try:
            timeout = float(env_timeout)
        except ValueError:
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
                diff_was_truncated=False,
            )

            # Generate message
            result = generate_message(config=config, hint=hint, context=context)

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
