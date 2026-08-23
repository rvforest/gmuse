"""Temporary TOML asset flows for origin-aware validation."""

from pathlib import Path

from tools.evals.gmuse_evals.load import load_assets
from tools.evals.gmuse_evals.validate import validate_assets


def _write_common_assets(root: Path, provenance: str) -> None:
    for directory in ("fixtures", "rubrics", "cases", "suites"):
        (root / directory).mkdir()
    provenance_note = (
        f'{provenance}_notes = "temporary notes"' if provenance == "synthetic" else ""
    )
    (root / "fixtures" / "fixture.toml").write_text(
        f'''schema_version = "1.0"
id = "fixture"
revision = 1
origin = "{provenance}"
ecosystem = "python"
change_type = "docs"
safety_tags = []
injection_tags = []
patch = ""
expected_staged_diff_sha256 = "{"0" * 64}"
expected_files_changed = []
history = []
selection_rationale = "temporary provenance test"

[[base_files]]
path = "README.md"
content = "before\\n"

[provenance]
origin = "{provenance}"
{provenance_note}
''',
        encoding="utf-8",
    )
    (root / "rubrics" / "rubric.toml").write_text(
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
    (root / "cases" / "case.toml").write_text(
        """schema_version = "1.0"
id = "case"
revision = 1
fixture_id = "fixture"
rubric_id = "rubric"
formats = ["freeform"]
history_depth = 0
include_branch = false
max_chars = 72
tags = []
""",
        encoding="utf-8",
    )
    (root / "suites" / "custom.toml").write_text(
        """schema_version = "1.0"
id = "custom"
version = "1.0"
suite_kind = "custom"
case_ids = ["case"]

[coverage_policy]
required_dimensions = []
advisory_dimensions = []
minimum_case_counts = {}
""",
        encoding="utf-8",
    )


def test_valid_synthetic_toml_flows_through_loader_and_validator(
    tmp_path: Path,
) -> None:
    _write_common_assets(tmp_path, "synthetic")

    result = validate_assets(load_assets(tmp_path), "custom", reconstruct=False)

    assert result.report.status == "passed"


def test_invalid_origin_provenance_flows_to_structured_errors(tmp_path: Path) -> None:
    _write_common_assets(tmp_path, "real")

    result = validate_assets(load_assets(tmp_path), "custom", reconstruct=False)

    assert result.report.status == "failed"
    assert any(issue.code == "missing_provenance" for issue in result.report.errors)


def test_complete_real_provenance_document_flows_through_loader_and_validator(
    tmp_path: Path,
) -> None:
    _write_common_assets(tmp_path, "real")
    fixture_path = tmp_path / "fixtures" / "fixture.toml"
    fixture_path.write_text(
        fixture_path.read_text(encoding="utf-8")
        + """
source_repository_url = "https://github.com/example/project"
source_owner_repo = "example/project"
source_commit_sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
source_commit_url = "https://github.com/example/project/commit/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
source_license_expression = "0BSD"
redistribution_review = "metadata_only"
original_commit_message = "docs: update guide"
imported_at = 2026-01-01T00:00:00Z
""",
        encoding="utf-8",
    )

    result = validate_assets(load_assets(tmp_path), "custom", reconstruct=False)

    assert result.report.status == "passed"


def test_invalid_real_provenance_url_flows_to_structured_error(
    tmp_path: Path,
) -> None:
    _write_common_assets(tmp_path, "real")
    fixture_path = tmp_path / "fixtures" / "fixture.toml"
    fixture_path.write_text(
        fixture_path.read_text(encoding="utf-8")
        + """
source_repository_url = "example.com/project"
source_owner_repo = "example/project"
source_commit_sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
source_commit_url = "https://github.com/example/project/commit/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
source_license_expression = "Python-2.0"
redistribution_review = "metadata_only"
original_commit_message = "docs: update guide"
imported_at = 2026-01-01T00:00:00Z
""",
        encoding="utf-8",
    )

    result = validate_assets(load_assets(tmp_path), "custom", reconstruct=False)

    assert any(issue.code == "invalid_source_url" for issue in result.report.errors)
