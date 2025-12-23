"""Commit message generation service.

This module provides the core business logic for generating commit messages.
It orchestrates git operations, prompt building, and LLM interaction.

Public API:
    - generate_message: Main entry point for generating commit messages
    - gather_context: Collect context from git repository

Data Classes:
    - GenerationContext: Context gathered for generation
    - GenerationResult: Result of message generation
"""

from dataclasses import dataclass
from typing import Final, Optional

from gmuse.config import ConfigDict
from gmuse.git import (
    BranchInfo,
    CommitHistory,
    RepositoryInstructions,
    StagedDiff,
    get_commit_history,
    get_current_branch,
    get_staged_diff,
    load_repository_instructions,
    truncate_diff,
)
from gmuse.llm import LLMClient
from gmuse.logging import get_logger
from gmuse.prompts import build_prompt, validate_message

logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

DEFAULT_MAX_DIFF_BYTES: Final[int] = 20000
"""Default maximum diff size in bytes (~5000 tokens).

This serves as the default value but can be overridden via configuration
using max_diff_bytes parameter.
"""


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------


@dataclass(slots=True)
class GenerationContext:
    """Context gathered for commit message generation.

    This dataclass encapsulates all the information collected from the git
    repository that is used to generate a commit message.

    Attributes:
        diff: Staged changes from git
        history: Recent commit history for style context (None if empty)
        repo_instructions: Project-level guidance from .gmuse file (None if absent)
        branch_info: Current branch information (None if not included or unavailable)
        diff_was_truncated: Whether the diff was truncated to fit limits
    """

    diff: StagedDiff
    history: Optional[CommitHistory]
    repo_instructions: Optional[RepositoryInstructions]
    branch_info: Optional["BranchInfo"] = None
    diff_was_truncated: bool = False


@dataclass(slots=True)
class GenerationResult:
    """Result of commit message generation.

    Attributes:
        message: The generated commit message text
        context: The context that was used for generation
    """

    message: str
    context: GenerationContext


def gather_context(
    history_depth: int = 5,
    max_diff_bytes: int = DEFAULT_MAX_DIFF_BYTES,
    include_branch: bool = False,
    branch_max_length: int = 60,
) -> GenerationContext:
    """Gather all context needed for commit message generation.

    This function collects staged changes, commit history, repository
    instructions, and optionally branch information needed to generate
    a contextually appropriate commit message.

    Args:
        history_depth: Number of recent commits to fetch for style context
        max_diff_bytes: Maximum diff size in bytes before truncation
        include_branch: Whether to include current branch information
        branch_max_length: Maximum length for branch summary

    Returns:
        GenerationContext with all gathered information

    Raises:
        NotAGitRepositoryError: If not in a git repository
        NoStagedChangesError: If no files are staged
    """
    logger.debug("Gathering generation context...")

    # Get staged diff
    logger.debug("Extracting staged diff...")
    diff = get_staged_diff()

    # Truncate if necessary
    diff_was_truncated = False
    if diff.size_bytes > max_diff_bytes:
        logger.debug(f"Diff exceeds {max_diff_bytes} bytes, truncating...")
        diff = truncate_diff(diff, max_bytes=max_diff_bytes)
        diff_was_truncated = True

    # Get commit history for context
    logger.debug(f"Fetching commit history (depth={history_depth})...")
    history = get_commit_history(depth=history_depth)

    # Load repository instructions if present
    logger.debug("Checking for .gmuse file...")
    repo_instructions = load_repository_instructions()

    # Get branch info if requested
    branch_info = None
    if include_branch:
        logger.debug("Extracting branch information...")
        branch_info = get_current_branch(max_length=branch_max_length)
        # Skip default branches (main, master, develop) for privacy
        if branch_info and branch_info.is_default:
            logger.debug("Skipping default branch (not informative)")
            branch_info = None

    return GenerationContext(
        diff=diff,
        history=history if history.commits else None,
        repo_instructions=repo_instructions if repo_instructions.exists else None,
        branch_info=branch_info,
        diff_was_truncated=diff_was_truncated,
    )


def generate_message(
    config: ConfigDict,
    hint: Optional[str] = None,
    context: Optional[GenerationContext] = None,
) -> GenerationResult:
    """Generate a commit message from staged changes.

    This is the main entry point for commit message generation. It orchestrates
    context gathering, prompt building, and LLM interaction.

    Args:
        config: Merged configuration dictionary
        hint: Optional user hint for message generation
        context: Pre-gathered context (if None, will be gathered automatically)

    Returns:
        GenerationResult with the message and context used

    Raises:
        NotAGitRepositoryError: If not in a git repository
        NoStagedChangesError: If no files are staged
        LLMError: If LLM interaction fails
        InvalidMessageError: If generated message fails validation

    Example:
        >>> from gmuse.config import merge_config
        >>> config = merge_config()
        >>> result = generate_message(config, hint="security fix")
        >>> print(result.message)
        'fix(auth): patch XSS vulnerability in login form'
    """
    # Gather context if not provided
    if context is None:
        context = gather_context(
            history_depth=config.get("history_depth", 5),
            include_branch=config.get("include_branch", False),
            branch_max_length=config.get("branch_max_length", 60),
        )

    # Build prompt
    logger.debug(f"Building prompt (format={config.get('format')})...")
    system_prompt, user_prompt = build_prompt(
        diff=context.diff,
        format=config.get("format", "freeform"),
        commit_history=context.history,
        repo_instructions=context.repo_instructions,
        branch_info=context.branch_info,
        user_hint=hint,
        learning_examples=None,  # TODO: Implement learning in Phase 7
        max_chars=config.get("max_chars"),
    )

    # Initialize LLM client
    logger.debug(f"Initializing LLM client (model={config.get('model')})...")
    client = LLMClient(
        model=config.get("model"),
        timeout=int(config.get("timeout") or 30),
        provider=config.get("provider"),
    )

    # Generate message
    logger.debug("Generating commit message...")
    message = client.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=float(config.get("temperature", 0.7)),
        max_tokens=int(config.get("max_tokens", 500)),
    )

    # Validate message
    logger.debug("Validating generated message...")
    # Use configured max_chars if set, otherwise fall back to max_message_length
    effective_max = (
        int(config.get("max_chars"))
        if config.get("max_chars") is not None
        else int(config.get("max_message_length", 1000))
    )

    validate_message(
        message,
        format=config.get("format", "freeform"),
        max_length=effective_max,
    )

    logger.debug("Generation complete")

    return GenerationResult(
        message=message,
        context=context,
    )
