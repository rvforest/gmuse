"""Prompt builder for LLM commit message generation.

This module assembles prompts from various context sources including staged diffs,
commit history, repository instructions, and learning examples.

Public API:
    - build_prompt: Build complete system and user prompts
    - build_context: Build context section from various sources
    - validate_message: Validate generated commit message
    - estimate_tokens: Estimate token count for text

Format-specific task prompts:
    - get_freeform_task: Natural language commit messages
    - get_conventional_task: Conventional Commits format
    - get_gitmoji_task: Gitmoji-style commit messages
"""

import re
from typing import Final, List, Optional, Tuple

from gmuse.exceptions import InvalidMessageError
from gmuse.git import BranchInfo, CommitHistory, RepositoryInstructions, StagedDiff
from gmuse.logging import get_logger

logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

PROMPT_VERSION: Final[str] = "1.0.0"
"""Version identifier for prompt format (useful for tracking/debugging)."""

SYSTEM_PROMPT: Final[
    str
] = """You are an expert commit message generator. Your role is to analyze code changes and produce clear, informative commit messages that help developers understand what changed and why.

Guidelines:
- Focus on WHAT changed and WHY (when obvious from diff)
- Be concise but informative
- Use technical terminology appropriately
- Avoid stating the obvious (e.g., "Updated file.py")
- Prioritize clarity over cleverness"""
"""Base system prompt used for all commit message generations."""

MAX_MESSAGE_LENGTH: Final[int] = 1000
"""Default maximum allowed length for generated commit messages.

This serves as the default value used by validate_message() when no max_length
parameter is provided. Can be overridden per-call or via configuration.
"""

# -----------------------------------------------------------------------------
# Format-Specific Task Prompts
# -----------------------------------------------------------------------------


def get_freeform_task() -> str:
    """Get task prompt for freeform commit messages.

    Returns:
        Task prompt string

    Example:
        >>> task = get_freeform_task()
        >>> print(task)
        Generate a commit message in natural language...
    """
    return """Generate a commit message in natural language.

Requirements:
- Use imperative mood (e.g., "Add feature" not "Added feature")
- Keep it concise (1-3 sentences)
- Focus on the most significant changes
- No special formatting required

Output only the commit message text, nothing else."""


def get_conventional_task(max_chars: int | None = None) -> str:
    """Get task prompt for conventional commit messages.

    Args:
        max_chars: Optional override for maximum characters. When provided, the
            default fixed-length guidance is omitted to avoid conflicting
            instructions.

    Returns:
        Task prompt string

    Example:
        >>> task = get_conventional_task()
        >>> print(task)
        Generate a commit message following Conventional Commits specification...
    """
    length_guidance = (
        "- Keep total length under 100 characters\n" if max_chars is None else ""
    )

    return f"""Generate a commit message following Conventional Commits specification.

Format: type(scope): description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style/formatting (no logic change)
- refactor: Code restructuring (no behavior change)
- test: Adding or updating tests
- chore: Build process, dependencies, etc.

Requirements:
- type is REQUIRED
- scope is OPTIONAL (use if changes are focused on one area)
- description must be lowercase, imperative mood
{length_guidance}- No period at end of description

Examples:
feat(auth): add JWT token validation
fix(api): handle null pointer in user endpoint
docs: update installation instructions

Output only the commit message (one line), nothing else."""


def get_gitmoji_task() -> str:
    """Get task prompt for gitmoji commit messages.

    Returns:
        Task prompt string

    Example:
        >>> task = get_gitmoji_task()
        >>> print(task)
        Generate a commit message with a relevant emoji prefix...
    """
    return """Generate a commit message with a relevant emoji prefix (gitmoji style).

Common emojis and their meanings:
✨ :sparkles: - New feature
🐛 :bug: - Bug fix
📝 :memo: - Documentation
💄 :lipstick: - UI/styling
♻️ :recycle: - Refactoring
✅ :white_check_mark: - Tests
🔧 :wrench: - Configuration
⚡ :zap: - Performance
🔒 :lock: - Security

Format: emoji description

Requirements:
- Choose emoji based on primary change type
- Description should be concise, imperative mood
- Use only ONE emoji (the most relevant)

Examples:
✨ Add JWT authentication
🐛 Fix null pointer in user endpoint
📝 Update installation guide

Output only the commit message (emoji + description), nothing else."""


