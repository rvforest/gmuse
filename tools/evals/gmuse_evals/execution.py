"""Execute run entries through gmuse's production generation path."""

from __future__ import annotations

import contextlib
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gmuse.commit import (
    GenerationAttemptResult,
    GenerationContext,
    GenerationPromptMetadata,
    ResponseGenerator,
    ValidationOutcome,
    gather_context,
    generate_message_attempt,
)
from gmuse.exceptions import NoStagedChangesError

from .deterministic import deterministic_response
from .errors import OperationalError, classify_error
from .git_reconstruct import ReconstructionError, reconstruct_fixture
from .runner import RunEntry


@dataclass(frozen=True, slots=True)
class CaseExecutionResult:
    """Structured result of one reconstructed repository execution."""

    entry_id: str
    case_id: str
    message: str | None
    validation: ValidationOutcome
    operational_error: OperationalError | None
    prompt: GenerationPromptMetadata
    context: GenerationContext | None
    staged_diff_digest: str | None
    duration_seconds: float
    preserved_repository: str | None = None
    raw_prompt: str | None = None

    def as_metadata(self, entry: RunEntry) -> dict[str, object]:
        """Return Inspect-safe sample metadata, including invalid output."""
        from .logs import build_sample_metadata

        return build_sample_metadata(
            entry_id=self.entry_id,
            case_id=self.case_id,
            candidate_kind=entry.candidate_kind,
            prompt=self.prompt,
            case_revision=entry.case.revision,
            fixture_id=entry.fixture.id,
            fixture_revision=entry.fixture.revision,
            fixture_digest=entry.fixture.expected_staged_diff_sha256,
            rubric_id=entry.validated_case.rubric.id,
            rubric_version=entry.validated_case.rubric.version,
            generation=entry.generation.as_dict(),
            staged_diff_digest=self.staged_diff_digest,
            validation=self.validation,
            operational_error=(
                self.operational_error.as_dict() if self.operational_error else None
            ),
            timing={"duration_seconds": self.duration_seconds},
            generated_message=self.message,
        )


@contextlib.contextmanager
def _working_directory(path: Path):
    """Temporarily run production Git helpers inside a reconstructed repo."""
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _empty_prompt() -> GenerationPromptMetadata:
    """Return safe placeholder metadata for setup failures before prompting."""
    return GenerationPromptMetadata.from_prompts("", "")


def _debug_copy(
    repository: Path, prompt: str | None, debug_dir: Path | None, entry_id: str
) -> tuple[str | None, str | None]:
    """Copy troubleshooting artifacts outside ordinary Inspect metadata."""
    if debug_dir is None:
        return None, None
    target = debug_dir / entry_id.replace("/", "_").replace(":", "_")
    target.mkdir(parents=True, exist_ok=True)
    repository_copy = target / "repository"
    shutil.copytree(repository, repository_copy, dirs_exist_ok=True)
    raw_prompt = None
    if prompt is not None:
        prompt_path = target / "prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")
        raw_prompt = str(prompt_path)
    return str(repository_copy), raw_prompt


def execute_entry(
    entry: RunEntry,
    *,
    response_generator: ResponseGenerator | None = None,
    preserve_debug: bool = False,
    debug_dir: Path | str | None = None,
) -> CaseExecutionResult:
    """Reconstruct, stage, and execute one entry through gmuse production code."""
    started = time.perf_counter()
    debug_root = (
        Path(debug_dir).expanduser().resolve() if debug_dir is not None else None
    )
    if preserve_debug and debug_root is None:
        debug_root = Path(".gmuse-evals") / "debug"

    try:
        with reconstruct_fixture(entry.fixture) as repository:
            with _working_directory(repository.path):
                if entry.generation.repository_instructions is not None:
                    (repository.path / ".gmuse").write_text(
                        entry.generation.repository_instructions, encoding="utf-8"
                    )
                if not repository.staged_diff.raw_diff.strip():
                    raise NoStagedChangesError(
                        "fixture reconstruction produced no staged diff"
                    )
                if (
                    repository.staged_diff.hash
                    != entry.fixture.expected_staged_diff_sha256
                ):
                    raise ReconstructionError(
                        "staged diff digest mismatch after reconstruction"
                    )
                context = gather_context(
                    history_depth=entry.generation.history_depth,
                    max_diff_bytes=entry.generation.max_diff_bytes,
                    include_branch=entry.generation.include_branch,
                )
                callback = response_generator
                if callback is None and entry.candidate_kind == "deterministic_check":
                    callback = lambda **kwargs: deterministic_response(
                        format=entry.generation.format,
                        case_id=entry.case_id,
                        change_type=entry.fixture.change_type,
                        max_chars=entry.generation.max_chars,
                        **kwargs,
                    )
                attempt: GenerationAttemptResult = generate_message_attempt(
                    {
                        "format": entry.generation.format,
                        "history_depth": entry.generation.history_depth,
                        "include_branch": entry.generation.include_branch,
                        "max_chars": entry.generation.max_chars,
                        "max_message_length": entry.generation.max_chars or 1000,
                        "model": entry.generation.model,
                        "temperature": entry.generation.temperature,
                        "max_tokens": entry.generation.max_tokens,
                        "max_diff_bytes": entry.generation.max_diff_bytes,
                        "timeout": entry.generation.timeout,
                    },
                    hint=entry.generation.hint,
                    context=context,
                    response_generator=callback,
                )
                raw_prompt = None
                if preserve_debug:
                    raw_prompt = _raw_prompt_for_context(attempt, entry)
                    preserved_repository, prompt_path = _debug_copy(
                        repository.path,
                        raw_prompt,
                        debug_root,
                        entry.entry_id,
                    )
                else:
                    preserved_repository, prompt_path = None, None
                operational = _attempt_operational_error(attempt)
                return CaseExecutionResult(
                    entry_id=entry.entry_id,
                    case_id=entry.case_id,
                    message=attempt.message,
                    validation=attempt.validation,
                    operational_error=operational,
                    prompt=attempt.prompt,
                    context=attempt.context,
                    staged_diff_digest=repository.staged_diff.hash,
                    duration_seconds=time.perf_counter() - started,
                    preserved_repository=preserved_repository,
                    raw_prompt=prompt_path,
                )
    except Exception as error:
        operational = classify_error(error)
        return CaseExecutionResult(
            entry_id=entry.entry_id,
            case_id=entry.case_id,
            message=None,
            validation=ValidationOutcome(
                valid=False, category="operational", message=str(error)
            ),
            operational_error=operational,
            prompt=_empty_prompt(),
            context=None,
            staged_diff_digest=None,
            duration_seconds=time.perf_counter() - started,
        )


def _attempt_operational_error(
    attempt: GenerationAttemptResult,
) -> OperationalError | None:
    """Classify an attempt error while preserving its separate channel."""
    if attempt.operational_error is None:
        return None
    return classify_error(RuntimeError(attempt.operational_error.message))


def _raw_prompt_for_context(attempt: GenerationAttemptResult, entry: RunEntry) -> str:
    """Build the debug-only prompt text from the same production context."""
    from gmuse.prompts import build_prompt

    assert attempt.context is not None
    system, user = build_prompt(
        diff=attempt.context.diff,
        format=entry.generation.format,
        commit_history=attempt.context.history,
        repo_instructions=attempt.context.repo_instructions,
        branch_info=attempt.context.branch_info,
        user_hint=entry.generation.hint,
        max_chars=entry.generation.max_chars,
    )
    return f"SYSTEM:\n{system}\n\nUSER:\n{user}"


__all__ = ["CaseExecutionResult", "execute_entry"]
