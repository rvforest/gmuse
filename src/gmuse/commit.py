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
from typing import Any, Callable, Final, Optional, cast

from gmuse.config import ConfigDict
from gmuse.exceptions import InvalidMessageError
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
from gmuse.prompts import (
    PROMPT_VERSION,
    build_prompt,
    estimate_tokens,
    validate_message,
)

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


@dataclass(frozen=True, slots=True)
class GenerationPromptMetadata:
    """Privacy-safe observations about the prompts used for one attempt.

    Prompt text is intentionally not retained. Hashes, byte sizes, and rough
    token estimates are sufficient for comparing production-path runs without
    copying repository content into ordinary eval artifacts.

    Attributes:
        prompt_hash: SHA-256 hash of the system and user prompts together.
        system_prompt_hash: SHA-256 hash of the system prompt.
        user_prompt_hash: SHA-256 hash of the user prompt.
        prompt_size_bytes: Combined UTF-8 prompt size.
        system_prompt_size_bytes: UTF-8 size of the system prompt.
        user_prompt_size_bytes: UTF-8 size of the user prompt.
        estimated_input_tokens: Heuristic input token estimate.
        estimated_output_tokens: Heuristic output token estimate, when known.
        prompt_version: Version of gmuse's prompt builder.

    Example:
        >>> metadata = GenerationPromptMetadata.from_prompts("system", "diff")
        >>> len(metadata.prompt_hash)
        64
    """

    prompt_hash: str
    system_prompt_hash: str
    user_prompt_hash: str
    prompt_size_bytes: int
    system_prompt_size_bytes: int
    user_prompt_size_bytes: int
    estimated_input_tokens: int
    estimated_output_tokens: int | None = None
    prompt_version: str = PROMPT_VERSION

    @classmethod
    def from_prompts(
        cls,
        system_prompt: str,
        user_prompt: str,
        *,
        output: str | None = None,
        prompt_version: str = PROMPT_VERSION,
    ) -> "GenerationPromptMetadata":
        """Build metadata from prompt text without returning the text itself."""
        import hashlib

        def digest(value: str) -> str:
            return hashlib.sha256(value.encode("utf-8")).hexdigest()

        combined = f"{system_prompt}\n\n{user_prompt}"
        return cls(
            prompt_hash=digest(combined),
            system_prompt_hash=digest(system_prompt),
            user_prompt_hash=digest(user_prompt),
            prompt_size_bytes=len(combined.encode("utf-8")),
            system_prompt_size_bytes=len(system_prompt.encode("utf-8")),
            user_prompt_size_bytes=len(user_prompt.encode("utf-8")),
            estimated_input_tokens=estimate_tokens(combined),
            estimated_output_tokens=(
                estimate_tokens(output) if output is not None else None
            ),
            prompt_version=prompt_version,
        )

    @property
    def prompt_sha256(self) -> str:
        """Return the canonical prompt hash under its explicit name."""
        return self.prompt_hash


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    """Structured production validation outcome for a generated message."""

    valid: bool
    category: str | None = None
    message: str | None = None

    @property
    def status(self) -> str:
        """Return the contract-friendly validation state."""
        return "passed" if self.valid else "failed"

    @property
    def error_category(self) -> str | None:
        """Return the validation category under its explicit name."""
        return self.category


@dataclass(frozen=True, slots=True)
class GenerationOperationalError:
    """An operational failure observed while trying to generate a response."""

    category: str
    message: str
    exception_type: str
    exception: Exception | None = None


@dataclass(frozen=True, slots=True)
class GenerationAttemptResult:
    """Non-raising observation of one production generation attempt.

    Unlike :func:`generate_message`, this record retains invalid generated
    output and provider/setup failures so maintainer evals can log them.
    """

    message: str | None
    context: GenerationContext
    prompt: GenerationPromptMetadata
    validation: ValidationOutcome
    operational_error: GenerationOperationalError | None = None

    @property
    def raw_message(self) -> str | None:
        """Return the unmodified provider or deterministic response."""
        return self.message

    @property
    def prompt_metadata(self) -> GenerationPromptMetadata:
        """Return prompt observations under the explicit contract name."""
        return self.prompt

    @property
    def validation_outcome(self) -> ValidationOutcome:
        """Return production validation under the explicit contract name."""
        return self.validation


ResponseGenerator = Callable[..., str]
"""Typed injection seam for deterministic or test response generation."""


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
    credential_lookup_timeout: float | None = None,
    response_generator: ResponseGenerator | None = None,
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
    attempt = generate_message_attempt(
        config,
        hint=hint,
        context=context,
        credential_lookup_timeout=credential_lookup_timeout,
        response_generator=response_generator,
    )
    if attempt.operational_error is not None:
        if attempt.operational_error.exception is not None:
            raise attempt.operational_error.exception
        raise _restore_operational_exception(attempt.operational_error)
    if not attempt.validation.valid:
        raise InvalidMessageError(
            attempt.validation.message or "Invalid generated message"
        )
    assert attempt.message is not None
    return GenerationResult(message=attempt.message, context=attempt.context)