# -----------------------------------------------------------------------------
# Context Building
# -----------------------------------------------------------------------------


def build_context(
    diff: StagedDiff,
    commit_history: Optional[CommitHistory] = None,
    repo_instructions: Optional[RepositoryInstructions] = None,
    branch_info: Optional[BranchInfo] = None,
    user_hint: Optional[str] = None,
    learning_examples: Optional[List[Tuple[str, str]]] = None,
) -> str:
    """Build context section of prompt from various sources.

    Args:
        diff: Staged diff information
        commit_history: Recent commit history for style context
        repo_instructions: Repository-level instructions from .gmuse file
        branch_info: Current branch information for context
        user_hint: User-provided hint via --hint flag
        learning_examples: List of (generated, final) message pairs from learning

    Returns:
        Formatted context string

    Example:
        >>> from gmuse.git import StagedDiff
        >>> diff = StagedDiff(
        ...     raw_diff="diff --git a/file.py...",
        ...     files_changed=["file.py"],
        ...     lines_added=10,
        ...     lines_removed=2,
        ...     hash="abc123",
        ...     size_bytes=500,
        ... )
        >>> context = build_context(diff)
        >>> print(context)
        Staged changes summary:
        - Files changed: 1
        ...
    """
    parts: List[str] = []

    # Add branch context if available
    if branch_info:
        parts.append("Branch context:")
        if branch_info.branch_type:
            parts.append(f"- Branch type: {branch_info.branch_type}")
        if branch_info.branch_summary:
            parts.append(f"- Branch summary: {branch_info.branch_summary}")
        parts.append("")  # Empty line

    # Add commit history if available
    if commit_history and commit_history.commits:
        parts.append("Recent commits for style reference:")
        for commit in commit_history.commits[:5]:  # Limit to 5 commits
            parts.append(f"- {commit.message}")
        parts.append("")  # Empty line

    # Add repository instructions if available
    if repo_instructions and repo_instructions.exists and repo_instructions.content:
        parts.append("Repository instructions:")
        parts.append(repo_instructions.content)
        parts.append("")  # Empty line

    # Add user hint if provided
    if user_hint:
        parts.append(f"User hint: {user_hint}")
        parts.append("")  # Empty line

    # Add learning examples if available
    if learning_examples and len(learning_examples) > 0:
        parts.append("Previous style examples from this repository:")
        parts.append("")
        for i, (generated, final) in enumerate(learning_examples[:5], 1):
            parts.append(f"Example {i}:")
            parts.append(f'Generated: "{generated}"')
            parts.append(f'You edited to: "{final}"')
            parts.append("")
        parts.append("Please match this editing style in your response.")
        parts.append("")  # Empty line

    # Add diff summary
    parts.append("Staged changes summary:")
    parts.append(f"- Files changed: {len(diff.files_changed)}")
    parts.append(f"- Lines added: {diff.lines_added}")
    parts.append(f"- Lines removed: {diff.lines_removed}")
    parts.append("")  # Empty line

    # Add diff content
    if diff.truncated:
        parts.append("[Diff truncated to fit token limits]")
    parts.append("Diff:")
    parts.append(diff.raw_diff)

    return "\n".join(parts)


