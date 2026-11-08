"""Typer presentation layer for maintainer eval validation."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import typer

from .load import EvalLoadError
from .models import COVERAGE_DIMENSIONS, ValidationIssue
from .logs import LogLocationError, summarize_results
from .inspect_tasks import run_inspect_plan
from .runner import Guardrails, RunPlanError, build_run_plan
from .validate import validate_suite

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Validate offline gmuse evaluation fixtures and suites.",
)
validate_app = typer.Typer(add_completion=False, help="Validate an eval suite.")
app.add_typer(validate_app, name="validate")


def _render_issues(title: str, issues: Sequence[ValidationIssue]) -> None:
    """Render issue objects without coupling validation to Typer."""
    if not issues:
        return
    typer.echo(f"{title}:")
    for issue in issues:
        typer.echo(f"- {issue.render()}")


@validate_app.callback(invoke_without_command=True)
def validate(
    suite: str = typer.Option("smoke", "--suite", help="Suite identifier to validate."),
    evals_dir: Path = typer.Option(
        Path("evals"), "--evals-dir", help="Root directory containing eval assets."
    ),
    strict_balance: bool = typer.Option(
        False,
        "--strict-balance",
        help="Treat advisory coverage gaps as validation failures.",
    ),
) -> None:
    """Validate a suite without model, judge, or network calls.

    The callback stays presentation-only so later runners can call the same
    structured validator directly.

    Args:
        suite: Stable suite identifier.
        evals_dir: Root directory containing eval assets.
        strict_balance: Whether advisory coverage gaps should fail validation.

    Raises:
        typer.Exit: With status one when loading or validation fails.

    Example:
        Run ``python -m tools.evals.gmuse_evals validate --suite smoke``.
    """
    try:
        result = validate_suite(evals_dir, suite, strict_balance=strict_balance)
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
        f"Cases: {len(result.cases)}\n"
        f"Fixtures: {len({item.fixture.id for item in result.cases})}\n"
        f"Warnings: {len(report.warnings)}"
    )
    typer.echo("Coverage:")
    for dimension in COVERAGE_DIMENSIONS:
        values = report.coverage.dimensions.get(dimension, [])
        typer.echo(f"- {dimension}: {', '.join(sorted(values)) or 'none'}")
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
    yes: bool = typer.Option(
        False, "--yes", help="Acknowledge the displayed live plan."
    ),
    preserve_debug: bool = typer.Option(False, "--preserve-debug"),
    strict_balance: bool = typer.Option(False, "--strict-balance"),
) -> None:
    """Run a validated suite through the production-path Inspect runner."""
    if mode not in {"check", "live"}:
        typer.echo("Error: --mode must be one of: check, live.")
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
        validated = validate_suite(evals_dir, suite, strict_balance=strict_balance)
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

    typer.echo(f"Run mode: {mode}")
    typer.echo(f"Suite: {plan.suite_id}")
    typer.echo(f"Planned entries: {plan.planned_entries}")
    typer.echo(f"Selected cases: {', '.join(plan.selected_case_ids)}")
    if plan.models:
        typer.echo(f"Models: {', '.join(plan.models)}")
    typer.echo(f"Guardrails: {plan.guardrails.as_dict()}")
    for entry in plan.entries:
        typer.echo(f"Entry {entry.entry_id}: {entry.generation.as_dict()}")
    if mode == "check":
        typer.echo("Candidate kind: deterministic_check")
        typer.echo("Provider calls: 0")
    if mode == "live" and not yes:
        if not typer.confirm("Proceed with live provider calls?", default=False):
            typer.echo("Live eval cancelled. No provider calls were made.")
            raise typer.Exit(code=0)

    try:
        execution = run_inspect_plan(
            plan, log_dir=log_dir, preserve_debug=preserve_debug
        )
    except (LogLocationError, RuntimeError, ValueError) as error:
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
