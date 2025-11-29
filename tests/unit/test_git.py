"""Unit tests for gmuse.git module."""

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest

from gmuse.exceptions import NoStagedChangesError, NotAGitRepositoryError
from gmuse.git import (
    CommitHistory,
    CommitRecord,
    RepositoryInstructions,
    StagedDiff,
    get_commit_history,
    get_repo_root,
    get_staged_diff,
    is_git_repository,
    load_repository_instructions,
    truncate_diff,
)


class TestIsGitRepository:
    """Tests for is_git_repository function."""

    def test_is_git_repository_success(self) -> None:
        """Test detecting a valid git repository."""
        mock_result = mock.Mock(returncode=0)
        with mock.patch("subprocess.run", return_value=mock_result):
            assert is_git_repository() is True

    def test_is_git_repository_failure(self) -> None:
        """Test detecting non-git directory."""
        mock_result = mock.Mock(returncode=128)
        with mock.patch("subprocess.run", return_value=mock_result):
            assert is_git_repository() is False

    def test_is_git_repository_timeout(self) -> None:
        """Test handling timeout when checking repository."""
        with mock.patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5)
        ):
            assert is_git_repository() is False

    def test_is_git_repository_git_not_found(self) -> None:
        """Test handling git command not found."""
        with mock.patch("subprocess.run", side_effect=FileNotFoundError()):
            assert is_git_repository() is False


class TestGetRepoRoot:
    """Tests for get_repo_root function."""

    def test_get_repo_root_success(self) -> None:
        """Test getting repository root path."""
        mock_result = mock.Mock(
            returncode=0,
            stdout="/home/user/project\n",
            stderr="",
        )
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run", return_value=mock_result):
                root = get_repo_root()
                assert root == Path("/home/user/project")

    def test_get_repo_root_not_a_repository(self) -> None:
        """Test error when not in a git repository."""
        with mock.patch("gmuse.git.is_git_repository", return_value=False):
            with pytest.raises(NotAGitRepositoryError, match="Not a git repository"):
                get_repo_root()

    def test_get_repo_root_command_fails(self) -> None:
        """Test error when git command fails."""
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "git", stderr="error"),
            ):
                with pytest.raises(
                    NotAGitRepositoryError, match="Failed to get repository root"
                ):
                    get_repo_root()


class TestGetStagedDiff:
    """Tests for get_staged_diff function."""

    def test_get_staged_diff_success(self) -> None:
        """Test extracting staged diff successfully."""
        mock_diff = """diff --git a/file.py b/file.py
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
+new line
 existing line
-removed line
"""
        mock_files = "file.py\n"

        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                # First call: git diff --cached
                # Second call: git diff --cached --name-only
                mock_run.side_effect = [
                    mock.Mock(returncode=0, stdout=mock_diff, stderr=""),
                    mock.Mock(returncode=0, stdout=mock_files, stderr=""),
                ]

                diff = get_staged_diff()

                assert diff.raw_diff == mock_diff
                assert diff.files_changed == ["file.py"]
                assert diff.lines_added == 1
                assert diff.lines_removed == 1
                assert len(diff.hash) == 64  # SHA256 hash
                assert diff.size_bytes > 0
                assert diff.truncated is False

    def test_get_staged_diff_no_changes(self) -> None:
        """Test error when no staged changes exist."""
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch(
                "subprocess.run",
                return_value=mock.Mock(returncode=0, stdout="", stderr=""),
            ):
                with pytest.raises(
                    NoStagedChangesError, match="No staged changes found"
                ):
                    get_staged_diff()

    def test_get_staged_diff_not_a_repository(self) -> None:
        """Test error when not in a git repository."""
        with mock.patch("gmuse.git.is_git_repository", return_value=False):
            with pytest.raises(NotAGitRepositoryError):
                get_staged_diff()


