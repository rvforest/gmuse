"""Deterministic, offline reconstruction of fixture Git repositories."""

from __future__ import annotations

import os
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from gmuse.git import StagedDiff, get_staged_diff

from .models import EvalFixture

_GIT_TIMEOUT_SECONDS = 30


class ReconstructionError(RuntimeError):
    """Signal that a fixture cannot be reconstructed or staged.

    Translation into one domain exception keeps Git implementation details out
    of validation orchestration.

    Example:
        >>> raise ReconstructionError("patch did not apply")
        Traceback (most recent call last):
        ...
        ReconstructionError: patch did not apply
    """


@dataclass(frozen=True)
class ReconstructedRepository:
    """Temporary repository and its production-fidelity staged diff.

    The paired values let downstream runners reuse the exact validated working
    repository without recomputing evidence.

    Attributes:
        path: Temporary repository root, valid inside the context manager.
        staged_diff: Exact staged diff extracted through ``gmuse.git``.

    Example:
        >>> with reconstruct_fixture(fixture) as repository:
        ...     repository.staged_diff.hash
    """

    path: Path
    staged_diff: StagedDiff


def _run_git(
    repository: Path,
    *args: str,
    input_text: str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a checked Git command in the temporary repository."""
    command_environment = env or _isolated_git_environment()
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
            input=input_text,
            env=command_environment,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        detail = getattr(error, "stderr", "") or str(error)
        raise ReconstructionError(
            f"git {' '.join(args)} failed: {detail.strip()}"
        ) from error


def _isolated_git_environment() -> dict[str, str]:
    """Return an environment that cannot inherit Git-specific behavior."""
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_COUNT": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def _commit_environment(sequence: int) -> dict[str, str]:
    """Return deterministic identity and timestamp environment variables."""
    environment = _isolated_git_environment()
    timestamp = f"2000-01-{sequence + 1:02d}T00:00:00+0000"
    environment.update(
        {
            "GIT_AUTHOR_NAME": "gmuse eval",
            "GIT_AUTHOR_EMAIL": "gmuse-eval@example.invalid",
            "GIT_COMMITTER_NAME": "gmuse eval",
            "GIT_COMMITTER_EMAIL": "gmuse-eval@example.invalid",
            "GIT_AUTHOR_DATE": timestamp,
            "GIT_COMMITTER_DATE": timestamp,
        }
    )
    return environment


def _validate_fixture_paths(fixture: EvalFixture, repository: Path) -> None:
    """Defend the filesystem boundary even when models are constructed manually."""
    seen: set[str] = set()
    for item in fixture.base_files:
        if item.path in seen:
            raise ReconstructionError(f"duplicate base file path: {item.path}")
        seen.add(item.path)
        if ".git" in Path(item.path).parts:
            raise ReconstructionError(f"fixture path may not contain .git: {item.path}")
        target = (repository / item.path).resolve()
        if repository.resolve() not in target.parents:
            raise ReconstructionError(f"fixture path escapes repository: {item.path}")
        if any(ord(character) < 32 for character in item.path):
            raise ReconstructionError(
                f"fixture path contains control characters: {item.path}"
            )


def _materialize_base(fixture: EvalFixture, repository: Path) -> None:
    """Write UTF-8 fixture files and preserve executable modes."""
    _validate_fixture_paths(fixture, repository)
    for item in fixture.base_files:
        target = repository / item.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(item.content.encode("utf-8"))
        if item.executable:
            target.chmod(target.stat().st_mode | 0o111)
    if fixture.repository_instructions is not None:
        instructions = repository / ".gmuse"
        instructions.write_bytes(fixture.repository_instructions.encode("utf-8"))


def _commit_baseline(fixture: EvalFixture, repository: Path) -> None:
    """Create a real baseline commit and deterministic synthetic history."""
    _run_git(repository, "add", "--all")
    executable_paths = [item.path for item in fixture.base_files if item.executable]
    for path in executable_paths:
        _run_git(repository, "update-index", "--chmod=+x", "--", path)
    _run_git(
        repository,
        "commit",
        "--allow-empty",
        "-m",
        "fixture: establish base",
        env=_commit_environment(0),
    )
    # Fixture history is recorded newest-first, matching gmuse.git's production
    # history extraction. Commit it oldest-first so ``git log`` returns the
    # declared order without exposing the bootstrap commit.
    for sequence, history in enumerate(reversed(fixture.history), start=1):
        args = ["commit", "--allow-empty", "-m", history.subject]
        if history.body:
            args.extend(["-m", history.body])
        _run_git(repository, *args, env=_commit_environment(sequence))


def _checkout_branch(fixture: EvalFixture, repository: Path) -> None:
    """Create the requested branch after validating Git's ref rules."""
    if not fixture.branch_name:
        return
    _run_git(repository, "check-ref-format", "--branch", fixture.branch_name)
    _run_git(repository, "checkout", "-b", fixture.branch_name)


def _apply_patch(fixture: EvalFixture, repository: Path) -> None:
    """Apply only complete, safe patches to both worktree and index."""
    _run_git(repository, "apply", "--check", "--index", input_text=fixture.patch)
    _run_git(repository, "apply", "--index", input_text=fixture.patch)


def _configure_deterministic_git(repository: Path) -> None:
    """Override user/global settings that can change staged diff bytes."""
    settings = {
        "diff.noprefix": "false",
        "diff.mnemonicPrefix": "false",
        "diff.context": "3",
        "diff.algorithm": "myers",
        "color.ui": "false",
        "color.diff": "false",
        "core.quotePath": "true",
        "core.autocrlf": "false",
        "core.eol": "lf",
        "core.filemode": "true",
        "commit.gpgsign": "false",
    }
    for key, value in settings.items():
        _run_git(repository, "config", "--local", key, value)


@contextmanager
def reconstruct_fixture(fixture: EvalFixture) -> Iterator[ReconstructedRepository]:
    """Reconstruct one fixture in a temporary repository.

    The yielded diff is obtained through :func:`gmuse.git.get_staged_diff`, so
    its raw text and SHA-256 digest have the same semantics as production.

    Args:
        fixture: Validated offline fixture to materialize and stage.

    Yields:
        A temporary repository and its exact staged diff.

    Raises:
        ReconstructionError: If repository setup, patching, or diff extraction
            fails or exceeds the Git timeout.

    Example:
        >>> with reconstruct_fixture(fixture) as repository:
        ...     assert repository.staged_diff.files_changed
    """
    with tempfile.TemporaryDirectory(prefix="gmuse-eval-") as temporary:
        repository = Path(temporary)
        _run_git(repository, "init", "-q", "-b", "main")
        _run_git(repository, "config", "user.name", "gmuse eval")
        _run_git(repository, "config", "user.email", "gmuse-eval@example.invalid")
        _configure_deterministic_git(repository)
        hooks = repository / ".gmuse-eval-hooks"
        hooks.mkdir()
        _run_git(repository, "config", "core.hooksPath", str(hooks))
        _materialize_base(fixture, repository)
        _commit_baseline(fixture, repository)
        _checkout_branch(fixture, repository)
        _apply_patch(fixture, repository)
        try:
            staged = get_staged_diff(
                path=repository, git_env=_isolated_git_environment()
            )
        except Exception as error:  # pragma: no cover - defensive translation
            raise ReconstructionError(
                f"unable to extract staged patch: {error}"
            ) from error
        yield ReconstructedRepository(repository, staged)
