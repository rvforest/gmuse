"""Unit tests for branch-related functionality in gmuse.git module."""

import subprocess
from unittest import mock

import pytest

from gmuse.exceptions import NotAGitRepositoryError
from gmuse.git import (
    _parse_branch_info,
    _sanitize_branch_name,
    get_current_branch,
)


class TestSanitizeBranchName:
    """Tests for _sanitize_branch_name function."""

    def test_sanitize_lowercase(self) -> None:
        """Test that branch names are converted to lowercase."""
        assert _sanitize_branch_name("Feature/Add-Auth") == "feature/add/auth"

    def test_sanitize_normalize_separators(self) -> None:
        """Test that separators are normalized to forward slash."""
        assert _sanitize_branch_name("feature-add_auth") == "feature/add/auth"
        assert _sanitize_branch_name("feature--add__auth") == "feature/add/auth"

    def test_sanitize_remove_username(self) -> None:
        """Test that username prefixes are removed."""
        assert _sanitize_branch_name("user/feature/add-auth") == "feature/add/auth"
        assert _sanitize_branch_name("username/fix-bug") == "fix/bug"

    def test_sanitize_mask_ticket_ids(self) -> None:
        """Test that ticket IDs are masked."""
        assert (
            _sanitize_branch_name("feature/PROJ-123-add-auth")
            == "feature/ticket-xxx/add/auth"
        )
        assert _sanitize_branch_name("fix/ABC-456-bug") == "fix/ticket-xxx/bug"
        assert _sanitize_branch_name("JIRA-789/update-api") == "ticket-xxx/update/api"

    def test_sanitize_remove_long_hashes(self) -> None:
        """Test that long hex hashes are removed."""
        assert _sanitize_branch_name("feature/abc123456-test") == "feature/test"
        assert _sanitize_branch_name("fix/deadbeef12345678") == "fix"

    def test_sanitize_truncate_long_names(self) -> None:
        """Test that long branch names are truncated."""
        long_name = "feature/" + "x" * 100
        result = _sanitize_branch_name(long_name, max_length=60)
        assert len(result) <= 60
        assert result.startswith("feature")

    def test_sanitize_clean_trailing_separators(self) -> None:
        """Test that trailing separators are removed."""
        assert _sanitize_branch_name("feature/test/") == "feature/test"
        assert _sanitize_branch_name("/feature/test") == "feature/test"

    def test_sanitize_truncation_cleans_mid_segment(self) -> None:
        """Truncation should not leave partial path segments.

        This hits the branch where we truncate inside a multi-segment summary and
        then drop the incomplete tail segment.
        """
        # Many segments so truncation likely cuts in the middle of one.
        branch = "feature/one/two/three/four"
        # With max_length=20: first segment is "feature" (7 chars), leaving 12 for rest.
        # rest[:12] => "one/two/three" contains '/', so the code rsplit()s to "one/two".
        assert _sanitize_branch_name(branch, max_length=20) == "feature/one/two"


class TestParseBranchInfo:
    """Tests for _parse_branch_info function."""

    def test_parse_feature_branch(self) -> None:
        """Test parsing feature branch with type and summary."""
        branch_type, summary = _parse_branch_info("feature/add-authentication")
        assert branch_type == "feature"
        assert summary == "add/authentication"

    def test_parse_fix_branch(self) -> None:
        """Test parsing fix branch."""
        branch_type, summary = _parse_branch_info("fix/PROJ-123-bug-in-api")
        assert branch_type == "fix"
        assert summary == "ticket-xxx/bug/in/api"

    def test_parse_hotfix_branch(self) -> None:
        """Test parsing hotfix branch."""
        branch_type, summary = _parse_branch_info("hotfix/critical-security-issue")
        assert branch_type == "hotfix"
        assert summary == "critical/security/issue"

    def test_parse_feat_alias(self) -> None:
        """Test parsing 'feat' as alias for 'feature'."""
        branch_type, summary = _parse_branch_info("feat/new-feature")
        assert branch_type == "feat"
        assert summary == "new/feature"

    def test_parse_bugfix_alias(self) -> None:
        """Test parsing 'bugfix' as alias for 'fix'."""
        branch_type, summary = _parse_branch_info("bugfix/issue-42")
        assert branch_type == "bugfix"
        assert summary == "issue/42"

    def test_parse_with_hyphen_separator(self) -> None:
        """Test parsing branch with hyphen separator instead of slash."""
        branch_type, summary = _parse_branch_info("feature-add-auth")
        assert branch_type == "feature"
        assert summary == "add/auth"

    def test_parse_without_type(self) -> None:
        """Test parsing branch without recognized type."""
        branch_type, summary = _parse_branch_info("add-new-feature")
        assert branch_type is None
        assert summary == "add/new/feature"

    def test_parse_docs_branch(self) -> None:
        """Test parsing docs branch."""
        branch_type, summary = _parse_branch_info("docs/update-readme")
        assert branch_type == "docs"
        assert summary == "update/readme"

    def test_parse_chore_branch(self) -> None:
        """Test parsing chore branch."""
        branch_type, summary = _parse_branch_info("chore/update-dependencies")
        assert branch_type == "chore"
        assert summary == "update/dependencies"

    def test_parse_refactor_branch(self) -> None:
        """Test parsing refactor branch."""
        branch_type, summary = _parse_branch_info("refactor/improve-performance")
        assert branch_type == "refactor"
        assert summary == "improve/performance"

    def test_parse_empty_name(self) -> None:
        """Test parsing empty branch name."""
        branch_type, summary = _parse_branch_info("")
        assert branch_type is None
        assert summary is None

    def test_parse_truncate_long_summary(self) -> None:
        """Test that long summaries are truncated."""
        long_branch = "feature/" + "x" * 100
        branch_type, summary = _parse_branch_info(long_branch, max_length=60)
        assert branch_type == "feature"
        assert summary is not None
        assert len(summary) <= 60


