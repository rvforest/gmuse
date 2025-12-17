"""Integration tests for gmuse completions-run command."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestCompletionsRunIntegration:
    """Integration tests for the completions-run runtime helper."""

    def test_completions_run_help(self) -> None:
        """gmuse completions-run --help should display help text."""
        result = subprocess.run(
            [sys.executable, "-m", "gmuse.cli.main", "completions-run", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--shell" in result.stdout
        assert "--for" in result.stdout
        assert "--hint" in result.stdout
        assert "--timeout" in result.stdout

    def test_completions_run_output_is_valid_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """completions-run output should always be valid JSON."""
        # Create a non-git directory to trigger an error
        monkeypatch.chdir(tmp_path)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "gmuse.cli.main",
                "completions-run",
                "--shell",
                "zsh",
                "--for",
                "git commit -m",
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        # Output should be valid JSON regardless of success/failure
        assert result.stdout.strip(), "Output should not be empty"
        output = json.loads(result.stdout)

        # Should have required fields
        assert "suggestion" in output
        assert "status" in output
        assert "metadata" in output

    def test_completions_run_no_staged_changes_in_git_repo(
        self, tmp_path: Path
    ) -> None:
        """completions-run in git repo without staged changes returns correct status."""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "gmuse.cli.main",
                "completions-run",
                "--shell",
                "zsh",
                "--for",
                "git commit -m",
            ],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        output = json.loads(result.stdout)

        assert output["status"] == "no_staged_changes"
        assert output["suggestion"] == ""

    def test_completions_zsh_command(self) -> None:
        """gmuse completions zsh should emit the completion script."""
        result = subprocess.run(
            [sys.executable, "-m", "gmuse.cli.main", "completions", "zsh"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "#compdef git" in result.stdout
        assert "_gmuse_git_commit_message" in result.stdout
        assert "gmuse completions-run" in result.stdout

    def test_completions_help(self) -> None:
        """gmuse completions --help should show subcommands."""
        result = subprocess.run(
            [sys.executable, "-m", "gmuse.cli.main", "completions", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "zsh" in result.stdout
