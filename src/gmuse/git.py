"""Git utilities for extracting repository information.

This module provides functions to interact with git repositories using subprocess
to extract staged diffs, commit history, and repository metadata.

Public API:
    - is_git_repository: Check if directory is a git repo
    - get_repo_root: Get repository root path
    - get_staged_diff: Extract staged changes
    - get_commit_history: Fetch recent commits
    - get_current_branch: Get current branch information
    - truncate_diff: Truncate large diffs
    - load_repository_instructions: Load .gmuse file

Data Classes:
    - StagedDiff: Staged changes information
    - CommitRecord: Single commit data
    - CommitHistory: Collection of commits
    - RepositoryInstructions: Content from .gmuse file
    - BranchInfo: Current branch information
"""

import hashlib
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, Optional

from gmuse.exceptions import NoStagedChangesError, NotAGitRepositoryError
from gmuse.logging import get_logger

logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_GIT_TIMEOUT_SHORT: Final[int] = 5
"""Timeout for quick git operations like rev-parse (seconds)."""

_GIT_TIMEOUT_LONG: Final[int] = 30
"""Timeout for potentially slow git operations like diff/log (seconds)."""


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------


@dataclass(slots=True)
class StagedDiff:
    """Represents the git diff of staged changes.

    This dataclass encapsulates all information about staged changes in a git
    repository, including the raw diff content and computed metadata.

    Attributes:
        raw_diff: Full output of `git diff --cached`
        files_changed: List of file paths that were modified
        lines_added: Total lines added across all files
        lines_removed: Total lines removed across all files
        hash: SHA256 hash of raw_diff (useful for caching/deduplication)
        size_bytes: Size of raw_diff in bytes
        truncated: Whether diff was truncated to fit token limits
    """

    raw_diff: str
    files_changed: list[str]
    lines_added: int
    lines_removed: int
    hash: str
    size_bytes: int
    truncated: bool = False


@dataclass(slots=True)
class CommitRecord:
    """Single commit from repository history.

    Attributes:
        hash: Full git commit SHA (40 characters)
        message: Commit message subject line
        author: Commit author name
        timestamp: Commit timestamp as datetime object
    """

    hash: str
    message: str
    author: str
    timestamp: datetime


@dataclass(slots=True)
class CommitHistory:
    """Collection of recent commits for style context.

    Used to provide the LLM with examples of the repository's commit style
    to help generate consistent messages.

    Attributes:
        commits: Ordered list of recent commits (newest first)
        depth: Number of commits requested (may differ from len(commits))
        repository_path: Absolute path to git repository root
    """

    commits: list[CommitRecord]
    depth: int
    repository_path: str


@dataclass(slots=True)
class RepositoryInstructions:
    """Project-level guidance from .gmuse file.

    The .gmuse file allows repository maintainers to provide custom guidance
    for commit message generation.

    Attributes:
        content: Raw text content from .gmuse file (empty if not found)
        file_path: Absolute path to .gmuse file
        exists: Whether .gmuse file was found in the repository
    """

    content: str
    file_path: str
    exists: bool


@dataclass(slots=True)
class BranchInfo:
    """Information about the current git branch.

    Used to provide context about the branch when generating commit messages.
    Branch names are sanitized to protect privacy and improve LLM understanding.

    Attributes:
        raw_name: Original branch name from git
        branch_type: Extracted branch type (e.g., 'feature', 'fix', 'hotfix')
        branch_summary: Sanitized summary of branch purpose (truncated, tickets masked)
        is_default: Whether this is a default branch (main, master, develop)
    """

    raw_name: str
    branch_type: Optional[str]
    branch_summary: Optional[str]
    is_default: bool = False


# -----------------------------------------------------------------------------
# Internal Helpers
# -----------------------------------------------------------------------------


