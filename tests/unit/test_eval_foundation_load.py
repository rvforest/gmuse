"""Tests for deterministic eval asset discovery and TOML loading."""

from pathlib import Path

import pytest

from tools.evals.gmuse_evals.load import (
    EvalLoadError,
    discover_asset_files,
    load_assets,
    load_suite_assets,
)
from tools.evals.gmuse_evals.validate import validate_suite


FIXTURE = """
schema_version = "1.0"
id = "fixture-one"
revision = 1
origin = "synthetic"
ecosystem = "python"
change_type = "docs"
safety_tags = []
injection_tags = []
patch = "diff --git a/README.md b/README.md\\n"
expected_staged_diff_sha256 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
expected_files_changed = ["README.md"]
history = []
selection_rationale = "test"

[provenance]
origin = "synthetic"
synthetic_notes = "test data"

[[base_files]]
path = "README.md"
content = "before\\n"
executable = false
"""


def test_asset_discovery_is_sorted_and_kind_scoped(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    (fixture_dir / "z.toml").write_text(FIXTURE, encoding="utf-8")
    (fixture_dir / "a.toml").write_text(
        FIXTURE.replace("fixture-one", "fixture-two"), encoding="utf-8"
    )
    (fixture_dir / "ignored.txt").write_text("ignored", encoding="utf-8")

    assert [path.name for path in discover_asset_files(tmp_path, "fixtures")] == [
        "a.toml",
        "z.toml",
    ]


def test_loader_reports_duplicate_ids(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    (fixture_dir / "one.toml").write_text(FIXTURE, encoding="utf-8")
    (fixture_dir / "two.toml").write_text(FIXTURE, encoding="utf-8")

    with pytest.raises(EvalLoadError, match="duplicate fixture id 'fixture-one'"):
        load_assets(tmp_path)


def test_loader_reports_malformed_documents(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    (fixture_dir / "broken.toml").write_text("id = [", encoding="utf-8")

    with pytest.raises(EvalLoadError, match="broken.toml"):
        load_assets(tmp_path)


def test_loader_reports_missing_asset_directories(tmp_path: Path) -> None:
    with pytest.raises(EvalLoadError, match="fixtures"):
        load_assets(tmp_path)


def test_loader_rejects_unknown_schema_versions(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    (fixture_dir / "future.toml").write_text(
        FIXTURE.replace('schema_version = "1.0"', 'schema_version = "999.0"'),
        encoding="utf-8",
    )

    with pytest.raises(EvalLoadError, match="schema_version"):
        load_assets(tmp_path)


def _write_suite_graph(root: Path) -> None:
    for directory in ("fixtures", "rubrics", "cases", "suites"):
        (root / directory).mkdir()
    (root / "fixtures" / "selected.toml").write_text(FIXTURE, encoding="utf-8")
    (root / "rubrics" / "selected.toml").write_text(
        """schema_version = "1.0"
id = "rubric-one"
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
    (root / "cases" / "selected.toml").write_text(
        """schema_version = "1.0"
id = "case-one"
revision = 1
fixture_id = "fixture-one"
rubric_id = "rubric-one"
formats = ["freeform"]
history_depth = 0
include_branch = false
tags = []
""",
        encoding="utf-8",
    )
    for suite_id, kind in (("smoke", "smoke"), ("core", "core")):
        (root / "suites" / f"{suite_id}.toml").write_text(
            f'''schema_version = "1.0"
id = "{suite_id}"
version = "1.0"
suite_kind = "{kind}"
case_ids = ["case-one"]

[coverage_policy]
required_dimensions = []
advisory_dimensions = []
minimum_case_counts = {{}}
''',
            encoding="utf-8",
        )


def test_suite_loader_skips_unreferenced_schema_invalid_documents(
    tmp_path: Path,
) -> None:
    _write_suite_graph(tmp_path)
    (tmp_path / "fixtures" / "unreferenced.toml").write_text(
        'schema_version = "999.0"\nid = "unreferenced"\n',
        encoding="utf-8",
    )

    assets, suite = load_suite_assets(tmp_path, "smoke")

    assert suite.id == "smoke"
    assert set(assets.fixtures) == {"fixture-one"}
    assert set(assets.suites) == {"smoke", "core"}


@pytest.mark.parametrize(
    "fixture_text",
    [
        'schema_version = "999.0"\nid = "fixture-one"\n',
        'schema_version = "1.0"\nid = "fixture-one"\n',
    ],
)
def test_suite_loader_validates_referenced_fixture_documents(
    tmp_path: Path, fixture_text: str
) -> None:
    _write_suite_graph(tmp_path)
    (tmp_path / "fixtures" / "selected.toml").write_text(fixture_text, encoding="utf-8")

    with pytest.raises(EvalLoadError, match="fixture-one"):
        load_suite_assets(tmp_path, "smoke")


def test_suite_loader_keeps_duplicate_id_diagnostics_global(tmp_path: Path) -> None:
    _write_suite_graph(tmp_path)
    (tmp_path / "fixtures" / "duplicate.toml").write_text(FIXTURE, encoding="utf-8")

    with pytest.raises(EvalLoadError, match="duplicate fixture id 'fixture-one'"):
        load_suite_assets(tmp_path, "smoke")


def test_suite_validation_aggregates_missing_transitive_references(
    tmp_path: Path,
) -> None:
    _write_suite_graph(tmp_path)
    (tmp_path / "cases" / "missing.toml").write_text(
        """schema_version = "1.0"
id = "case-missing"
revision = 1
fixture_id = "fixture-missing"
rubric_id = "rubric-missing"
formats = ["freeform"]
history_depth = 0
include_branch = false
tags = []
""",
        encoding="utf-8",
    )
    for suite_id in ("smoke", "core"):
        path = tmp_path / "suites" / f"{suite_id}.toml"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                'case_ids = ["case-one"]',
                'case_ids = ["case-one", "case-missing"]',
            ),
            encoding="utf-8",
        )

    result = validate_suite(tmp_path, "smoke")

    assert result.report.status == "failed"
    assert {issue.asset_id for issue in result.report.errors} >= {
        "fixture-missing",
        "rubric-missing",
    }
