"""Inspect log location and privacy-safe gmuse metadata helpers."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gmuse.commit import GenerationPromptMetadata, ValidationOutcome

EVAL_SCHEMA_VERSION = "1.0"
DEFAULT_INSPECT_LOG_DIR = Path(".gmuse-evals") / "inspect"


class LogLocationError(ValueError):
    """Raised before execution when an explicit log location conflicts."""


@dataclass(frozen=True, slots=True)
class RunSummary:
    """Counts reported after Inspect entries have reached the solver."""

    planned_entries: int
    completed_entries: int
    validation_passed: int
    validation_failed: int
    operational_errors: int
    log_locations: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        """Return JSON-compatible summary fields."""
        return {
            "planned_entries": self.planned_entries,
            "completed_entries": self.completed_entries,
            "validation_passed": self.validation_passed,
            "validation_failed": self.validation_failed,
            "operational_errors": self.operational_errors,
            "log_locations": list(self.log_locations),
        }


def resolve_log_dir(
    log_dir: Path | str | None = None, *, explicit: bool = False
) -> Path:
    """Create and validate a local Inspect log directory.

    Default directories may contain prior independent runs. An explicitly
    selected directory is treated as a run identity and must be empty of
    existing Inspect logs to prevent accidental mixing.
    """
    path = (
        (Path(log_dir) if log_dir is not None else DEFAULT_INSPECT_LOG_DIR)
        .expanduser()
        .resolve()
    )
    if explicit and path.exists() and any(path.glob("*.eval")):
        raise LogLocationError(
            "Inspect log location already contains a conflicting run identity; choose a new --log-dir"
        )
    path.mkdir(parents=True, exist_ok=True)
    return path


def independent_run_id(suite_id: str, mode: str) -> str:
    """Return a collision-resistant identity independent of previous runs."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{suite_id}-{mode}-{uuid.uuid4().hex[:8]}"


def build_run_metadata(
    *,
    execution_mode: str,
    suite_id: str,
    suite_version: str,
    selected_case_ids: list[str] | tuple[str, ...],
    prompt_version: str,
    selected_model_ids: list[str] | tuple[str, ...] = (),
    effective_generation_defaults: dict[str, object] | None = None,
    guardrails: dict[str, Any] | None = None,
    fixture_schema_version: str = "1.0",
    deterministic_output_policy: str | None = None,
) -> dict[str, object]:
    """Build required run-level Inspect metadata without prompt text."""
    return {
        "gmuse_eval_schema_version": EVAL_SCHEMA_VERSION,
        "run_id": independent_run_id(suite_id, execution_mode),
        "execution_mode": execution_mode,
        "suite_id": suite_id,
        "suite_version": suite_version,
        "selected_case_ids": list(selected_case_ids),
        "selected_model_ids": list(selected_model_ids),
        "deterministic_output_policy": deterministic_output_policy,
        "effective_generation_defaults": effective_generation_defaults or {},
        "prompt_version": prompt_version,
        "gmuse_project_revision": _project_revision(),
        "guardrails": guardrails or {},
        "fixture_foundation_schema_version": fixture_schema_version,
    }


def build_sample_metadata(
    *,
    entry_id: str,
    case_id: str,
    candidate_kind: str,
    prompt: GenerationPromptMetadata | None = None,
    case_revision: int | None = None,
    fixture_id: str | None = None,
    fixture_revision: int | None = None,
    fixture_digest: str | None = None,
    rubric_id: str | None = None,
    rubric_version: str | None = None,
    generation: dict[str, object] | None = None,
    staged_diff_digest: str | None = None,
    validation: ValidationOutcome | dict[str, object] | None = None,
    operational_error: dict[str, Any] | None = None,
    timing: dict[str, object] | None = None,
    generated_message: str | None = None,
) -> dict[str, object]:
    """Build complete sample metadata while excluding raw prompts."""
    prompt_data: dict[str, object] = {}
    if prompt is not None:
        prompt_data = {
            "prompt_hash": prompt.prompt_hash,
            "prompt_sha256": prompt.prompt_sha256,
            "prompt_size_bytes": prompt.prompt_size_bytes,
            "estimated_input_tokens": prompt.estimated_input_tokens,
            "estimated_output_tokens": prompt.estimated_output_tokens,
            "prompt_version": prompt.prompt_version,
        }
    if isinstance(validation, ValidationOutcome):
        validation_data: dict[str, object] = {
            "valid": validation.valid,
            "category": validation.category,
            "message": validation.message,
        }
    else:
        validation_data = validation or {"valid": False}
    metadata: dict[str, object] = {
        "gmuse_eval_schema_version": EVAL_SCHEMA_VERSION,
        "entry_id": entry_id,
        "case_id": case_id,
        "case_revision": case_revision,
        "fixture_id": fixture_id,
        "fixture_revision": fixture_revision,
        "fixture_digest": fixture_digest,
        "rubric_id": rubric_id,
        "rubric_version": rubric_version,
        "candidate_kind": candidate_kind,
        "candidate_model": (generation or {}).get("model"),
        "generation_config": generation or {},
        "format": (generation or {}).get("format"),
        "history_depth": (generation or {}).get("history_depth"),
        "branch_inclusion": (generation or {}).get("include_branch"),
        "hint_present": (generation or {}).get("hint_present"),
        "repository_instructions_present": (generation or {}).get(
            "repository_instructions_present"
        ),
        "max_chars": (generation or {}).get("max_chars"),
        "temperature": (generation or {}).get("temperature"),
        "token_cap": (generation or {}).get("max_tokens"),
        "staged_diff_digest": staged_diff_digest,
        "validation": validation_data,
        "production_validation": validation_data,
        "validation_state": "passed" if validation_data.get("valid") else "failed",
        "validation_error_category": validation_data.get("category"),
        "validation_error_message": validation_data.get("message"),
        "operational_error": operational_error,
        "operational_error_category": (operational_error or {}).get("category"),
        "operational_error_message": (operational_error or {}).get("message"),
        "timing": timing or {},
        **prompt_data,
    }
    if generated_message is not None:
        metadata["generated_message"] = generated_message
    return metadata


def summarize_results(
    results: list[dict[str, Any]],
    *,
    planned_entries: int,
    log_locations: tuple[str, ...] = (),
) -> RunSummary:
    """Aggregate result metadata without scoring message quality."""
    passed = 0
    failed = 0
    operational = 0
    for result in results:
        error = result.get("operational_error")
        if error:
            operational += 1
        validation = result.get("validation") or {}
        if validation.get("valid"):
            passed += 1
        elif not error:
            failed += 1
    return RunSummary(
        planned_entries=planned_entries,
        completed_entries=len(results),
        validation_passed=passed,
        validation_failed=failed,
        operational_errors=operational,
        log_locations=log_locations,
    )


def json_metadata(metadata: dict[str, object]) -> str:
    """Serialize metadata deterministically for diagnostics and tests."""
    return json.dumps(metadata, sort_keys=True, separators=(",", ":"), default=str)


def _project_revision() -> str | None:
    """Best-effort repository revision without failing eval execution."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() or None


__all__ = [
    "DEFAULT_INSPECT_LOG_DIR",
    "EVAL_SCHEMA_VERSION",
    "LogLocationError",
    "RunSummary",
    "build_run_metadata",
    "build_sample_metadata",
    "independent_run_id",
    "json_metadata",
    "resolve_log_dir",
    "summarize_results",
]