def build_prompt(
    diff: StagedDiff,
    format: str = "freeform",
    commit_history: Optional[CommitHistory] = None,
    repo_instructions: Optional[RepositoryInstructions] = None,
    branch_info: Optional[BranchInfo] = None,
    user_hint: Optional[str] = None,
    learning_examples: Optional[List[Tuple[str, str]]] = None,
    max_chars: Optional[int] = None,
) -> Tuple[str, str]:
    """Build complete prompt for LLM generation.

    Args:
        diff: Staged diff information
        format: Message format style ("freeform", "conventional", "gitmoji")
        commit_history: Recent commit history for style context
        repo_instructions: Repository-level instructions from .gmuse file
        branch_info: Current branch information for context
        user_hint: User-provided hint via --hint flag
        learning_examples: List of (generated, final) message pairs from learning

    Returns:
        Tuple of (system_prompt, user_prompt)

    Raises:
        ValueError: If format is not recognized

    Example:
        >>> from gmuse.git import StagedDiff
        >>> diff = StagedDiff(
        ...     raw_diff="diff --git a/file.py...",
        ...     files_changed=["file.py"],
        ...     lines_added=10,
        ...     lines_removed=2,
        ...     hash="abc123",
        ...     size_bytes=500,
        ... )
        >>> system, user = build_prompt(diff, format="conventional")
        >>> print(system)
        You are an expert commit message generator...
    """
    # Get system prompt
    system_prompt = SYSTEM_PROMPT

    # Build context
    context = build_context(
        diff=diff,
        commit_history=commit_history,
        repo_instructions=repo_instructions,
        branch_info=branch_info,
        user_hint=user_hint,
        learning_examples=learning_examples,
    )

    # Get task prompt based on format
    task_prompt_map = {
        "freeform": get_freeform_task,
        "conventional": get_conventional_task,
        "gitmoji": get_gitmoji_task,
    }

    if format not in task_prompt_map:
        raise ValueError(
            f"Unknown format: {format}. Must be one of: {list(task_prompt_map.keys())}"
        )

    # Only conventional format needs max_chars parameter to conditionally suppress
    # its default "100 characters" guidance. Freeform and gitmoji have no specific
    # numeric length constraints, so they work fine with the universal constraint below.
    task_prompt = task_prompt_map[format](
        **({"max_chars": max_chars} if format == "conventional" else {})
    )

    # If max_chars is provided, append an explicit constraint to the user prompt
    # for all formats.
    if max_chars is not None:
        task_prompt = (
            task_prompt
            + f"\n\nAdditional requirement:\n- Ensure the final commit message is at most {max_chars} characters long."
        )

    # Combine context and task
    user_prompt = f"{context}\n\n{task_prompt}"

    logger.debug(
        f"Built prompt: system={len(system_prompt)} chars, "
        f"user={len(user_prompt)} chars, format={format}"
    )

    return system_prompt, user_prompt


# -----------------------------------------------------------------------------
# Message Validation
# -----------------------------------------------------------------------------


def validate_message(
    message: str, format: str = "freeform", max_length: int = MAX_MESSAGE_LENGTH
) -> None:
    """Validate generated commit message.

    Args:
        message: Generated commit message to validate
        format: Expected message format
        max_length: Maximum allowed message length (default: 1000)

    Raises:
        InvalidMessageError: If message fails validation

    Example:
        >>> validate_message("feat(auth): add JWT", format="conventional")
        # No error
        >>> validate_message("", format="freeform")
        Traceback (most recent call last):
        ...
        InvalidMessageError: Generated message is empty
    """
    # Basic checks
    if not message or not message.strip():
        raise InvalidMessageError("Generated message is empty")

    if len(message) > max_length:
        raise InvalidMessageError(
            f"Message too long: {len(message)} characters (max {max_length})"
        )

    # Format-specific validation
    if format == "conventional":
        pattern = r"^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+"
        if not re.match(pattern, message):
            raise InvalidMessageError(
                f"Message does not match Conventional Commits format.\n"
                f"Expected: type(scope): description\n"
                f"Got: {message}"
            )

    elif format == "gitmoji":
        # Check if message starts with an emoji (Unicode character in emoji range)
        if not re.match(
            r"^[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF] ", message
        ):
            raise InvalidMessageError(
                f"Message does not start with an emoji.\n"
                f"Expected: emoji description\n"
                f"Got: {message}"
            )

    logger.debug(f"Message validated successfully: format={format}")


# -----------------------------------------------------------------------------
# Token Estimation
# -----------------------------------------------------------------------------

_CHARS_PER_TOKEN: Final[int] = 4
"""Default characters per token heuristic for GPT models.

This serves as the default value used by estimate_tokens() when no chars_per_token
parameter is provided. Can be overridden per-call or via configuration.
"""


def estimate_tokens(text: str, chars_per_token: int = _CHARS_PER_TOKEN) -> int:
    """Estimate token count for text.

    Uses a simple heuristic (default: ~4 characters per token, approximate for
    GPT models). This is a rough estimate and actual token counts vary by model
    and tokenizer.

    Args:
        text: Text to estimate tokens for
        chars_per_token: Characters per token heuristic (default: 4)

    Returns:
        Estimated token count

    Example:
        >>> estimate_tokens("Hello world")
        3
        >>> estimate_tokens("A" * 400)
        100
    """
    return len(text) // chars_per_token