def generate_message_attempt(
    config: ConfigDict,
    hint: Optional[str] = None,
    context: Optional[GenerationContext] = None,
    credential_lookup_timeout: float | None = None,
    response_generator: ResponseGenerator | None = None,
) -> GenerationAttemptResult:
    """Observe one production generation attempt without hiding failures.

    The context, prompt builder, provider boundary, and validator are the same
    components used by :func:`generate_message`. ``response_generator`` is a
    typed internal seam used by offline evals; when omitted, the normal
    :class:`~gmuse.llm.LLMClient` is used.

    Args:
        config: Merged gmuse generation configuration.
        hint: Optional user hint.
        context: Pre-gathered context, or gather it from the current repository.
        credential_lookup_timeout: Optional credential lookup timeout.
        response_generator: Optional deterministic response callback.

    Returns:
        A result containing raw output, prompt metadata, validation, and any
        operational provider failure.

    Raises:
        NotAGitRepositoryError: If context must be gathered outside a Git repo.
        NoStagedChangesError: If context must be gathered without staged changes.
    """
    if context is None:
        context = gather_context(
            history_depth=config.get("history_depth", 5),
            max_diff_bytes=config.get("max_diff_bytes", DEFAULT_MAX_DIFF_BYTES),
            include_branch=config.get("include_branch", False),
            branch_max_length=config.get("branch_max_length", 60),
        )

    logger.debug("Building prompt (format=%s)...", config.get("format"))
    system_prompt, user_prompt = build_prompt(
        diff=context.diff,
        format=config.get("format", "freeform"),
        commit_history=context.history,
        repo_instructions=context.repo_instructions,
        branch_info=context.branch_info,
        user_hint=hint,
        learning_examples=None,
        max_chars=config.get("max_chars"),
    )

    prompt = GenerationPromptMetadata.from_prompts(system_prompt, user_prompt)
    try:
        if response_generator is not None:
            message = _call_response_generator(
                response_generator,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=float(config.get("temperature", 0.7)),
                max_tokens=int(config.get("max_tokens", 500)),
                model=config.get("model"),
            )
        else:
            client = LLMClient(
                model=config.get("model"),
                timeout=int(config.get("timeout") or 30),
                credential_lookup_timeout=credential_lookup_timeout,
            )
            message = client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=float(config.get("temperature", 0.7)),
                max_tokens=int(config.get("max_tokens", 500)),
            )
    except Exception as error:
        return GenerationAttemptResult(
            message=None,
            context=context,
            prompt=prompt,
            validation=ValidationOutcome(valid=False),
            operational_error=GenerationOperationalError(
                category="unknown",
                message=str(error),
                exception_type=type(error).__name__,
                exception=error,
            ),
        )

    max_chars = cast(int | None, config.get("max_chars"))
    effective_max = (
        max_chars
        if max_chars is not None
        else int(cast(Any, config.get("max_message_length", 1000)))
    )
    try:
        validate_message(
            message,
            format=config.get("format", "freeform"),
            max_length=effective_max,
        )
    except InvalidMessageError as error:
        return GenerationAttemptResult(
            message=message,
            context=context,
            prompt=GenerationPromptMetadata.from_prompts(
                system_prompt, user_prompt, output=message
            ),
            validation=ValidationOutcome(
                valid=False, category="validation", message=str(error)
            ),
        )

    return GenerationAttemptResult(
        message=message,
        context=context,
        prompt=GenerationPromptMetadata.from_prompts(
            system_prompt, user_prompt, output=message
        ),
        validation=ValidationOutcome(valid=True),
    )


def _restore_operational_exception(error: GenerationOperationalError) -> Exception:
    """Recreate the legacy exception class for ``generate_message`` callers."""
    from gmuse.exceptions import LLMError

    return LLMError(error.message)


def _call_response_generator(
    response_generator: ResponseGenerator,
    **kwargs: object,
) -> str:
    """Call injected seams with either rich or prompt-only callback shapes."""
    import inspect

    try:
        signature = inspect.signature(response_generator)
    except (TypeError, ValueError):
        return response_generator(**kwargs)
    parameters = signature.parameters.values()
    if any(parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in parameters):
        return response_generator(**kwargs)
    keyword_arguments = {
        name: value for name, value in kwargs.items() if name in signature.parameters
    }
    try:
        return response_generator(**keyword_arguments)
    except TypeError:
        return response_generator(kwargs["system_prompt"], kwargs["user_prompt"])
