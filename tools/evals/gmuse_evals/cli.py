"""Typer presentation layer for maintainer eval validation."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Sequence

import typer

from .load import EvalLoadError
from .models import COVERAGE_DIMENSIONS, ValidationIssue
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
