"""Typer presentation layer for maintainer eval validation."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import typer

from gmuse.credentials import infer_provider_from_model

from .inspect_runner import run_inspect_plan
from .inspect_scorers import (
    InspectJudgePlan,
    InspectScoringError,
    JudgeCallLimitExceeded,
    JudgeCallLimitRequired,
    UnsupportedJudgeRunLimits,
    execute_inspect_judge_plan,
    prepare_inspect_judge_plan,
    score_inspect_log,
)
from .judge import JudgeConfiguration
from .load import EvalLoadError
from .logs import LogLocationError, locate_log_dir, summarize_results
from .models import SuiteComposition, ValidationIssue
from .run_plan import Guardrails, RunPlanError, build_run_plan
from .validate import validate_suite

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Validate, run, and score maintainer gmuse evaluations.",
)
validate_app = typer.Typer(add_completion=False, help="Validate an eval suite.")
app.add_typer(validate_app, name="validate")


def _warn_on_unpinned_inputs(evals_dir: Path) -> None:
    """Warn when HEAD may not identify the runner and eval assets on disk."""
    try:
        root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        checkout = Path(root.stdout.strip()).resolve()
        assets = evals_dir.resolve()
        if not assets.is_relative_to(checkout):
            typer.echo(
                "Warning: eval assets are outside the checkout. The project revision "
                "does not identify those assets.",
                err=True,
            )
            return
        status = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--untracked-files=all",
                "--",
                str(assets.relative_to(checkout)),
                "src/gmuse",
                "tools/evals",
                "pyproject.toml",
                "uv.lock",
            ],
            cwd=checkout,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        typer.echo("Warning: could not verify eval checkout provenance.", err=True)
        return
    if status.stdout:
        typer.echo(
            "Warning: eval assets or runner inputs have local changes. The recorded "
            "project revision may be insufficient to reproduce this run.",
            err=True,
        )


def _render_issues(title: str, issues: Sequence[ValidationIssue]) -> None:
    """Render issue objects without coupling validation to Typer."""
    if not issues:
        return
    typer.echo(f"{title}:")
    for issue in issues:
        typer.echo(f"- {issue.render()}")


def _render_composition(composition: SuiteComposition) -> None:
    """Render counted composition without exposing raw asset metadata."""
    if not composition.groups:
        return
    typer.echo("Suite composition")
    for group in composition.groups:
        typer.echo(f"\n{group.name}")
        for entry in group.entries:
            suffix = "case" if entry.case_count == 1 else "cases"
            typer.echo(f"- {entry.label}: {entry.case_count} {suffix}")


@validate_app.callback(invoke_without_command=True)
def validate(
    suite: str = typer.Option("smoke", "--suite", help="Suite identifier to validate."),
    evals_dir: Path = typer.Option(
        Path("evals"), "--evals-dir", help="Root directory containing eval assets."
    ),
    strict_composition: bool = typer.Option(
        False,
        "--strict-composition",
        help="Promote advisory composition-goal shortfalls to failures.",
    ),
) -> None:
    """Validate a suite without model, judge, or network calls.

    The callback stays presentation-only so later runners can call the same
    structured validator directly.

    Args:
        suite: Stable suite identifier.
        evals_dir: Root directory containing eval assets.
        strict_composition: Whether advisory composition-goal shortfalls fail.

    Raises:
        typer.Exit: With status one when loading or validation fails.

    Example:
        Run ``python -m tools.evals.gmuse_evals validate --suite smoke``.
    """
    try:
        result = validate_suite(
            evals_dir,
            suite,
            strict_composition=strict_composition,
        )
    except EvalLoadError as error:
        typer.echo(f"Validated suite: {suite}")
        typer.echo("Status: failed")
        typer.echo(f"\nErrors:\n- {error}")
        raise typer.Exit(code=1) from error

    report = result.report
    typer.echo(f"Validated suite: {report.suite_id}")
    typer.echo(f"Status: {report.status}")
    if report.status == "failed":
        typer.echo()
        _render_issues("Errors", report.errors)
    _render_issues("Warnings", report.warnings)
    typer.echo(
        f"Cases: {len(result.resolved_cases)}\n"
        f"Fixtures: {len({item.fixture.id for item in result.resolved_cases})}\n"
        f"Warnings: {len(report.warnings)}"
    )
    if report.composition_goals:
        typer.echo("\nComposition goals:")
        for goal in report.composition_goals:
            typer.echo(
                f"- {goal.selector}={goal.value}: observed {goal.observed_cases}, "
                f"required {goal.minimum_cases} ({goal.severity}) - {goal.status}"
            )
    typer.echo()
    _render_composition(report.composition)
    if report.status == "failed":
        raise typer.Exit(code=1)


@app.command("run")
def run(
    mode: str = typer.Option(
        ..., "--mode", help="Execution mode: check (offline) or live (provider calls)."
    ),
    suite: str = typer.Option("smoke", "--suite", help="Validated suite identifier."),
    evals_dir: Path = typer.Option(
        Path("evals"), "--evals-dir", help="Root directory containing eval assets."
    ),
    model: list[str] = typer.Option(
        [], "--model", help="Live model identifier; repeat for a model matrix."
    ),
    format: str | None = typer.Option(None, "--format", help="Format override."),
    history_depth: int | None = typer.Option(None, "--history-depth"),
    include_branch: bool | None = typer.Option(
        None, "--include-branch/--no-include-branch"
    ),
    hint: str | None = typer.Option(None, "--hint"),
    repository_instructions: Path | None = typer.Option(
        None, "--repository-instructions"
    ),
    max_chars: int | None = typer.Option(None, "--max-chars"),
    temperature: float | None = typer.Option(None, "--temperature"),
    max_tokens: int | None = typer.Option(None, "--max-tokens"),
    limit_samples: int | None = typer.Option(None, "--limit-samples"),
    limit_tokens: int | None = typer.Option(None, "--limit-tokens"),
    limit_cost: float | None = typer.Option(None, "--limit-cost"),
    limit_time: int | None = typer.Option(None, "--limit-time"),
    concurrency: int | None = typer.Option(None, "--concurrency"),
    log_dir: Path | None = typer.Option(None, "--log-dir"),
    plan_only: bool = typer.Option(
        False,
        "--plan",
        help="Preview a live run without calling providers or writing logs.",
    ),
    yes: bool = typer.Option(False, "--yes", help="Confirm the displayed live plan."),
    show_config: bool = typer.Option(
        False,
        "--show-config",
        help="Show effective settings in check mode; live always shows them.",
    ),
    preserve_debug: bool = typer.Option(False, "--preserve-debug"),
    strict_composition: bool = typer.Option(False, "--strict-composition"),
) -> None:
    """Run a validated suite through the production-path Inspect runner.

    Raises:
        typer.Exit: If preflight or execution fails, or the maintainer declines.

    Example:
        Run ``python -m tools.evals.gmuse_evals run --mode check --suite smoke``.
    """
    if mode not in {"check", "live"}:
        typer.echo("Error: --mode must be one of: check, live.")
        raise typer.Exit(code=2)
    if plan_only and mode != "live":
        typer.echo("Error: --plan is only valid with --mode live.")
        raise typer.Exit(code=2)
    if repository_instructions is not None:
        try:
            instructions = repository_instructions.read_text(encoding="utf-8")
        except OSError as error:
            typer.echo(f"Error: cannot read repository instructions: {error}")
            raise typer.Exit(code=2) from error
    else:
        instructions = None
    overrides = {
        key: value
        for key, value in {
            "format": format,
            "history_depth": history_depth,
            "include_branch": include_branch,
            "hint": hint,
            "repository_instructions": instructions,
            "max_chars": max_chars,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }.items()
        if value is not None
    }
    guardrails = Guardrails(
        max_samples=limit_samples,
        max_tokens=limit_tokens,
        max_cost=limit_cost,
        time_limit=limit_time,
        concurrency=concurrency,
    )
    try:
        validated = validate_suite(
            evals_dir,
            suite,
            strict_composition=strict_composition,
        )
        plan = build_run_plan(
            validated,
            mode=mode,  # type: ignore[arg-type]
            models=tuple(model),
            formats=(format,) if format else (),
            overrides=overrides,
            guardrails=guardrails,
        )
    except (EvalLoadError, RunPlanError) as error:
        typer.echo(f"Error: {error}")
        raise typer.Exit(code=2) from error

    if (
        mode == "live"
        and limit_samples is not None
        and plan.planned_entries > limit_samples
    ):
        typer.echo(
            f"Error: planned samples {plan.planned_entries} exceed --limit-samples {limit_samples}."
        )
        typer.echo("No provider calls were made.")
        raise typer.Exit(code=2)

    live_log_dir = None
    if mode == "live":
        try:
            live_log_dir = locate_log_dir(log_dir, explicit=log_dir is not None)
        except (LogLocationError, OSError, RuntimeError) as error:
            typer.echo(f"Error: {error}")
            raise typer.Exit(code=2) from error

    _warn_on_unpinned_inputs(evals_dir)
    typer.echo(f"Run mode: {mode}")
    typer.echo(f"Suite: {plan.suite_id}")
    if mode == "live":
        typer.echo(f"Suite revision: {plan.suite_version}")
        typer.echo(f"Cases: {len(plan.selected_case_ids)}")
    typer.echo(f"Planned entries: {plan.planned_entries}")
    typer.echo(f"Selected cases: {', '.join(plan.selected_case_ids)}")
    formats = dict.fromkeys(entry.generation.format for entry in plan.entries)
    typer.echo(f"Formats: {', '.join(formats)}")
    if plan.models:
        typer.echo(f"Models: {', '.join(plan.models)}")
    if plan.guardrails.max_samples is not None:
        typer.echo(f"Sample limit: {plan.guardrails.max_samples}")
    if live_log_dir is not None:
        typer.echo("Concurrency: 1")
        typer.echo(f"Inspect log directory: {live_log_dir}")
        confirmation = "plan_only" if plan_only else "--yes" if yes else "interactive"
        typer.echo(f"Confirmation: {confirmation}")
    if show_config or mode == "live":
        for entry in plan.entries:
            typer.echo(f"Entry {entry.entry_id}: {entry.generation.as_dict()}")
    if plan_only:
        typer.echo("Provider calls: 0")
        return
    if mode == "check":
        typer.echo("Candidate kind: deterministic_check")
        typer.echo("Provider calls: 0")
    if mode == "live" and not yes:
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            typer.echo(
                "Error: non-interactive live runs require --yes. "
                "Review the run with --plan before confirming."
            )
            raise typer.Exit(code=2)
        if not typer.confirm("Proceed with live provider calls?", default=False):
            typer.echo("Live eval cancelled. No provider calls were made.")
            raise typer.Exit(code=0)

    try:
        execution = run_inspect_plan(
            plan, log_dir=log_dir, preserve_debug=preserve_debug
        )
    except (OSError, RuntimeError, ValueError) as error:
        typer.echo(f"Error: {error}")
        raise typer.Exit(code=2) from error
    locations = tuple(
        str(getattr(log, "location", ""))
        for log in execution.logs
        if getattr(log, "location", "")
    ) or (str(execution.log_dir),)
    summary = summarize_results(
        list(execution.results),
        planned_entries=plan.planned_entries,
        log_locations=locations,
    )
    typer.echo(f"Inspect log: {', '.join(locations)}")
    typer.echo(f"Completed entries: {summary.completed_entries}")
    typer.echo(f"Validation passed: {summary.validation_passed}")
    typer.echo(f"Validation failed: {summary.validation_failed}")
    typer.echo(f"Operational errors: {summary.operational_errors}")


def _resolve_judge_options(
    judge_model: str,
    *,
    judge_provider: str | None,
    equivalent_models: Sequence[str] | None,
    temperature: float | None,
    max_tokens: int | None,
    timeout: int | None,
) -> tuple[JudgeConfiguration, tuple[tuple[str, str], ...]]:
    """Validate the judge configuration and declared model aliases."""
    model = judge_model.strip()
    provider = judge_provider or infer_provider_from_model(model)
    if not model or not provider:
        raise InspectScoringError(
            "Specify a judge model with a provider prefix or --judge-provider."
        )
    aliases = []
    for identity in equivalent_models or []:
        alias_provider, _, alias_model = identity.partition("/")
        if not alias_provider.strip() or not alias_model.strip():
            raise InspectScoringError(
                "Equivalent candidate models must use provider/model."
            )
        aliases.append((alias_provider.strip(), alias_model.strip()))
    overrides = {
        key: value
        for key, value in (
            ("temperature", temperature),
            ("max_tokens", max_tokens),
            ("timeout", timeout),
        )
        if value is not None
    }
    try:
        configuration = JudgeConfiguration.model_validate(
            {"judge_provider": provider, "judge_model": model, **overrides}
        )
    except ValueError as error:
        raise InspectScoringError(
            "Judge settings require a provider, temperature from 0 to 2, and positive --max-tokens and --timeout."
        ) from error
    return configuration, tuple(aliases)


def _render_judge_plan(plan: InspectJudgePlan) -> None:
    """Display the resolved plan before confirmation or execution."""
    configuration = plan.configuration
    typer.echo(
        f"Judge provider and model: {configuration.judge_provider} / {configuration.judge_model}"
    )
    typer.echo(f"Judge prompt version: {configuration.judge_prompt_version}")
    typer.echo(f"Rubric revisions: {', '.join(plan.rubric_revisions) or 'none'}")
    typer.echo(f"Planned judge calls: {plan.planned_calls}")
    typer.echo(f"Judge call limit: {plan.guardrails.max_samples}")
    typer.echo(f"Judge response token limit: {configuration.max_tokens}")
    typer.echo(f"Judge call timeout: {configuration.timeout}s")
    typer.echo(f"Judge temperature: {configuration.temperature}")
    typer.echo(f"Reused judge results: {plan.reused_count}")
    typer.echo(f"Scored Inspect log destination: {plan.destination}")


def _scoring_error_message(error: InspectScoringError | ImportError) -> str:
    """Add CLI guidance to errors from the scoring API."""
    if isinstance(error, ImportError):
        return "Install the development dependencies to score Inspect logs."
    if isinstance(error, JudgeCallLimitRequired):
        return "Live judging requires an explicit positive --limit-samples."
    if isinstance(error, JudgeCallLimitExceeded):
        return f"Planned judge calls {error.planned_calls} exceed --limit-samples {error.limit}."
    if isinstance(error, UnsupportedJudgeRunLimits):
        return f"{error} Use --limit-samples, --max-tokens, and --timeout."
    return str(error)


@app.command("score")
def score(
    log: Path = typer.Option(..., "--log", help="Source candidate Inspect log."),
    output: Path = typer.Option(..., "--output", help="New scored .eval file."),
    evals_dir: Path = typer.Option(
        Path("evals"), "--evals-dir", help="Root directory containing eval assets."
    ),
    judge_model: str | None = typer.Option(
        None, "--judge-model", help="Enable live scoring with this model."
    ),
    judge_provider: str | None = typer.Option(
        None,
        "--judge-provider",
        help="Provider override when the model does not specify a provider.",
    ),
    limit_samples: int | None = typer.Option(
        None, "--limit-samples", help="Maximum new judge attempts."
    ),
    limit_tokens: int | None = typer.Option(None, "--limit-tokens"),
    limit_cost: float | None = typer.Option(None, "--limit-cost"),
    limit_time: int | None = typer.Option(None, "--limit-time-seconds", "--limit-time"),
    concurrency: int | None = typer.Option(
        None, "--limit-concurrency", "--concurrency"
    ),
    temperature: float | None = typer.Option(None, "--temperature"),
    max_tokens: int | None = typer.Option(
        None, "--max-tokens", help="Token limit for each judge response."
    ),
    timeout: int | None = typer.Option(
        None, "--timeout", help="Timeout in seconds for each judge call."
    ),
    plan_only: bool = typer.Option(
        False, "--plan", help="Show the live scoring plan without judging."
    ),
    yes: bool = typer.Option(
        False, "--yes", help="Confirm the displayed live scoring plan."
    ),
    judge_hard_failures: bool = typer.Option(
        False, "--judge-hard-failures", help="Include hard-gated samples for diagnosis."
    ),
    identity_reason: str | None = typer.Option(
        None,
        "--include-candidate-identity",
        help="Diagnostic reason for showing candidate provider and model to the judge.",
    ),
    equivalent_models: list[str] | None = typer.Option(
        None,
        "--equivalent-candidate-model",
        help="Candidate provider/model to flag as self-judged. Repeat for aliases.",
    ),
    resume: Path | None = typer.Option(
        None, "--resume", help="Previous compatible scored Inspect log."
    ),
) -> None:
    """Apply deterministic checks and optionally judge saved candidate outputs.

    Example:
        Run ``python -m tools.evals.gmuse_evals score --log run.eval --output scored.eval``.
    """
    try:
        if judge_model is None:
            if (
                any(
                    value is not None
                    for value in (
                        judge_provider,
                        limit_samples,
                        limit_tokens,
                        limit_cost,
                        limit_time,
                        concurrency,
                        temperature,
                        max_tokens,
                        timeout,
                        identity_reason,
                        equivalent_models,
                        resume,
                    )
                )
                or plan_only
                or yes
                or judge_hard_failures
            ):
                raise InspectScoringError("Judge options require --judge-model.")
            summary = score_inspect_log(log, output, evals_dir=evals_dir)
        else:
            configuration, aliases = _resolve_judge_options(
                judge_model,
                judge_provider=judge_provider,
                equivalent_models=equivalent_models,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            plan = prepare_inspect_judge_plan(
                log,
                output,
                configuration=configuration,
                guardrails=Guardrails(
                    limit_samples, limit_tokens, limit_cost, limit_time, concurrency
                ),
                evals_dir=evals_dir,
                diagnostic_hard_failures=judge_hard_failures,
                identity_inclusion_reason=identity_reason,
                equivalent_models=aliases,
                resume=resume,
            )
            _render_judge_plan(plan)
            if plan_only:
                typer.echo("Provider calls: 0")
                return
            if not yes:
                if not sys.stdin.isatty():
                    raise InspectScoringError(
                        "Non-interactive live judging requires --yes."
                    )
                if not typer.confirm("Proceed with live judge scoring?", default=False):
                    typer.echo("Judge scoring cancelled. Provider calls: 0")
                    return
            summary = execute_inspect_judge_plan(plan, confirmed=True)
    except (InspectScoringError, ImportError) as error:
        typer.echo(f"Error: {_scoring_error_message(error)}", err=True)
        raise typer.Exit(code=2) from error

    typer.echo(f"Scored Inspect log: {summary.destination}")
    typer.echo(f"Candidate samples: {summary.total}")
    label = "Deterministically scored" if judge_model is None else "Scored"
    typer.echo(f"{label}: {summary.scored}")
    typer.echo(f"Hard failures: {summary.hard_failed}")
    typer.echo(f"Unscored: {summary.unscored}")
    if judge_model is not None:
        typer.echo(f"Judge operational failures: {summary.judge_failures}")
    typer.echo(f"Provider calls: {summary.judge_calls}")
    if summary.interrupted:
        typer.echo(
            "Judge scoring interrupted. Resume from the saved scored log.", err=True
        )
        raise typer.Exit(code=130)
