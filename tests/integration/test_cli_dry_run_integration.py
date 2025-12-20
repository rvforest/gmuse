"""Integration tests for gmuse msg --dry-run (T006)."""

import subprocess
from pathlib import Path

import pytest

from gmuse.cli.main import app
from typer.testing import CliRunner


runner: CliRunner = CliRunner()


# -----------------------------------------------------------------------------
# Fixture: Git repo with staged changes
# -----------------------------------------------------------------------------


@pytest.fixture
def git_repo_with_staged_changes(tmp_path: Path) -> Path:
    """Create a temporary git repo with staged changes."""
    repo: Path = tmp_path / "repo"
    repo.mkdir()

    # Initialize repo
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create and stage a file
    (repo / "hello.py").write_text("print('hello')\n")
    subprocess.run(
        ["git", "add", "hello.py"], cwd=repo, check=True, capture_output=True
    )

    return repo


# -----------------------------------------------------------------------------
# Tests for dry-run CLI output layout (T006)
# -----------------------------------------------------------------------------


class TestDryRunIntegration:
    """Integration tests verifying CLI output layout for --dry-run."""

    def test_dry_run_outputs_header_and_prompts(
        self, git_repo_with_staged_changes: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """gmuse msg --dry-run prints MODEL, FORMAT, TRUNCATED, and prompts."""
        monkeypatch.chdir(git_repo_with_staged_changes)

        result = runner.invoke(app, ["msg", "--dry-run"])

        assert result.exit_code == 0, f"Unexpected error: {result.output}"
        assert "MODEL:" in result.output
        assert "FORMAT:" in result.output
        assert "TRUNCATED:" in result.output
        assert "SYSTEM PROMPT:" in result.output
        assert "USER PROMPT:" in result.output

    def test_dry_run_exit_code_zero(
        self, git_repo_with_staged_changes: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """gmuse msg --dry-run should exit with code 0."""
        monkeypatch.chdir(git_repo_with_staged_changes)

        result = runner.invoke(app, ["msg", "--dry-run"])

        assert result.exit_code == 0

    def test_dry_run_with_format_flag(
        self, git_repo_with_staged_changes: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--format flag should be reflected in the header."""
        monkeypatch.chdir(git_repo_with_staged_changes)

        result = runner.invoke(app, ["msg", "--dry-run", "--format", "gitmoji"])

        assert result.exit_code == 0
        assert "FORMAT: gitmoji" in result.output

    def test_dry_run_with_hint_flag(
        self, git_repo_with_staged_changes: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--hint should be passed through and appear in user prompt section."""
        monkeypatch.chdir(git_repo_with_staged_changes)

        result = runner.invoke(app, ["msg", "--dry-run", "--hint", "security fix"])

        assert result.exit_code == 0
        # Hint is embedded by build_prompt in user prompt as "User hint: <hint>"
        assert "User hint: security fix" in result.output


class TestDryRunErrorCases:
    """Integration tests verifying error handling preserves exit codes."""

    def test_dry_run_not_a_git_repo_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """gmuse msg --dry-run in non-git dir should return non-zero exit."""
        not_git: Path = tmp_path / "not_git"
        not_git.mkdir()
        monkeypatch.chdir(not_git)

        result = runner.invoke(app, ["msg", "--dry-run"])

        assert result.exit_code != 0
        assert (
            "not a git repository" in result.output.lower()
            or "error" in result.output.lower()
        )

    def test_dry_run_no_staged_changes_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """gmuse msg --dry-run with no staged changes should return non-zero exit."""
        repo: Path = tmp_path / "empty_repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "t@t.com"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "T"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        monkeypatch.chdir(repo)

        result = runner.invoke(app, ["msg", "--dry-run"])

        assert result.exit_code != 0
        assert "no staged" in result.output.lower() or "stage" in result.output.lower()
