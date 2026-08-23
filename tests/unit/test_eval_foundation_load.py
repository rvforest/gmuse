"""Tests for deterministic eval asset discovery and TOML loading."""

from pathlib import Path

import pytest

from tools.evals.gmuse_evals.load import (
    EvalLoadError,
    discover_asset_files,
    load_assets,
)


FIXTURE = '''
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
'''


def test_asset_discovery_is_sorted_and_kind_scoped(tmp_path: Path) -> None:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    (fixture_dir / "z.toml").write_text(FIXTURE, encoding="utf-8")
    (fixture_dir / "a.toml").write_text(FIXTURE.replace("fixture-one", "fixture-two"), encoding="utf-8")
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
