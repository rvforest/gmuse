"""Contract tests for the maintainer-only validation CLI."""

from pathlib import Path

from typer.testing import CliRunner

from tools.evals.gmuse_evals.cli import app
from tools.evals.gmuse_evals.models import COVERAGE_DIMENSIONS


def test_cli_exposes_offline_validation_options() -> None:
    result = CliRunner().invoke(app, ["validate", "--help"])

    assert result.exit_code == 0
    assert "--suite" in result.stdout
    assert "--evals-dir" in result.stdout
    assert "--strict-balance" in result.stdout


def test_cli_renders_complete_sorted_coverage() -> None:
    result = CliRunner().invoke(app, ["validate", "--suite", "smoke"])

    assert result.exit_code == 0
    coverage = result.stdout.split("Coverage:\n", 1)[1]
    labels = [
        line.removeprefix("- ").split(":", 1)[0]
        for line in coverage.splitlines()
        if line.startswith("- ")
    ]
    assert labels == list(COVERAGE_DIMENSIONS)
    assert "- format: conventional, freeform, gitmoji" in coverage
    assert "Cases: 2" in result.stdout
    assert "Fixtures: 2" in result.stdout
    assert "Warnings: 0" in result.stdout


def test_cli_reports_missing_evals_with_nonzero_exit(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["validate", "--evals-dir", str(tmp_path)])

    assert result.exit_code != 0
    assert "fixtures" in result.stdout


def test_cli_strict_balance_promotes_advisory_policy_gap(tmp_path: Path) -> None:
    for directory in ("fixtures", "rubrics", "cases", "suites"):
        (tmp_path / directory).mkdir()
    (tmp_path / "fixtures" / "fixture.toml").write_text(
        '''schema_version = "1.0"
id = "fixture"
revision = 1
origin = "synthetic"
ecosystem = "python"
change_type = "docs"
safety_tags = []
injection_tags = []
patch = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 before
+after
"""
expected_staged_diff_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
expected_files_changed = ["README.md"]
history = []
selection_rationale = "cli policy test"

[[base_files]]
path = "README.md"
content = "before\\n"

[provenance]
origin = "synthetic"
synthetic_notes = "test"
''',
        encoding="utf-8",
    )
    (tmp_path / "rubrics" / "rubric.toml").write_text(
        """schema_version = "1.0"
id = "rubric"
version = "1.0"
required_concepts = []
forbidden_concepts = []
allowed_conventional_types = ["docs"]
allowed_scopes = []
example_good = []
example_bad = []
""",
        encoding="utf-8",
    )
    (tmp_path / "cases" / "case.toml").write_text(
        """schema_version = "1.0"
id = "case"
revision = 1
fixture_id = "fixture"
rubric_id = "rubric"
formats = ["freeform"]
history_depth = 0
include_branch = false
tags = []
""",
        encoding="utf-8",
    )
    (tmp_path / "suites" / "custom.toml").write_text(
        """schema_version = "1.0"
id = "custom"
version = "1.0"
suite_kind = "custom"
case_ids = ["case"]

[coverage_policy]
required_dimensions = []
advisory_dimensions = ["format"]
minimum_case_counts = { format = 2 }
""",
        encoding="utf-8",
    )
    from tools.evals.gmuse_evals.git_reconstruct import reconstruct_fixture
    from tools.evals.gmuse_evals.load import load_assets

    loaded = load_assets(tmp_path)
    with reconstruct_fixture(loaded.fixtures["fixture"]) as repository:
        fixture_text = (tmp_path / "fixtures" / "fixture.toml").read_text(
            encoding="utf-8"
        )
        (tmp_path / "fixtures" / "fixture.toml").write_text(
            fixture_text.replace("0" * 64, repository.staged_diff.hash),
            encoding="utf-8",
        )

    advisory = CliRunner().invoke(
        app, ["validate", "--suite", "custom", "--evals-dir", str(tmp_path)]
    )
    strict = CliRunner().invoke(
        app,
        [
            "validate",
            "--suite",
            "custom",
            "--evals-dir",
            str(tmp_path),
            "--strict-balance",
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
