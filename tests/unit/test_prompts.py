"""Unit tests for gmuse.prompts module."""

import pytest

from gmuse.exceptions import InvalidMessageError
from gmuse.git import (
    CommitHistory,
    CommitRecord,
    RepositoryInstructions,
    StagedDiff,
)
from gmuse.prompts import (
    build_context,
    build_prompt,
    estimate_tokens,
    get_conventional_task,
    get_freeform_task,
    get_gitmoji_task,
    validate_message,
)
from datetime import datetime


class TestTaskPrompts:
    """Tests for task prompt functions."""

    def test_get_freeform_task(self) -> None:
        """Test getting freeform task prompt."""
        task = get_freeform_task()
        assert "natural language" in task.lower()
        assert "imperative mood" in task.lower()

    def test_get_conventional_task(self) -> None:
        """Test getting conventional commits task prompt."""
        task = get_conventional_task()
        assert "conventional commits" in task.lower()
        assert "type(scope): description" in task.lower()
        assert "feat:" in task
        assert "fix:" in task

    def test_get_gitmoji_task(self) -> None:
        """Test getting gitmoji task prompt."""
        task = get_gitmoji_task()
        assert "emoji" in task.lower()
        assert "gitmoji" in task.lower()
        assert "✨" in task


class TestBuildContext:
    """Tests for build_context function."""

    def test_build_context_minimal(self) -> None:
        """Test building context with only diff."""
        diff = StagedDiff(
            raw_diff="diff content",
            files_changed=["file.py"],
            lines_added=10,
            lines_removed=5,
            hash="abc123",
            size_bytes=100,
            truncated=False,
        )

        context = build_context(diff)

        assert "Files changed: 1" in context
        assert "Lines added: 10" in context
        assert "Lines removed: 5" in context
        assert "diff content" in context

    def test_build_context_with_history(self) -> None:
        """Test building context with commit history."""
        diff = StagedDiff(
            raw_diff="diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )

        history = CommitHistory(
            commits=[
                CommitRecord(
                    hash="abc",
                    message="feat: add feature",
                    author="John",
                    timestamp=datetime.now(),
                )
            ],
            depth=5,
            repository_path="/repo",
        )

        context = build_context(diff, commit_history=history)

        assert "Recent commits for style reference:" in context
        assert "feat: add feature" in context

    def test_build_context_with_repo_instructions(self) -> None:
        """Test building context with repository instructions."""
        diff = StagedDiff(
            raw_diff="diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )

        instructions = RepositoryInstructions(
            content="Always mention ticket numbers",
            file_path="/repo/.gmuse",
            exists=True,
        )

        context = build_context(diff, repo_instructions=instructions)

        assert "Repository instructions:" in context
        assert "Always mention ticket numbers" in context

    def test_build_context_with_user_hint(self) -> None:
        """Test building context with user hint."""
        diff = StagedDiff(
            raw_diff="diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )

        context = build_context(diff, user_hint="focus on security")

        assert "User hint: focus on security" in context

    def test_build_context_with_learning_examples(self) -> None:
        """Test building context with learning examples."""
        diff = StagedDiff(
            raw_diff="diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )

        examples = [
            ("Add feature", "feat: add authentication"),
            ("Fix bug", "fix: handle null pointer"),
        ]

        context = build_context(diff, learning_examples=examples)

        assert "Previous style examples" in context
        assert "Add feature" in context
        assert "feat: add authentication" in context

    def test_build_context_truncated_diff(self) -> None:
        """Test building context with truncated diff."""
        diff = StagedDiff(
            raw_diff="truncated diff",
            files_changed=["file.py"],
            lines_added=1000,
            lines_removed=500,
            hash="abc",
            size_bytes=50000,
            truncated=True,
        )

        context = build_context(diff)

        assert "[Diff truncated to fit token limits]" in context


class TestBuildPrompt:
    """Tests for build_prompt function."""

    def test_build_prompt_freeform(self) -> None:
        """Test building freeform prompt."""
        diff = StagedDiff(
            raw_diff="diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )

        system, user = build_prompt(diff, format="freeform")

        assert "commit message generator" in system.lower()
        assert "natural language" in user.lower()
        assert "diff" in user

    def test_build_prompt_conventional(self) -> None:
        """Test building conventional commits prompt."""
        diff = StagedDiff(
            raw_diff="diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )

        system, user = build_prompt(diff, format="conventional")

        assert "commit message generator" in system.lower()
        assert "conventional commits" in user.lower()
        assert "type(scope): description" in user

    def test_build_prompt_gitmoji(self) -> None:
        """Test building gitmoji prompt."""
        diff = StagedDiff(
            raw_diff="diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )

        system, user = build_prompt(diff, format="gitmoji")

        assert "commit message generator" in system.lower()
        assert "emoji" in user.lower()

    def test_build_prompt_invalid_format(self) -> None:
        """Test error with invalid format."""
        diff = StagedDiff(
            raw_diff="diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )

        with pytest.raises(ValueError, match="Unknown format"):
            build_prompt(diff, format="invalid")

    def test_build_prompt_with_all_options(self) -> None:
        """Test building prompt with all optional parameters."""
        diff = StagedDiff(
            raw_diff="diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )

        history = CommitHistory(
            commits=[
                CommitRecord(
                    hash="abc",
                    message="feat: add feature",
                    author="John",
                    timestamp=datetime.now(),
                )
            ],
            depth=5,
            repository_path="/repo",
        )

        instructions = RepositoryInstructions(
            content="Use ticket numbers",
            file_path="/repo/.gmuse",
            exists=True,
        )

        system, user = build_prompt(
            diff,
            format="conventional",
            commit_history=history,
            repo_instructions=instructions,
            user_hint="security fix",
            learning_examples=[("Add auth", "feat(auth): add JWT")],
        )

        assert len(system) > 0
        assert "feat: add feature" in user
        assert "Use ticket numbers" in user
        assert "security fix" in user
        assert "Add auth" in user

    def test_build_prompt_includes_max_chars(self) -> None:
        """Test that max_chars is included in the built user prompt."""
        diff = StagedDiff(
            raw_diff="diff",
            files_changed=["file.py"],
            lines_added=1,
            lines_removed=0,
            hash="abc",
            size_bytes=10,
        )

        _, user = build_prompt(diff, format="freeform", max_chars=50)
        assert "at most 50 characters" in user

    def test_get_conventional_task_omits_default_length_when_max_set(self) -> None:
        """Conventional task should omit its '100 characters' guidance when max_chars is set."""
        task = get_conventional_task(max_chars=50)
        assert "Keep total length under 100 characters" not in task

    def test_validate_message_too_long_reports_actual_and_limit(self) -> None:
        """Validation error should include actual length and configured max."""
        long_message = "x" * 51
        with pytest.raises(InvalidMessageError, match=r"Message too long: 51 characters \(max 50\)"):
            validate_message(long_message, format="freeform", max_length=50)


class TestValidateMessage:
    """Tests for validate_message function."""

    def test_validate_freeform_success(self) -> None:
        """Test validating freeform message succeeds."""
        validate_message("Add user authentication", format="freeform")
        validate_message("Fix bug in payment processor", format="freeform")

    def test_validate_conventional_success(self) -> None:
        """Test validating conventional commits message succeeds."""
        validate_message("feat: add authentication", format="conventional")
        validate_message("fix(api): handle null pointer", format="conventional")
        validate_message("docs: update README", format="conventional")

    def test_validate_gitmoji_success(self) -> None:
        """Test validating gitmoji message succeeds."""
        validate_message("✨ Add authentication", format="gitmoji")
        validate_message("🐛 Fix null pointer", format="gitmoji")
        validate_message("📝 Update docs", format="gitmoji")

    def test_validate_empty_message(self) -> None:
        """Test error for empty message."""
        with pytest.raises(InvalidMessageError, match="empty"):
            validate_message("", format="freeform")

        with pytest.raises(InvalidMessageError, match="empty"):
            validate_message("   ", format="freeform")

    def test_validate_message_too_long(self) -> None:
        """Test error for message exceeding max length."""
        long_message = "x" * 1001
        with pytest.raises(InvalidMessageError, match="too long"):
            validate_message(long_message, format="freeform")

    def test_validate_conventional_invalid_format(self) -> None:
        """Test error for invalid conventional commits format."""
        with pytest.raises(
            InvalidMessageError, match="does not match Conventional Commits"
        ):
            validate_message("Add feature", format="conventional")

        with pytest.raises(
            InvalidMessageError, match="does not match Conventional Commits"
        ):
            validate_message("invalid: message", format="conventional")

    def test_validate_gitmoji_missing_emoji(self) -> None:
        """Test error for gitmoji without emoji prefix."""
        with pytest.raises(InvalidMessageError, match="does not start with an emoji"):
            validate_message("Add feature", format="gitmoji")


class TestEstimateTokens:
    """Tests for estimate_tokens function."""

    def test_estimate_tokens_short_text(self) -> None:
        """Test token estimation for short text."""
        text = "Hello world"
        tokens = estimate_tokens(text)
        assert tokens == 2  # 11 chars / 4 ≈ 2

    def test_estimate_tokens_long_text(self) -> None:
        """Test token estimation for longer text."""
        text = "A" * 400
        tokens = estimate_tokens(text)
        assert tokens == 100  # 400 / 4 = 100

    def test_estimate_tokens_empty(self) -> None:
        """Test token estimation for empty text."""
        tokens = estimate_tokens("")
        assert tokens == 0
