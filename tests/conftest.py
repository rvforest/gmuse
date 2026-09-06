from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture(autouse=True)
def _isolate_gmuse_global_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> Iterator[None]:
    """Isolate tests from user machine configuration and environment.

    The CLI loads global config from the XDG location (e.g., ~/.config/gmuse/config.toml)
    and also supports GMUSE_* environment variables. If a developer has these set,
    integration/unit tests can become non-deterministic.

    This fixture:
    - redirects XDG_CONFIG_HOME to a per-test temp directory
    - clears any GMUSE_* env vars (tests can still set them explicitly)
    - clears common provider API key env vars to avoid accidental provider detection
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    for key in list(os.environ.keys()):
        if key.startswith("GMUSE_"):
            monkeypatch.delenv(key, raising=False)

    for key in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    yield


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository for integration tests."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()

    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path


@pytest.fixture
def evals_dir(tmp_path: Path) -> Path:
    """Return a temporary root containing every evaluator asset catalog.

    The profile catalog is intentionally included alongside fixtures, rubrics,
    cases, and suites so tests exercise the complete selected asset graph.
    """
    root = tmp_path / "evals"
    for directory in (
        "fixtures",
        "scoring_profiles",
        "rubrics",
        "cases",
        "suites",
    ):
        (root / directory).mkdir(parents=True)
    return root


@pytest.fixture
def eval_asset_dirs(evals_dir: Path) -> dict[str, Path]:
    """Return all temporary evaluator catalog paths keyed by asset kind."""
    return {
        directory: evals_dir / directory
        for directory in (
            "fixtures",
            "scoring_profiles",
            "rubrics",
            "cases",
            "suites",
        )
    }