class TestGetCommitHistory:
    """Tests for get_commit_history function."""

    def test_get_commit_history_success(self) -> None:
        """Test fetching commit history successfully."""
        mock_log = """abc123|John Doe|2025-11-28T10:00:00+00:00|feat: add feature
def456|Jane Smith|2025-11-27T09:00:00+00:00|fix: fix bug
"""
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("gmuse.git.get_repo_root", return_value=Path("/repo")):
                with mock.patch(
                    "subprocess.run",
                    return_value=mock.Mock(returncode=0, stdout=mock_log, stderr=""),
                ):
                    history = get_commit_history(depth=5)

                    assert len(history.commits) == 2
                    assert history.depth == 5
                    assert history.repository_path == "/repo"

                    assert history.commits[0].hash == "abc123"
                    assert history.commits[0].author == "John Doe"
                    assert history.commits[0].message == "feat: add feature"

    def test_get_commit_history_no_commits(self) -> None:
        """Test handling repository with no commits."""
        error = subprocess.CalledProcessError(
            128, "git", stderr="does not have any commits yet"
        )
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("gmuse.git.get_repo_root", return_value=Path("/repo")):
                with mock.patch("subprocess.run", side_effect=error):
                    history = get_commit_history()

                    assert len(history.commits) == 0
                    assert history.depth == 5

    def test_get_commit_history_malformed_line(self) -> None:
        """Test handling malformed commit lines."""
        mock_log = "abc123|John Doe|invalid_format\n"
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("gmuse.git.get_repo_root", return_value=Path("/repo")):
                with mock.patch(
                    "subprocess.run",
                    return_value=mock.Mock(returncode=0, stdout=mock_log, stderr=""),
                ):
                    history = get_commit_history()
                    assert len(history.commits) == 0  # Malformed line skipped


class TestTruncateDiff:
    """Tests for truncate_diff function."""

    def test_truncate_diff_no_truncation_needed(self) -> None:
        """Test that small diffs are not truncated."""
        diff = StagedDiff(
            raw_diff="small diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc123",
            size_bytes=10,
            truncated=False,
        )

        result = truncate_diff(diff, max_bytes=1000)
        assert result == diff
        assert result.truncated is False

    def test_truncate_diff_large_diff(self) -> None:
        """Test truncating large diff."""
        large_content = "line\n" * 10000
        diff = StagedDiff(
            raw_diff=large_content,
            files_changed=["file.py"],
            lines_added=10000,
            lines_removed=0,
            hash="abc123",
            size_bytes=len(large_content.encode()),
            truncated=False,
        )

        result = truncate_diff(diff, max_bytes=1000)
        assert result.truncated is True
        assert result.size_bytes < diff.size_bytes
        assert "truncated" in result.raw_diff

    def test_truncate_diff_preserves_headers(self) -> None:
        """Test that file headers are preserved during truncation."""
        diff_content = """diff --git a/file.py b/file.py
--- a/file.py
+++ b/file.py
""" + ("line\n" * 10000)

        diff = StagedDiff(
            raw_diff=diff_content,
            files_changed=["file.py"],
            lines_added=10000,
            lines_removed=0,
            hash="abc123",
            size_bytes=len(diff_content.encode()),
            truncated=False,
        )

        result = truncate_diff(diff, max_bytes=500)
        assert "diff --git" in result.raw_diff
        assert "---" in result.raw_diff
        assert "+++" in result.raw_diff


class TestLoadRepositoryInstructions:
    """Tests for load_repository_instructions function."""

    def test_load_repository_instructions_exists(self) -> None:
        """Test loading .gmuse file when it exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            gmuse_file = repo_path / ".gmuse"
            gmuse_file.write_text("Always use ticket numbers")

            with mock.patch("gmuse.git.get_repo_root", return_value=repo_path):
                instructions = load_repository_instructions()

                assert instructions.exists is True
                assert instructions.content == "Always use ticket numbers"
                assert instructions.file_path == str(gmuse_file)

    def test_load_repository_instructions_not_exists(self) -> None:
        """Test when .gmuse file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)

            with mock.patch("gmuse.git.get_repo_root", return_value=repo_path):
                instructions = load_repository_instructions()

                assert instructions.exists is False
                assert instructions.content == ""

    def test_load_repository_instructions_read_error(self) -> None:
        """Test handling read errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            gmuse_file = repo_path / ".gmuse"
            gmuse_file.write_text("content")
            gmuse_file.chmod(0o000)  # Remove read permissions

            with mock.patch("gmuse.git.get_repo_root", return_value=repo_path):
                try:
                    instructions = load_repository_instructions()
                    # Should handle error gracefully
                    assert instructions.exists is False
                finally:
                    gmuse_file.chmod(0o644)  # Restore permissions for cleanup
