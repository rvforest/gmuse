"""Typer presentation layer for maintainer eval validation."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

import typer

from .load import EvalLoadError
from .models import SuiteComposition, ValidationIssue
from .logs import LogLocationError, summarize_results
from .inspect_runner import run_inspect_plan
from .run_plan import Guardrails, RunPlanError, build_run_plan
from .validate import validate_suite

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Validate offline gmuse evaluation fixtures and suites.",
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
    yes: bool = typer.Option(
        False, "--yes", help="Acknowledge the displayed live plan."
    ),
    preserve_debug: bool = typer.Option(False, "--preserve-debug"),
    strict_composition: bool = typer.Option(False, "--strict-composition"),
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

    _warn_on_unpinned_inputs(evals_dir)
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