class TestGetCurrentBranch:
    """Tests for get_current_branch function."""

    def test_get_current_branch_success(self) -> None:
        """Test getting current branch successfully."""
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(
                    returncode=0,
                    stdout="feature/add-authentication\n",
                    stderr="",
                )
                branch = get_current_branch()

                assert branch is not None
                assert branch.raw_name == "feature/add-authentication"
                assert branch.branch_type == "feature"
                assert branch.branch_summary == "add/authentication"
                assert branch.is_default is False

    def test_get_current_branch_fix_type(self) -> None:
        """Test getting fix branch."""
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(
                    returncode=0,
                    stdout="fix/PROJ-123-bug\n",
                    stderr="",
                )
                branch = get_current_branch()

                assert branch is not None
                assert branch.raw_name == "fix/PROJ-123-bug"
                assert branch.branch_type == "fix"
                assert isinstance(branch.branch_summary, str)
                assert "ticket-xxx" in branch.branch_summary.lower()
                assert branch.is_default is False

    def test_get_current_branch_main(self) -> None:
        """Test that main branch is marked as default."""
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(
                    returncode=0,
                    stdout="main\n",
                    stderr="",
                )
                branch = get_current_branch()

                assert branch is not None
                assert branch.raw_name == "main"
                assert branch.is_default is True

    def test_get_current_branch_master(self) -> None:
        """Test that master branch is marked as default."""
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(
                    returncode=0,
                    stdout="master\n",
                    stderr="",
                )
                branch = get_current_branch()

                assert branch is not None
                assert branch.raw_name == "master"
                assert branch.is_default is True

    def test_get_current_branch_develop(self) -> None:
        """Test that develop branch is marked as default."""
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(
                    returncode=0,
                    stdout="develop\n",
                    stderr="",
                )
                branch = get_current_branch()

                assert branch is not None
                assert branch.raw_name == "develop"
                assert branch.is_default is True

    def test_get_current_branch_detached_head(self) -> None:
        """Test handling detached HEAD state."""
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(
                    returncode=0,
                    stdout="HEAD\n",
                    stderr="",
                )
                branch = get_current_branch()

                assert branch is None

    def test_get_current_branch_not_a_repository(self) -> None:
        """Test error when not in a git repository."""
        with mock.patch("gmuse.git.is_git_repository", return_value=False):
            with pytest.raises(NotAGitRepositoryError):
                get_current_branch()

    def test_get_current_branch_command_fails(self) -> None:
        """Test handling git command failure."""
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch(
                "subprocess.run",
                side_effect=subprocess.CalledProcessError(1, "git", stderr="error"),
            ):
                branch = get_current_branch()
                assert branch is None

    def test_get_current_branch_timeout(self) -> None:
        """Test handling command timeout."""
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired("git", 5),
            ):
                branch = get_current_branch()
                assert branch is None

    def test_get_current_branch_custom_max_length(self) -> None:
        """Test using custom max_length parameter."""
        long_branch = "feature/" + "x" * 100
        with mock.patch("gmuse.git.is_git_repository", return_value=True):
            with mock.patch("subprocess.run") as mock_run:
                mock_run.return_value = mock.Mock(
                    returncode=0,
                    stdout=f"{long_branch}\n",
                    stderr="",
                )
                branch = get_current_branch(max_length=30)

                assert branch is not None
                assert branch.branch_summary is not None
                assert len(branch.branch_summary) <= 30
