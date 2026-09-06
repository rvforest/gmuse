"""Contract tests for the maintainer-only validation CLI."""

from pathlib import Path

from click import unstyle
from typer.testing import CliRunner

from tools.evals.gmuse_evals.cli import app


def test_cli_exposes_offline_validation_options() -> None:
    result = CliRunner().invoke(app, ["validate", "--help"])
    output = unstyle(result.stdout)

    assert result.exit_code == 0
    assert "--suite" in output
    assert "--evals-dir" in output
    assert "--strict-composition" in output
    assert "--strict-balance" not in output


def test_cli_renders_human_readable_composition_only() -> None:
    result = CliRunner().invoke(app, ["validate", "--suite", "smoke"])

    assert result.exit_code == 0
    assert "Coverage:" not in result.stdout
    assert "Cases: 2" in result.stdout
    assert "Fixtures: 2" in result.stdout
    assert "Warnings: 0" in result.stdout
    assert "Suite composition" in result.stdout
    assert "- Documentation: 1 case" in result.stdout
    assert "- Direct instruction in code comment: 1 case" in result.stdout


def test_cli_reports_missing_evals_with_nonzero_exit(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["validate", "--evals-dir", str(tmp_path)])

    assert result.exit_code != 0
    assert "fixtures" in result.stdout


def test_cli_strict_composition_promotes_advisory_goal(tmp_path: Path) -> None:
    import shutil

    evals_dir = tmp_path / "evals"
    shutil.copytree("evals", evals_dir)
    core_path = evals_dir / "suites" / "core.toml"
    core_path.write_text(
        core_path.read_text(encoding="utf-8").replace(
            '''selector = "case.format"
value = "gitmoji"
minimum_cases = 1
severity = "advisory"''',
            '''selector = "case.format"
value = "gitmoji"
minimum_cases = 2
severity = "advisory"''',
        ),
        encoding="utf-8",
    )

    advisory = CliRunner().invoke(
        app, ["validate", "--suite", "core", "--evals-dir", str(evals_dir)]
    )
    strict = CliRunner().invoke(
        app,
        [
            "validate",
            "--suite",
            "core",
            "--evals-dir",
            str(evals_dir),
            "--strict-composition",
        ],
    )

    assert advisory.exit_code == 0
    assert "Warnings: 1" in advisory.stdout
    assert strict.exit_code != 0


def test_cli_ignores_schema_invalid_assets_outside_selected_suite_graph(
    tmp_path: Path,
) -> None:
    import shutil

    evals_dir = tmp_path / "evals"
    shutil.copytree("evals", evals_dir)
    (evals_dir / "fixtures" / "unreferenced-invalid.toml").write_text(
        'schema_version = "999.0"\nid = "unreferenced-invalid"\n',
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app, ["validate", "--suite", "smoke", "--evals-dir", str(evals_dir)]
    )

    assert result.exit_code == 0

    case_path = evals_dir / "cases" / "docs-history.toml"
    case_path.write_text(
        case_path.read_text(encoding="utf-8").replace(
            'fixture_id = "synthetic-docs-history"',
            'fixture_id = "unreferenced-invalid"',
        ),
        encoding="utf-8",
    )
    referenced = CliRunner().invoke(
        app, ["validate", "--suite", "smoke", "--evals-dir", str(evals_dir)]
    )

    assert referenced.exit_code != 0
    assert "unreferenced-invalid" in referenced.stdout
