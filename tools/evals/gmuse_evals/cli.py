"""Typer presentation layer for maintainer eval validation."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence

import typer

from .load import EvalLoadError
from .models import SuiteComposition, ValidationIssue
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