def _run_git(
    *args: str,
    cwd: Optional[str] = None,
    timeout: int = _GIT_TIMEOUT_SHORT,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Execute a git command and return the result.

    This is the core helper used by all git operations in this module.

    Args:
        ``*args``: Git command arguments (without 'git' prefix)
        cwd: Working directory for the command (None = current directory)
        timeout: Command timeout in seconds
        check: If True, raise CalledProcessError on non-zero exit code

    Returns:
        CompletedProcess with captured stdout/stderr

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
        subprocess.TimeoutExpired: If command exceeds timeout
        FileNotFoundError: If git executable is not found
    """
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=timeout,
        check=check,
    )


def _count_diff_lines(raw_diff: str) -> tuple[int, int]:
    """Count added and removed lines in a diff.

    Args:
        raw_diff: Raw git diff output

    Returns:
        Tuple of (lines_added, lines_removed)
    """
    lines_added = 0
    lines_removed = 0

    for line in raw_diff.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            lines_added += 1
        elif line.startswith("-") and not line.startswith("---"):
            lines_removed += 1

    return lines_added, lines_removed


def _parse_commit_line(line: str) -> Optional[CommitRecord]:
    """Parse a single commit log line into a CommitRecord.

    Expected format: hash|author|timestamp|message

    Args:
        line: Raw log line from git

    Returns:
        CommitRecord if parsing succeeds, None otherwise
    """
    parts = line.split("|", 3)
    if len(parts) != 4:
        logger.warning(f"Skipping malformed commit line: {line}")
        return None

    hash_val, author, timestamp_str, message = parts

    try:
        timestamp = datetime.fromisoformat(timestamp_str)
    except ValueError:
        logger.warning(f"Invalid timestamp: {timestamp_str}")
        timestamp = datetime.now()

    return CommitRecord(
        hash=hash_val,
        message=message,
        author=author,
        timestamp=timestamp,
    )


def _sanitize_branch_name(branch_name: str, max_length: int = 60) -> str:
    """Sanitize branch name for prompt context.

    Normalizes separators, converts to lowercase, removes usernames and long hashes.
    Masks potential ticket IDs (e.g., JIRA-123 -> TICKET-XXX).

    Args:
        branch_name: Raw branch name from git
        max_length: Maximum length for sanitized name (default: 60)

    Returns:
        Sanitized branch name suitable for LLM context

    Example:
        >>> _sanitize_branch_name("feature/USER-123-add-auth")
        'feature/ticket-xxx-add-auth'
        >>> _sanitize_branch_name("fix/PROJ-456/update-api")
        'fix/ticket-xxx/update-api'
    """
    import re

    # Convert to lowercase
    sanitized = branch_name.lower()

    # Normalize separators (replace multiple slashes/hyphens/underscores)
    sanitized = re.sub(r"[/_-]+", "/", sanitized)

    # Remove common username patterns (user/*, username/*)
    sanitized = re.sub(r"^(user|username)/", "", sanitized)

    # Mask ticket IDs: PROJ-123, ABC-456, TICKET-789 -> ticket-xxx
    # Match uppercase letters followed by hyphen and digits
    sanitized = re.sub(r"\b[A-Z]{2,}-\d+\b", "ticket-xxx", sanitized, flags=re.IGNORECASE)

    # Remove long hex hashes (8+ hex characters)
    sanitized = re.sub(r"\b[0-9a-f]{8,}\b", "", sanitized)

    # Clean up multiple separators created by removals
    sanitized = re.sub(r"/+", "/", sanitized)
    sanitized = sanitized.strip("/")

    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rsplit("/", 1)[0]

    return sanitized


def _parse_branch_info(branch_name: str, max_length: int = 60) -> tuple[Optional[str], Optional[str]]:
    """Parse branch name into type and summary.

    Extracts branch type (feature, fix, hotfix, etc.) and summary from common
    branch naming patterns like 'type/description' or 'type-description'.

    Args:
        branch_name: Raw branch name from git
        max_length: Maximum length for branch summary (default: 60)

    Returns:
        Tuple of (branch_type, branch_summary), both can be None

    Example:
        >>> _parse_branch_info("feature/add-authentication")
        ('feature', 'add-authentication')
        >>> _parse_branch_info("fix/PROJ-123-bug-in-api")
        ('fix', 'ticket-xxx-bug-in-api')
    """
    # Sanitize first
    sanitized = _sanitize_branch_name(branch_name, max_length=max_length)

    if not sanitized:
        return None, None

    # Common branch type patterns
    branch_types = ["feature", "feat", "fix", "hotfix", "bugfix", "bug", "docs", "chore", "refactor", "test", "style"]

    # Try to extract type from common patterns: type/description or type-description
    parts = sanitized.split("/", 1)
    if len(parts) == 2 and parts[0] in branch_types:
        return parts[0], parts[1]

    # Check if it starts with a type followed by hyphen
    for branch_type in branch_types:
        if sanitized.startswith(f"{branch_type}-"):
            summary = sanitized[len(branch_type) + 1:]
            return branch_type, summary

    # No recognized type pattern, treat entire sanitized name as summary
    return None, sanitized


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------


def is_git_repository(path: Optional[Path] = None) -> bool:
    """Check if the current/specified directory is a git repository.

    Args:
        path: Directory to check, defaults to current directory

    Returns:
        True if directory is a git repository, False otherwise

    Example:
        >>> is_git_repository()
        True
        >>> is_git_repository(Path("/tmp"))
        False
    """
    try:
        result = _run_git(
            "rev-parse",
            "--git-dir",
            cwd=str(path) if path else None,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_repo_root(path: Optional[Path] = None) -> Path:
    """Get the root directory of the git repository.

    Args:
        path: Directory to start from, defaults to current directory

    Returns:
        Path to repository root

    Raises:
        NotAGitRepositoryError: If not in a git repository

    Example:
        >>> root = get_repo_root()
        >>> print(root)
        /home/user/my-project
    """
    if not is_git_repository(path):
        raise NotAGitRepositoryError(
            "Not a git repository. Run gmuse from within a git repository."
        )

    try:
        result = _run_git(
            "rev-parse",
            "--show-toplevel",
            cwd=str(path) if path else None,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise NotAGitRepositoryError(
            f"Failed to get repository root: {e.stderr}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise NotAGitRepositoryError("Git command timed out") from e


def get_staged_diff() -> StagedDiff:
    """Extract staged changes from git repository.

    Returns:
        StagedDiff object with diff content and metadata

    Raises:
        NotAGitRepositoryError: If not in a git repository
        NoStagedChangesError: If no files are staged

    Example:
        >>> diff = get_staged_diff()
        >>> print(diff.files_changed)
        ['src/main.py', 'tests/test_main.py']
    """
    if not is_git_repository():
        raise NotAGitRepositoryError(
            "Not a git repository. Run gmuse from within a git repository."
        )

    # Get the diff content
    try:
        result = _run_git("diff", "--cached", timeout=_GIT_TIMEOUT_LONG)
        raw_diff = result.stdout

        if not raw_diff.strip():
            raise NoStagedChangesError(
                "No staged changes found. Stage files with 'git add' first."
            )
    except subprocess.CalledProcessError as e:
        raise NotAGitRepositoryError(f"Failed to get staged diff: {e.stderr}") from e
    except subprocess.TimeoutExpired as e:
        raise NotAGitRepositoryError("Git diff command timed out") from e

    # Get list of changed files
    try:
        result_files = _run_git("diff", "--cached", "--name-only", timeout=10)
        files_changed = [f for f in result_files.stdout.strip().split("\n") if f]
    except subprocess.CalledProcessError:
        files_changed = []

    # Calculate metadata
    lines_added, lines_removed = _count_diff_lines(raw_diff)
    diff_hash = hashlib.sha256(raw_diff.encode()).hexdigest()
    size_bytes = len(raw_diff.encode())

    logger.debug(
        f"Extracted diff: {len(files_changed)} files, "
        f"+{lines_added}/-{lines_removed} lines, "
        f"{size_bytes} bytes"
    )

    return StagedDiff(
        raw_diff=raw_diff,
        files_changed=files_changed,
        lines_added=lines_added,
        lines_removed=lines_removed,
        hash=diff_hash,
        size_bytes=size_bytes,
        truncated=False,
    )


def get_commit_history(depth: int = 5) -> CommitHistory:
    """Fetch recent commit messages for style context.

    Args:
        depth: Number of commits to fetch (default: 5)

    Returns:
        CommitHistory object with recent commits

    Raises:
        NotAGitRepositoryError: If not in a git repository

    Example:
        >>> history = get_commit_history(depth=10)
        >>> for commit in history.commits:
        ...     print(commit.message)
    """
    if not is_git_repository():
        raise NotAGitRepositoryError(
            "Not a git repository. Run gmuse from within a git repository."
        )

    repo_root = get_repo_root()

    try:
        # Format: hash|author|timestamp|message
        result = _run_git(
            "log",
            f"-n{depth}",
            "--format=%H|%an|%aI|%s",
            timeout=_GIT_TIMEOUT_LONG,
        )

        commits = [
            commit
            for line in result.stdout.strip().split("\n")
            if line and (commit := _parse_commit_line(line))
        ]

        logger.debug(f"Fetched {len(commits)} commits from history")

        return CommitHistory(
            commits=commits,
            depth=depth,
            repository_path=str(repo_root),
        )

    except subprocess.CalledProcessError as e:
        # Handle new repository with no commits
        if "does not have any commits yet" in e.stderr:
            logger.debug("Repository has no commits yet")
            return CommitHistory(
                commits=[],
                depth=depth,
                repository_path=str(repo_root),
            )
        raise NotAGitRepositoryError(
            f"Failed to fetch commit history: {e.stderr}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise NotAGitRepositoryError("Git log command timed out") from e


def truncate_diff(diff: StagedDiff, max_bytes: int = 20000) -> StagedDiff:
    """Truncate diff to fit within token limits.

    Strategy:
    - Keep file headers (diff --git, ---, +++)
    - Keep as many lines as possible within byte limit
    - Add truncation marker when limit is reached
    - Preserve structure for LLM understanding

    Args:
        diff: StagedDiff to truncate
        max_bytes: Maximum size in bytes (default: 20000 ≈ 5000 tokens)

    Returns:
        New StagedDiff with truncated content and truncated=True

    Example:
        >>> large_diff = get_staged_diff()
        >>> truncated = truncate_diff(large_diff, max_bytes=10000)
        >>> print(truncated.truncated)
        True
    """
    if diff.size_bytes <= max_bytes:
        return diff

    logger.debug(f"Truncating diff from {diff.size_bytes} to ~{max_bytes} bytes")

    lines = diff.raw_diff.split("\n")
    truncated_lines: list[str] = []
    current_size = 0

    for line in lines:
        line_size = len(line.encode()) + 1  # +1 for newline

        # Always keep file headers for context
        is_header = (
            line.startswith("diff --git")
            or line.startswith("---")
            or line.startswith("+++")
        )

        if is_header:
            truncated_lines.append(line)
            current_size += line_size
            continue

        # Check if adding this line would exceed limit
        if current_size + line_size > max_bytes:
            truncated_lines.append("... (diff truncated for brevity)")
            break

        truncated_lines.append(line)
        current_size += line_size

    truncated_diff = "\n".join(truncated_lines)

    return StagedDiff(
        raw_diff=truncated_diff,
        files_changed=diff.files_changed,
        lines_added=diff.lines_added,
        lines_removed=diff.lines_removed,
        hash=diff.hash,  # Keep original hash for deduplication
        size_bytes=len(truncated_diff.encode()),
        truncated=True,
    )


def load_repository_instructions() -> RepositoryInstructions:
    """Load project-level instructions from .gmuse file.

    The .gmuse file allows repository maintainers to provide custom guidance
    for commit message generation (e.g., preferred formats, conventions).

    Returns:
        RepositoryInstructions object with content from .gmuse file

    Raises:
        NotAGitRepositoryError: If not in a git repository

    Example:
        >>> instructions = load_repository_instructions()
        >>> if instructions.exists:
        ...     print(instructions.content)
    """
    repo_root = get_repo_root()
    gmuse_path = repo_root / ".gmuse"

    if not gmuse_path.exists():
        logger.debug("No .gmuse file found")
        return RepositoryInstructions(
            content="",
            file_path=str(gmuse_path),
            exists=False,
        )

    try:
        content = gmuse_path.read_text(encoding="utf-8")
        logger.debug(f"Loaded .gmuse file: {len(content)} characters")
        return RepositoryInstructions(
            content=content.strip(),
            file_path=str(gmuse_path),
            exists=True,
        )
    except OSError as e:
        logger.warning(f"Failed to read .gmuse file: {e}")
        return RepositoryInstructions(
            content="",
            file_path=str(gmuse_path),
            exists=False,
        )


def get_current_branch(max_length: int = 60) -> Optional[BranchInfo]:
    """Get information about the current git branch.

    Extracts the current branch name and parses it into structured information
    for use as context in commit message generation. Returns None if the
    repository is in a detached HEAD state or if branch detection fails.

    Args:
        max_length: Maximum length for branch summary (default: 60)

    Returns:
        BranchInfo object with parsed branch information, or None if unavailable

    Raises:
        NotAGitRepositoryError: If not in a git repository

    Example:
        >>> branch = get_current_branch()
        >>> if branch and not branch.is_default:
        ...     print(f"Type: {branch.branch_type}, Summary: {branch.branch_summary}")
    """
    if not is_git_repository():
        raise NotAGitRepositoryError(
            "Not a git repository. Run gmuse from within a git repository."
        )

    try:
        # Get current branch name
        result = _run_git("rev-parse", "--abbrev-ref", "HEAD", timeout=_GIT_TIMEOUT_SHORT)
        raw_branch = result.stdout.strip()

        # Check for detached HEAD state
        if raw_branch == "HEAD":
            logger.debug("Repository is in detached HEAD state")
            return None

        # Check if it's a default branch
        default_branches = {"main", "master", "develop", "development"}
        is_default = raw_branch.lower() in default_branches

        # Parse branch info
        branch_type, branch_summary = _parse_branch_info(raw_branch, max_length=max_length)

        logger.debug(
            f"Extracted branch: raw='{raw_branch}', type={branch_type}, "
            f"summary={branch_summary}, is_default={is_default}"
        )

        return BranchInfo(
            raw_name=raw_branch,
            branch_type=branch_type,
            branch_summary=branch_summary,
            is_default=is_default,
        )

    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to get current branch: {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        logger.warning("Git branch command timed out")
        return None
