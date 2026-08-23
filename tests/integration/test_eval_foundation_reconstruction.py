"""Integration coverage for deterministic temporary Git reconstruction."""

import subprocess
from pathlib import Path

import pytest

from gmuse.git import get_commit_history
from tools.evals.gmuse_evals.git_reconstruct import (
    ReconstructionError,
    reconstruct_fixture,
)
from tools.evals.gmuse_evals.models import (
    EvalFixture,
    FixtureFile,
    FixtureHistoryCommit,
    FixtureProvenance,
)


PATCH = """diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 before
+after
"""


def fixture(**overrides: object) -> EvalFixture:
    values: dict[str, object] = {
        "schema_version": "1.0",
        "id": "reconstruction",
        "revision": 1,
        "origin": "synthetic",
        "provenance": FixtureProvenance(
            origin="synthetic", synthetic_notes="test-only content"
        ),
        "ecosystem": "text",
        "change_type": "docs",
        "safety_tags": [],
        "injection_tags": [],
        "base_files": [FixtureFile(path="README.md", content="before\n")],
        "patch": PATCH,
        "expected_staged_diff_sha256": "0" * 64,
        "expected_files_changed": ["README.md"],
        "history": [FixtureHistoryCommit(subject="Establish docs")],
        "branch_name": "feature/reconstruction",
        "repository_instructions": "Prefer concise documentation.",
        "selection_rationale": "Exercises temporary repository setup.",
    }
    values.update(overrides)
    return EvalFixture.model_validate(values)


def test_reconstruction_is_deterministic_and_uses_production_diff(
    tmp_path: Path,
) -> None:
    del tmp_path  # The helper owns its isolated temporary repository.
    first = fixture()
    with reconstruct_fixture(first) as repository:
        first_hash = repository.staged_diff.hash
        assert repository.staged_diff.files_changed == ["README.md"]
        assert (repository.path / ".gmuse").read_text(encoding="utf-8") == (
            "Prefer concise documentation."
        )
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repository.path,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert branch == "feature/reconstruction"
        history = subprocess.run(
            ["git", "log", "--format=%s"],
            cwd=repository.path,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        assert "Establish docs" in history

    with reconstruct_fixture(first) as repository:
        assert repository.staged_diff.hash == first_hash


def test_reconstruction_preserves_executable_base_file_mode() -> None:
    executable = fixture(
        id="executable",
        base_files=[
            FixtureFile(path="script.sh", content="#!/bin/sh\n", executable=False)
        ],
        patch="""diff --git a/script.sh b/script.sh
old mode 100644
new mode 100755
""",
        expected_files_changed=["script.sh"],
    )

    with reconstruct_fixture(executable) as repository:
        mode = (repository.path / "script.sh").stat().st_mode
        assert mode & 0o111


def test_reconstruction_reports_patch_failures() -> None:
    broken = fixture(
        id="broken",
        patch="not a patch",
        expected_files_changed=[],
    )

    with pytest.raises(ReconstructionError, match="patch"):
        with reconstruct_fixture(broken):
            pass


def test_reconstruction_isolated_from_digest_affecting_global_git_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    unicode_patch = """diff --git a/docs/café.md b/docs/café.md
--- a/docs/café.md
+++ b/docs/café.md
@@ -1,5 +1,7 @@
 line one
 line two
 line three
 line four
 line five
+line six
+line seven
"""
    isolated = fixture(
        id="global-config",
        base_files=[
            FixtureFile(
                path="docs/café.md",
                content="line one\nline two\nline three\nline four\nline five\n",
            )
        ],
        patch=unicode_patch,
    )
    global_config = tmp_path / "gitconfig"
    global_config.write_text(
        """[diff]
    noprefix = true
    mnemonicPrefix = true
    context = 1
    algorithm = patience
    external = false
[color]
    ui = always
[core]
    quotePath = false
""",
        encoding="utf-8",
    )

    with reconstruct_fixture(isolated) as clean:
        expected = (
            clean.staged_diff.raw_diff,
            clean.staged_diff.files_changed,
            clean.staged_diff.hash,
        )

    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    monkeypatch.setenv("GIT_EXTERNAL_DIFF", "false")
    with reconstruct_fixture(isolated) as configured:
        observed = (
            configured.staged_diff.raw_diff,
            configured.staged_diff.files_changed,
            configured.staged_diff.hash,
        )

    assert observed == expected


def test_reconstruction_history_matches_declared_newest_first_order() -> None:
    history = [
        FixtureHistoryCommit(subject="docs: newest"),
        FixtureHistoryCommit(subject="docs: middle"),
        FixtureHistoryCommit(subject="docs: oldest"),
    ]
    historical = fixture(id="history-order", history=history)

    with reconstruct_fixture(historical) as repository:
        observed = get_commit_history(depth=3, path=repository.path)

    assert [commit.message for commit in observed.commits] == [
        item.subject for item in history
    ]
    assert all(
        commit.message != "fixture: establish base" for commit in observed.commits
    )
