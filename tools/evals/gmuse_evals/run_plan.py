"""Run-plan construction and configuration resolution for maintainer evals."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from gmuse.config import DEFAULTS

from .models import EvalCase, EvalFixture
from .results import ResolvedCase, SuiteValidationResult

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
    """Run selection limits checked by :func:`build_run_plan`.

    Attributes:
        max_samples: Positive entry cap required for live plans. The plan
            builder keeps the first entries up to this cap; the CLI rejects
            live matrices whose full size exceeds the cap before execution.
        max_tokens: Unsupported run-wide token limit; any value is rejected.
            Per-response token limits belong in EffectiveGenerationConfig.
        max_cost: Unsupported run-wide cost limit; any value is rejected.
        time_limit: Unsupported run-wide time limit; any value is rejected.
        concurrency: None or 1. Other values are rejected because fixture
            execution changes the process working directory.

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
        """Return whether a positive sample cap is configured.

        Other limit fields are validated separately by :func:`build_run_plan`.
        """
        return self.max_samples is not None and self.max_samples > 0


@dataclass(frozen=True, slots=True)
class EffectiveGenerationConfig:
    """Generation settings resolved for one case/format/model entry.

    Attributes:
        format: Message format supported by the source case.
        history_depth: Number of fixture history commits to include as context.
        include_branch: Whether to include sanitized fixture branch context.
        hint: Optional user guidance included in the prompt.
        repository_instructions: Optional .gmuse file content for the fixture.
        max_chars: Optional generated-message character limit.
        model: Provider model ID, or None for deterministic check entries.
        temperature: Provider sampling temperature.
        max_tokens: Per-response output token limit, not a run-wide budget.
        max_diff_bytes: Staged-diff byte limit before production truncation.
        timeout: Provider request timeout in seconds.
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

    Attributes:
        entry_id: Identity composed from case ID, format, and model, using
            ``deterministic-check`` in place of a model for check entries.
        resolved_case: Validated case and its resolved fixture, profile, and
            rubric assets.
        generation: Effective settings used for this entry's generation call.
        candidate_kind: ``deterministic_check`` for offline output or
            ``live_model`` for provider-generated output.
    """

    entry_id: str
    resolved_case: ResolvedCase
    generation: EffectiveGenerationConfig
    candidate_kind: Literal["deterministic_check", "live_model"]

    @property
    def case(self) -> EvalCase:
        """Return the source case configuration."""
        return self.resolved_case.case

    @property
    def case_id(self) -> str:
        """Return the stable case ID."""
        return self.case.id

    @property
    def fixture(self) -> EvalFixture:
        """Return the resolved fixture."""
        return self.resolved_case.fixture

    @property
    def model(self) -> str | None:
        """Return the selected model, if this is a live entry."""
        return self.generation.model


@dataclass(frozen=True, slots=True)
class RunPlan:
    """Resolved execution plan for one suite and one run mode.

    Attributes:
        mode: ``check`` for deterministic output or ``live`` for provider calls.
        suite_id: Source suite identifier.
        suite_version: Source suite revision as a string.
        entries: Selected entries after applying the sample cap, ordered by
            validated case, format, then model.
        planned_entries: Full matrix size before applying the sample cap;
            may exceed the number of selected entries.
        guardrails: Limits used to validate and cap the plan.
        overrides: Caller-provided generation overrides. Non-None values take
            precedence over case or fixture settings and production defaults.
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
    item: ResolvedCase,
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
    validated: SuiteValidationResult,
    *,
    mode: RunMode,
    models: tuple[str, ...] = (),
    formats: tuple[str, ...] = (),
    overrides: dict[str, Any] | None = None,
    guardrails: Guardrails | None = None,
) -> RunPlan:
    """Expand a validated suite into ordered case/format/model entries.

    This function only plans execution and makes no provider calls. It keeps
    the first ``guardrails.max_samples`` entries when a cap is supplied, while
    ``planned_entries`` retains the full matrix size. The CLI separately
    rejects live matrices exceeding the cap rather than running a subset.

    Args:
        validated: The spec-009 suite validation result.
        mode: ``check`` for deterministic output or ``live`` for providers.
        models: Live model IDs. Check mode forbids them.
        formats: Formats to use for every selected case, in the given order.
            Each format must be supported by every case. Empty uses each
            case's declared formats.
        overrides: Non-None generation overrides take precedence over case
            settings, fixture instructions, and production defaults.
        guardrails: Entry cap and supported concurrency setting. Live mode
            requires a positive sample cap; run-wide token, cost, and time
            limits are rejected in both modes.

    Returns:
        A plan ordered by validated case, format, then model, with selected
        entries capped and the full matrix size retained in ``planned_entries``.

    Raises:
        RunPlanError: If validation, selection, or guardrails are invalid.

    Example:
        >>> from .validate import validate_suite
        >>> validated = validate_suite("evals", "smoke")
        >>> plan = build_run_plan(
        ...     validated, mode="check", guardrails=Guardrails(max_samples=1)
        ... )
        >>> len(plan.entries)
        1
        >>> plan.planned_entries > len(plan.entries)
        True
    """
    if mode not in {"check", "live"}:
        raise RunPlanError("mode must be either 'check' or 'live'")
    if validated.suite is None or validated.report.status != "passed":
        details = "; ".join(issue.render() for issue in validated.report.errors)
        raise RunPlanError(f"suite validation failed: {details or 'unknown error'}")
    if not validated.resolved_cases:
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
    for item in validated.resolved_cases:
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
                        resolved_case=item,
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
        suite_version=str(validated.suite.revision),
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
