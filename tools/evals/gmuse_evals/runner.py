"""Run-plan resolution and orchestration for maintainer evals."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from gmuse.config import DEFAULTS

from .models import EvalCase, EvalFixture
from .validate import ValidatedCase, ValidatedSuite

RunMode = Literal["check", "live"]


class RunPlanError(ValueError):
    """Raised when a validated suite cannot produce a safe run plan.

    Example:
        >>> raise RunPlanError("no cases")
        Traceback (most recent call last):
        ...
        RunPlanError: no cases
    """


@dataclass(frozen=True, slots=True)
class Guardrails:
    """Explicit resource limits for live execution.

    Example:
        >>> Guardrails(max_samples=2).configured()
        True
    """

    max_samples: int | None = None
    max_tokens: int | None = None
    max_cost: float | None = None
    time_limit: int | None = None
    concurrency: int | None = None

    def as_dict(self) -> dict[str, int | float | None]:
        """Return JSON-compatible configured limits."""
        return {
            "samples": self.max_samples,
            "tokens": self.max_tokens,
            "cost": self.max_cost,
            "time": self.time_limit,
            "concurrency": self.concurrency,
        }

    def configured(self) -> bool:
        """Return whether at least one meaningful limit is configured."""
        return self.max_samples is not None and self.max_samples > 0


@dataclass(frozen=True, slots=True)
class EffectiveGenerationConfig:
    """Generation settings resolved for one case/format/model entry.

    Example:
        >>> config = EffectiveGenerationConfig("freeform", 0, False, None, None, None, None, 0.7, 500, 20000, 30)
        >>> config.format
        'freeform'
    """

    format: str
    history_depth: int
    include_branch: bool
    hint: str | None
    repository_instructions: str | None
    max_chars: int | None
    model: str | None
    temperature: float
    max_tokens: int
    max_diff_bytes: int
    timeout: int

    def as_dict(self) -> dict[str, object]:
        """Return stable JSON-compatible generation metadata."""
        return {
            "format": self.format,
            "history_depth": self.history_depth,
            "include_branch": self.include_branch,
            "hint_present": bool(self.hint),
            "repository_instructions_present": bool(self.repository_instructions),
            "max_chars": self.max_chars,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_diff_bytes": self.max_diff_bytes,
            "timeout": self.timeout,
        }


@dataclass(frozen=True, slots=True)
class RunEntry:
    """One stable case/format/model execution entry.

    Example:
        >>> RunEntry.__name__
        'RunEntry'
    """

    entry_id: str
    validated_case: ValidatedCase
    generation: EffectiveGenerationConfig
    candidate_kind: Literal["deterministic_check", "live_model"]

    @property
    def case(self) -> EvalCase:
        """Return the source case configuration."""
        return self.validated_case.case

    @property
    def case_id(self) -> str:
        """Return the stable case ID."""
        return self.case.id

    @property
    def fixture(self) -> EvalFixture:
        """Return the resolved fixture."""
        return self.validated_case.fixture

    @property
    def model(self) -> str | None:
        """Return the selected model, if this is a live entry."""
        return self.generation.model


@dataclass(frozen=True, slots=True)
class RunPlan:
    """Resolved execution plan for one suite and one run mode.

    Example:
        >>> RunPlan.__name__
        'RunPlan'
    """

    mode: RunMode
    suite_id: str
    suite_version: str
    entries: tuple[RunEntry, ...]
    planned_entries: int
    guardrails: Guardrails = field(default_factory=Guardrails)
    overrides: dict[str, Any] = field(default_factory=dict)

    @property
    def selected_case_ids(self) -> tuple[str, ...]:
        """Return ordered unique case IDs represented by the plan."""
        return tuple(dict.fromkeys(entry.case_id for entry in self.entries))

    @property
    def models(self) -> tuple[str, ...]:
        """Return ordered unique live model IDs."""
        return tuple(
            dict.fromkeys(entry.model for entry in self.entries if entry.model)
        )

    def metadata(self) -> dict[str, object]:
        """Return plan-level metadata suitable for Inspect."""
        return {
            "execution_mode": self.mode,
            "suite_id": self.suite_id,
            "suite_version": self.suite_version,
            "selected_case_ids": list(self.selected_case_ids),
            "selected_model_ids": list(self.models),
            "planned_entries": self.planned_entries,
            "effective_generation_defaults": self.overrides,
            "guardrails": self.guardrails.as_dict(),
            "deterministic_output_policy": "format_valid_v1"
            if self.mode == "check"
            else None,
        }


# ``EvalRun`` is the public name used by the data model; the resolved run
# object is represented by the same immutable plan in this implementation.
EvalRun = RunPlan


def _effective_config(
    item: ValidatedCase,
    format_name: str,
    model: str | None,
    overrides: dict[str, Any],
) -> EffectiveGenerationConfig:
    """Resolve case, fixture, and CLI values with explicit precedence."""
    case = item.case
    fixture = item.fixture

    def value(key: str, default: Any) -> Any:
        if key in overrides and overrides[key] is not None:
            return overrides[key]
        return default

    return EffectiveGenerationConfig(
        format=str(value("format", format_name)),
        history_depth=int(
            value(
                "history_depth",
                case.history_depth
                if case.history_depth is not None
                else DEFAULTS["history_depth"],
            )
        ),
        include_branch=bool(value("include_branch", case.include_branch)),
        hint=value("hint", case.user_hint),
        repository_instructions=value(
            "repository_instructions", fixture.repository_instructions
        ),
        max_chars=value("max_chars", case.max_chars),
        model=model,
        temperature=float(value("temperature", DEFAULTS["temperature"])),
        max_tokens=int(value("max_tokens", DEFAULTS["max_tokens"])),
        max_diff_bytes=int(value("max_diff_bytes", DEFAULTS["max_diff_bytes"])),
        timeout=int(value("timeout", DEFAULTS["timeout"])),
    )


def _entry_id(case_id: str, format_name: str, model: str | None) -> str:
    """Build a stable, filesystem-safe identity for one matrix cell."""
    candidate = model or "deterministic-check"
    return f"{case_id}:{format_name}:{candidate}"


def build_run_plan(
    validated: ValidatedSuite,
    *,
    mode: RunMode,
    models: tuple[str, ...] = (),
    formats: tuple[str, ...] = (),
    overrides: dict[str, Any] | None = None,
    guardrails: Guardrails | None = None,
) -> RunPlan:
    """Expand a validated suite into deterministic case/config entries.

    Args:
        validated: The spec-009 validated suite boundary.
        mode: ``check`` for deterministic output or ``live`` for providers.
        models: Live model IDs. Check mode forbids them.
        formats: Optional format filter/override.
        overrides: CLI-level generation overrides.
        guardrails: Resource limits for live execution.

    Raises:
        RunPlanError: If validation, selection, or guardrails are invalid.

    Example:
        >>> build_run_plan(validated, mode="check")  # doctest: +SKIP
        RunPlan(...)
    """
    if mode not in {"check", "live"}:
        raise RunPlanError("mode must be either 'check' or 'live'")
    if validated.suite is None or validated.report.status != "passed":
        details = "; ".join(issue.render() for issue in validated.report.errors)
        raise RunPlanError(f"suite validation failed: {details or 'unknown error'}")
    if not validated.cases:
        raise RunPlanError("no matching cases were selected")
    if mode == "check" and models:
        raise RunPlanError("--model is only valid with --mode live")
    if mode == "live" and not models:
        raise RunPlanError("--model is required with --mode live")

    limits = guardrails or Guardrails()
    if any(
        value is not None
        for value in (limits.max_tokens, limits.max_cost, limits.time_limit)
    ):
        raise RunPlanError(
            "token, cost, and time limits are unsupported by the direct gmuse "
            "provider path; use --limit-samples and --max-tokens instead"
        )
    if limits.concurrency not in (None, 1):
        raise RunPlanError("concurrency must be 1: fixture execution changes directory")
    if mode == "live" and not limits.configured():
        raise RunPlanError(
            "live evals require an explicit --limit-samples guardrail greater than zero"
        )
    resolved_overrides = dict(overrides or {})
    entries: list[RunEntry] = []
    selected_models = models or (None,)
    for item in validated.cases:
        case_formats = formats or tuple(item.case.formats)
        for format_name in case_formats:
            if format_name not in item.case.formats:
                raise RunPlanError(
                    f"format '{format_name}' is not supported by case '{item.case.id}'"
                )
            for model in selected_models:
                candidate_kind = (
                    "deterministic_check" if mode == "check" else "live_model"
                )
                generation = _effective_config(
                    item, format_name, model, resolved_overrides
                )
                entries.append(
                    RunEntry(
                        entry_id=_entry_id(item.case.id, format_name, model),
                        validated_case=item,
                        generation=generation,
                        candidate_kind=candidate_kind,
                    )
                )

    if not entries:
        raise RunPlanError("no matching cases or formats were selected")
    planned_entries = len(entries)
    if limits.max_samples is not None:
        if limits.max_samples <= 0:
            raise RunPlanError("sample limit must be greater than zero")
        entries = entries[: limits.max_samples]
    return RunPlan(
        mode=mode,
        suite_id=validated.suite.id,
        suite_version=validated.suite.version,
        entries=tuple(entries),
        planned_entries=planned_entries,
        guardrails=limits,
        overrides=resolved_overrides,
    )


__all__ = [
    "EffectiveGenerationConfig",
    "EvalRun",
    "Guardrails",
    "RunEntry",
    "RunMode",
    "RunPlan",
    "RunPlanError",
    "build_run_plan",
]
