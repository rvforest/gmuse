"""Integration tests for prompt template documentation synchronization.

These tests run the actual documentation build (via nox) to ensure:
- docs build succeeds in a clean environment
- the rendered reference page includes canonical template text
- the docs build fails when template extraction/validation fails
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _run_nox_docs(repo_root: Path, *, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["uv", "run", "nox", "-s", "docs"],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_docs_build_succeeds_and_contains_templates(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]

    result = _run_nox_docs(repo_root)
    assert result.returncode == 0, result.stdout + "\n" + result.stderr

    html_path = repo_root / "docs" / "build" / "html" / "reference" / "prompt-templates.html"
    assert html_path.exists()

    html = html_path.read_text(encoding="utf-8")
    assert "You are an expert commit message generator" in html
    assert "Generate a commit message in natural language" in html
    assert "Conventional Commits" in html


def test_docs_build_fails_on_template_validation_failure(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]

    result = _run_nox_docs(
        repo_root,
        extra_env={"GMUSE_DOCS_FORCE_TEMPLATE_VALIDATION_ERROR": "1"},
    )

    assert result.returncode != 0
    combined = (result.stdout + "\n" + result.stderr).lower()
    assert "prompt template validation failed" in combined
