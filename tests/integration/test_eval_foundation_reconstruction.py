"""Integration coverage for deterministic temporary Git reconstruction."""

import subprocess
from pathlib import Path

import pytest

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


def test_reconstruction_is_deterministic_and_uses_production_diff(tmp_path: Path) -> None:
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
        base_files=[FixtureFile(path="script.sh", content="#!/bin/sh\n", executable=False)],
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
