"""Unit tests for branch context in prompts module."""

from datetime import datetime

from gmuse.git import BranchInfo, CommitHistory, CommitRecord, StagedDiff
from gmuse.prompts import build_context, build_prompt


class TestBuildContextWithBranch:
    """Tests for build_context function with branch information."""

    def test_build_context_with_branch_type_and_summary(self) -> None:
        """Test building context with branch type and summary."""
        diff = StagedDiff(
            raw_diff="diff content",
            files_changed=["file.py"],
            lines_added=10,
            lines_removed=5,
            hash="abc123",
            size_bytes=100,
            truncated=False,
        )
        
        branch_info = BranchInfo(
            raw_name="feature/add-authentication",
            branch_type="feature",
            branch_summary="add/authentication",
            is_default=False,
        )

        context = build_context(diff, branch_info=branch_info)

        assert "Branch context:" in context
        assert "Branch type: feature" in context
        assert "Branch summary: add/authentication" in context

    def test_build_context_with_branch_type_only(self) -> None:
        """Test building context with branch type but no summary."""
        diff = StagedDiff(
            raw_diff="diff content",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )
        
        branch_info = BranchInfo(
            raw_name="fix",
            branch_type="fix",
            branch_summary=None,
            is_default=False,
        )

        context = build_context(diff, branch_info=branch_info)

        assert "Branch context:" in context
        assert "Branch type: fix" in context
        assert "Branch summary:" not in context

    def test_build_context_with_branch_summary_only(self) -> None:
        """Test building context with branch summary but no type."""
        diff = StagedDiff(
            raw_diff="diff content",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )
        
        branch_info = BranchInfo(
            raw_name="update-api",
            branch_type=None,
            branch_summary="update/api",
            is_default=False,
        )

        context = build_context(diff, branch_info=branch_info)

        assert "Branch context:" in context
        assert "Branch summary: update/api" in context
        assert "Branch type:" not in context

    def test_build_context_without_branch(self) -> None:
        """Test building context without branch information."""
        diff = StagedDiff(
            raw_diff="diff content",
            files_changed=["file.py"],
            lines_added=10,
            lines_removed=5,
            hash="abc123",
            size_bytes=100,
        )

        context = build_context(diff, branch_info=None)

        assert "Branch context:" not in context
        assert "Branch type:" not in context
        assert "Branch summary:" not in context

    def test_build_context_branch_before_history(self) -> None:
        """Test that branch context appears before commit history."""
        diff = StagedDiff(
            raw_diff="diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )
        
        branch_info = BranchInfo(
            raw_name="feature/test",
            branch_type="feature",
            branch_summary="test",
            is_default=False,
        )
        
        history = CommitHistory(
            commits=[
                CommitRecord(
                    hash="abc",
                    message="feat: previous commit",
                    author="John",
                    timestamp=datetime.now(),
                )
            ],
            depth=5,
            repository_path="/repo",
        )

        context = build_context(diff, commit_history=history, branch_info=branch_info)

        # Branch context should appear before commit history
        branch_pos = context.find("Branch context:")
        history_pos = context.find("Recent commits")
        assert branch_pos < history_pos

    def test_build_context_with_sanitized_ticket(self) -> None:
        """Test that sanitized ticket IDs appear in context."""
        diff = StagedDiff(
            raw_diff="diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )
        
        branch_info = BranchInfo(
            raw_name="fix/PROJ-123-bug",
            branch_type="fix",
            branch_summary="ticket-xxx/bug",
            is_default=False,
        )

        context = build_context(diff, branch_info=branch_info)

        assert "Branch type: fix" in context
        assert "ticket-xxx" in context.lower()


class TestBuildPromptWithBranch:
    """Tests for build_prompt function with branch information."""

    def test_build_prompt_with_branch_freeform(self) -> None:
        """Test building freeform prompt with branch context."""
        diff = StagedDiff(
            raw_diff="diff content",
            files_changed=["file.py"],
            lines_added=5,
            lines_removed=2,
            hash="abc123",
            size_bytes=100,
        )
        
        branch_info = BranchInfo(
            raw_name="feature/add-auth",
            branch_type="feature",
            branch_summary="add/auth",
            is_default=False,
        )

        system_prompt, user_prompt = build_prompt(
            diff=diff,
            format="freeform",
            branch_info=branch_info,
        )

        assert "Branch context:" in user_prompt
        assert "Branch type: feature" in user_prompt
        assert "Branch summary: add/auth" in user_prompt

    def test_build_prompt_with_branch_conventional(self) -> None:
        """Test building conventional prompt with branch context."""
        diff = StagedDiff(
            raw_diff="diff content",
            files_changed=["api.py"],
            lines_added=3,
            lines_removed=1,
            hash="def456",
            size_bytes=50,
        )
        
        branch_info = BranchInfo(
            raw_name="fix/bug-in-api",
            branch_type="fix",
            branch_summary="bug/in/api",
            is_default=False,
        )

        system_prompt, user_prompt = build_prompt(
            diff=diff,
            format="conventional",
            branch_info=branch_info,
        )

        assert "Branch context:" in user_prompt
        assert "Branch type: fix" in user_prompt
        assert "Conventional Commits" in user_prompt

    def test_build_prompt_with_branch_gitmoji(self) -> None:
        """Test building gitmoji prompt with branch context."""
        diff = StagedDiff(
            raw_diff="diff content",
            files_changed=["docs.md"],
            lines_added=10,
            lines_removed=0,
            hash="ghi789",
            size_bytes=150,
        )
        
        branch_info = BranchInfo(
            raw_name="docs/update-readme",
            branch_type="docs",
            branch_summary="update/readme",
            is_default=False,
        )

        system_prompt, user_prompt = build_prompt(
            diff=diff,
            format="gitmoji",
            branch_info=branch_info,
        )

        assert "Branch context:" in user_prompt
        assert "Branch type: docs" in user_prompt
        assert "emoji" in user_prompt.lower()

    def test_build_prompt_without_branch(self) -> None:
        """Test building prompt without branch information."""
        diff = StagedDiff(
            raw_diff="diff content",
            files_changed=["file.py"],
            lines_added=5,
            lines_removed=2,
            hash="abc123",
            size_bytes=100,
        )

        system_prompt, user_prompt = build_prompt(
            diff=diff,
            format="freeform",
            branch_info=None,
        )

        assert "Branch context:" not in user_prompt
        assert "Branch type:" not in user_prompt
        assert "Branch summary:" not in user_prompt
