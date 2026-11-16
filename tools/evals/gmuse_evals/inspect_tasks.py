"""Inspect AI dataset/task adapters with lazy framework imports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gmuse.commit import ResponseGenerator

from .execution import CaseExecutionResult, execute_entry
from .logs import build_run_metadata, resolve_log_dir
from .runner import RunPlan


def _debug_directory(log_dir: Path) -> Path:
    """Return the debug root beside the canonical ``.gmuse-evals`` root."""
    marker = ".gmuse-evals"
    if marker in log_dir.parts:
        marker_index = log_dir.parts.index(marker)
        return Path(*log_dir.parts[: marker_index + 1]) / "debug"
    return log_dir.parent / "debug"


def build_dataset(plan: RunPlan) -> list[Any]:
    """Build one Inspect ``Sample`` for every selected run entry."""
    from inspect_ai.dataset import Sample

    return [
        Sample(
            input=entry.case_id,
            id=entry.entry_id,
            target="",
            metadata={
                "entry_id": entry.entry_id,
                "case_id": entry.case_id,
                "candidate_kind": entry.candidate_kind,
                "format": entry.generation.format,
                "model": entry.generation.model,
            },
        )
        for entry in plan.entries
    ]


@dataclass(frozen=True, slots=True)
class InspectRunResult:
    """Inspect logs and per-entry metadata returned by orchestration."""

    logs: tuple[Any, ...]
    results: tuple[dict[str, object], ...]
    log_dir: Path


def build_task(
    plan: RunPlan,
    *,
    preserve_debug: bool = False,
    debug_dir: Path | str | None = None,
    result_sink: list[dict[str, object]] | None = None,
    response_generator: ResponseGenerator | None = None,
) -> Any:
    """Build a framework task whose solver invokes gmuse production code.

    Inspect is imported only when a maintainer explicitly builds a runner task;
    importing normal ``gmuse`` modules never requires it.
    """
    from inspect_ai import Task
    from inspect_ai.model import ModelOutput
    from inspect_ai.solver import solver

    entries = {entry.entry_id: entry for entry in plan.entries}
    collected = result_sink if result_sink is not None else []

    @solver
    def gmuse_solver() -> Any:
        async def solve(state: Any, _generate: Any) -> Any:
            entry_id = str(state.sample_id)
            entry = entries[entry_id]
            result: CaseExecutionResult = execute_entry(
                entry,
                preserve_debug=preserve_debug,
                debug_dir=debug_dir,
                response_generator=response_generator,
            )
            metadata = result.as_metadata(entry)
            collected.append(metadata)
            state.metadata = {**(state.metadata or {}), **metadata}
            state.output = ModelOutput(
                model=entry.model or "deterministic-check",
                completion=result.message or "",
                metadata=metadata,
                error=(
                    result.operational_error.message
                    if result.operational_error is not None
                    else None
                ),
            )
            return state

        return solve

    metadata = build_run_metadata(
        execution_mode=plan.mode,
        suite_id=plan.suite_id,
        suite_version=plan.suite_version,
        selected_case_ids=plan.selected_case_ids,
        selected_model_ids=plan.models,
        prompt_version="1.0.0",
        effective_generation_defaults=plan.overrides,
        guardrails=dict(plan.guardrails.as_dict()),
        deterministic_output_policy=(
            "format_valid_v1" if plan.mode == "check" else None
        ),
    )
    return Task(
        dataset=build_dataset(plan),
        solver=gmuse_solver(),
        scorer=None,
        model="mockllm/deterministic",
        metadata=metadata,
        name=f"gmuse-{plan.suite_id}-{plan.mode}",
        fail_on_error=False,
        continue_on_fail=True,
        score_on_error=True,
    )


def run_inspect_plan(
    plan: RunPlan,
    *,
    log_dir: Path | str | None = None,
    preserve_debug: bool = False,
    response_generator: ResponseGenerator | None = None,
) -> InspectRunResult:
    """Execute a plan using Inspect's native eval/log pipeline."""
    from inspect_ai import eval as inspect_eval

    explicit = log_dir is not None
    resolved_log_dir = resolve_log_dir(log_dir, explicit=explicit)
    results: list[dict[str, object]] = []
    task = build_task(
        plan,
        preserve_debug=preserve_debug,
        debug_dir=(_debug_directory(resolved_log_dir) if preserve_debug else None),
        result_sink=results,
        response_generator=response_generator,
    )
    logs = inspect_eval(
        task,
        model="mockllm/deterministic",
        log_dir=str(resolved_log_dir),
        log_format="eval",
        display="none",
        score=False,
        fail_on_error=False,
        continue_on_fail=True,
        # Fixture execution changes process cwd; never overlap sample execution.
        max_samples=1,
    )
    return InspectRunResult(tuple(logs), tuple(results), resolved_log_dir)


__all__ = ["InspectRunResult", "build_dataset", "build_task", "run_inspect_plan"]
