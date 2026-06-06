"""Integration tests for the generate/commit CLI workflow."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest import mock

from typer.testing import CliRunner

from gmuse.cli.main import app

runner = CliRunner()


def _create_history(repo: Path) -> None:
    readme = repo / "README.md"
    readme.write_text("# Test Project\n")
    subprocess.run(
        ["git", "add", "README.md"], cwd=repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def _stage_file(repo: Path, filename: str, content: str) -> None:
    file_path = repo / filename
    file_path.write_text(content)
    subprocess.run(["git", "add", filename], cwd=repo, check=True, capture_output=True)


def test_generate_is_stdout_only(git_repo: Path, monkeypatch) -> None:
    """generate should print only the draft message on success."""
    _create_history(git_repo)
    _stage_file(git_repo, "feature.py", "def hello():\n    return 'hi'\n")
    monkeypatch.chdir(git_repo)

    with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
        mock_client = mock.Mock()
        mock_client.generate.return_value = "feat: add hello"
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["generate"])

    assert result.exit_code == 0
    assert result.stdout == "feat: add hello\n"
    assert result.stderr == ""


def test_msg_warns_but_keeps_stdout_compatible(git_repo: Path, monkeypatch) -> None:
    """msg should preserve stdout output for legacy scripts while warning on stderr."""
    _create_history(git_repo)
    _stage_file(git_repo, "feature.py", "def hello():\n    return 'hi'\n")
    monkeypatch.chdir(git_repo)

    with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
        mock_client = mock.Mock()
        mock_client.generate.return_value = "feat: add hello"
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["msg"])

    assert result.exit_code == 0
    assert result.stdout == "feat: add hello\n"
    assert "deprecated" in result.stderr.lower()


def test_commit_yes_creates_git_commit(git_repo: Path, monkeypatch) -> None:
    """commit --yes should create a real git commit with the generated subject."""
    _create_history(git_repo)
    _stage_file(git_repo, "feature.py", "def hello():\n    return 'hi'\n")
    monkeypatch.chdir(git_repo)

    with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
        mock_client = mock.Mock()
        mock_client.generate.return_value = "feat: add hello"
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["commit", "--yes"])

    assert result.exit_code == 0
    last_subject = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"],
        cwd=git_repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert last_subject == "feat: add hello"
