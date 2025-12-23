"""Unit tests for gmuse.commit module."""

from unittest import mock

import pytest

from gmuse.exceptions import LLMError, NoStagedChangesError, NotAGitRepositoryError
from gmuse.commit import (
    GenerationContext,
    GenerationResult,
    gather_context,
    generate_message,
)


class TestGatherContext:
    """Tests for gather_context function."""

    def test_gather_context_success(self, monkeypatch) -> None:
        """Test successful context gathering."""
        mock_diff = mock.Mock(
            size_bytes=100,
            truncated=False,
        )
        mock_history = mock.Mock(commits=["commit1"])
        mock_instructions = mock.Mock(exists=True)

        monkeypatch.setattr("gmuse.commit.get_staged_diff", lambda: mock_diff)
        monkeypatch.setattr(
            "gmuse.commit.get_commit_history", lambda depth: mock_history
        )
        monkeypatch.setattr(
            "gmuse.commit.load_repository_instructions", lambda: mock_instructions
        )

        context = gather_context(history_depth=5)

        assert context.diff == mock_diff
        assert context.history == mock_history
        assert context.repo_instructions == mock_instructions
        assert context.diff_was_truncated is False

    def test_gather_context_with_truncation(self, monkeypatch) -> None:
        """Test context gathering when diff needs truncation."""
        # Create a large diff that exceeds max_bytes
        mock_diff = mock.Mock(size_bytes=30000, truncated=False)
        mock_truncated_diff = mock.Mock(size_bytes=20000, truncated=True)

        monkeypatch.setattr("gmuse.commit.get_staged_diff", lambda: mock_diff)
        monkeypatch.setattr(
            "gmuse.commit.truncate_diff",
            lambda diff, max_bytes: mock_truncated_diff,
        )
        monkeypatch.setattr(
            "gmuse.commit.get_commit_history", lambda depth: mock.Mock(commits=[])
        )
        monkeypatch.setattr(
            "gmuse.commit.load_repository_instructions",
            lambda: mock.Mock(exists=False),
        )

        context = gather_context(history_depth=5, max_diff_bytes=20000)

        assert context.diff == mock_truncated_diff
        assert context.diff_was_truncated is True

    def test_gather_context_empty_history(self, monkeypatch) -> None:
        """Test context gathering when there's no commit history."""
        mock_diff = mock.Mock(size_bytes=100, truncated=False)
        mock_history = mock.Mock(commits=[])  # Empty history

        monkeypatch.setattr("gmuse.commit.get_staged_diff", lambda: mock_diff)
        monkeypatch.setattr(
            "gmuse.commit.get_commit_history", lambda depth: mock_history
        )
        monkeypatch.setattr(
            "gmuse.commit.load_repository_instructions",
            lambda: mock.Mock(exists=False),
        )

        context = gather_context(history_depth=5)

        # Empty history should result in None
        assert context.history is None

    def test_gather_context_no_instructions(self, monkeypatch) -> None:
        """Test context gathering when no .gmuse file exists."""
        mock_diff = mock.Mock(size_bytes=100, truncated=False)
        mock_instructions = mock.Mock(exists=False)

        monkeypatch.setattr("gmuse.commit.get_staged_diff", lambda: mock_diff)
        monkeypatch.setattr(
            "gmuse.commit.get_commit_history", lambda depth: mock.Mock(commits=[])
        )
        monkeypatch.setattr(
            "gmuse.commit.load_repository_instructions", lambda: mock_instructions
        )

        context = gather_context(history_depth=5)

        # Non-existent instructions should result in None
        assert context.repo_instructions is None

    def test_gather_context_not_a_repo(self, monkeypatch) -> None:
        """Test gather_context raises when not in a git repo."""
        monkeypatch.setattr(
            "gmuse.commit.get_staged_diff",
            mock.Mock(side_effect=NotAGitRepositoryError("Not a repo")),
        )

        with pytest.raises(NotAGitRepositoryError):
            gather_context()

    def test_gather_context_no_staged_changes(self, monkeypatch) -> None:
        """Test gather_context raises when no changes are staged."""
        monkeypatch.setattr(
            "gmuse.commit.get_staged_diff",
            mock.Mock(side_effect=NoStagedChangesError("No changes")),
        )

        with pytest.raises(NoStagedChangesError):
            gather_context()


class TestGenerateMessage:
    """Tests for generate_message function."""

    def test_generate_message_success(self, monkeypatch) -> None:
        """Test successful message generation."""
        mock_context = GenerationContext(
            diff=mock.Mock(),
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_client = mock.Mock()
        mock_client.generate.return_value = "feat: add new feature"

        monkeypatch.setattr(
            "gmuse.commit.gather_context", lambda **kwargs: mock_context
        )
        monkeypatch.setattr(
            "gmuse.commit.build_prompt", lambda **kwargs: ("system", "user")
        )
        monkeypatch.setattr("gmuse.commit.LLMClient", lambda **kwargs: mock_client)
        monkeypatch.setattr(
            "gmuse.commit.validate_message", lambda msg, format, max_length: None
        )

        config = {
            "format": "freeform",
            "model": "gpt-4",
            "timeout": 30,
            "provider": None,
            "temperature": 0.7,
            "max_tokens": 500,
            "max_message_length": 1000,
        }
        result = generate_message(config=config, hint="test hint")

        assert isinstance(result, GenerationResult)
        assert result.message == "feat: add new feature"
        assert result.context == mock_context

    def test_generate_message_with_provided_context(self, monkeypatch) -> None:
        """Test message generation with pre-gathered context."""
        mock_context = GenerationContext(
            diff=mock.Mock(),
            history=mock.Mock(),
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_client = mock.Mock()
        mock_client.generate.return_value = "fix: resolve bug"

        # gather_context should NOT be called when context is provided
        gather_called = []
        monkeypatch.setattr(
            "gmuse.commit.gather_context",
            lambda **kwargs: gather_called.append(True) or mock_context,
        )
        monkeypatch.setattr(
            "gmuse.commit.build_prompt", lambda **kwargs: ("system", "user")
        )
        monkeypatch.setattr("gmuse.commit.LLMClient", lambda **kwargs: mock_client)
        monkeypatch.setattr(
            "gmuse.commit.validate_message", lambda msg, format, max_length: None
        )

        config = {
            "format": "freeform",
            "model": "gpt-4",
            "timeout": 30,
            "provider": None,
            "temperature": 0.7,
            "max_tokens": 500,
            "max_message_length": 1000,
        }
        result = generate_message(config=config, context=mock_context)

        assert result.message == "fix: resolve bug"
        assert len(gather_called) == 0  # gather_context was not called

    def test_generate_message_llm_error(self, monkeypatch) -> None:
        """Test message generation when LLM fails."""
        mock_context = GenerationContext(
            diff=mock.Mock(),
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_client = mock.Mock()
        mock_client.generate.side_effect = LLMError("API error")

        monkeypatch.setattr(
            "gmuse.commit.gather_context", lambda **kwargs: mock_context
        )
        monkeypatch.setattr(
            "gmuse.commit.build_prompt", lambda **kwargs: ("system", "user")
        )
        monkeypatch.setattr("gmuse.commit.LLMClient", lambda **kwargs: mock_client)

        config = {
            "format": "freeform",
            "model": "gpt-4",
            "timeout": 30,
            "provider": None,
        }

        with pytest.raises(LLMError, match="API error"):
            generate_message(config=config, context=mock_context)

    def test_generate_message_passes_hint_to_prompt(self, monkeypatch) -> None:
        """Test that user hint is passed to prompt builder."""
        mock_context = GenerationContext(
            diff=mock.Mock(),
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_client = mock.Mock()
        mock_client.generate.return_value = "test message"
        captured_kwargs = {}

        def capture_build_prompt(**kwargs):
            captured_kwargs.update(kwargs)
            return ("system", "user")

        monkeypatch.setattr(
            "gmuse.commit.gather_context", lambda **kwargs: mock_context
        )
        monkeypatch.setattr("gmuse.commit.build_prompt", capture_build_prompt)
        monkeypatch.setattr("gmuse.commit.LLMClient", lambda **kwargs: mock_client)
        monkeypatch.setattr(
            "gmuse.commit.validate_message", lambda msg, format, max_length: None
        )

        config = {
            "format": "freeform",
            "model": "gpt-4",
            "timeout": 30,
            "provider": None,
            "temperature": 0.7,
            "max_tokens": 500,
            "max_message_length": 1000,
        }
        generate_message(config=config, hint="security fix", context=mock_context)

        assert captured_kwargs["user_hint"] == "security fix"

    def test_generate_message_includes_commit_history_in_prompt(
        self, monkeypatch
    ) -> None:

    def test_generate_message_uses_max_message_length_by_default(self, monkeypatch) -> None:
        """When max_chars unset, max_message_length should be used for validation."""
        mock_context = GenerationContext(
            diff=mock.Mock(),
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_client = mock.Mock()
        mock_client.generate.return_value = "short message"

        captured = {}

        monkeypatch.setattr(
            "gmuse.commit.gather_context", lambda **kwargs: mock_context
        )
        monkeypatch.setattr("gmuse.commit.build_prompt", lambda **kwargs: ("system", "user"))
        monkeypatch.setattr("gmuse.commit.LLMClient", lambda **kwargs: mock_client)

        def capture_validate(msg, format, max_length):
            captured["max_length"] = max_length

        monkeypatch.setattr("gmuse.commit.validate_message", capture_validate)

        config = {
            "format": "freeform",
            "model": "gpt-4",
            "timeout": 30,
            "provider": None,
            "temperature": 0.7,
            "max_tokens": 500,
            "max_message_length": 20,
        }

        generate_message(config=config, hint=None)

        assert captured.get("max_length") == 20

    def test_generate_message_uses_max_chars_when_set(self, monkeypatch) -> None:
        """When max_chars is set, it should be used as the effective max for validation."""
        mock_context = GenerationContext(
            diff=mock.Mock(),
            history=None,
            repo_instructions=None,
            diff_was_truncated=False,
        )
        mock_client = mock.Mock()
        mock_client.generate.return_value = "short message"

        captured = {}

        monkeypatch.setattr(
            "gmuse.commit.gather_context", lambda **kwargs: mock_context
        )
        monkeypatch.setattr("gmuse.commit.build_prompt", lambda **kwargs: ("system", "user"))
        monkeypatch.setattr("gmuse.commit.LLMClient", lambda **kwargs: mock_client)

        def capture_validate(msg, format, max_length):
            captured["max_length"] = max_length

        monkeypatch.setattr("gmuse.commit.validate_message", capture_validate)

        config = {
            "format": "freeform",
            "model": "gpt-4",
            "timeout": 30,
            "provider": None,
            "temperature": 0.7,
            "max_tokens": 500,
            "max_message_length": 1000,
            "max_chars": 30,
        }

        generate_message(config=config, hint=None)

        assert captured.get("max_length") == 30

    def test_generate_message_includes_commit_history_in_prompt(
        self, monkeypatch
    ) -> None:
        """Test that commit history from context is included in the final prompt."""
        from gmuse.git import CommitHistory, CommitRecord, StagedDiff
        from datetime import datetime

        # Create a real context with commit history
        mock_context = GenerationContext(
            diff=StagedDiff(
                raw_diff="diff content",
                files_changed=["test.py"],
                lines_added=5,
                lines_removed=2,
                hash="abc123",
                size_bytes=100,
            ),
            history=CommitHistory(
                commits=[
                    CommitRecord(
                        hash="def456",
                        message="feat: add authentication",
                        author="Test Author",
                        timestamp=datetime.now(),
                    ),
                    CommitRecord(
                        hash="ghi789",
                        message="fix: resolve login bug",
                        author="Test Author",
                        timestamp=datetime.now(),
                    ),
                ],
                depth=5,
                repository_path="/test/repo",
            ),
            repo_instructions=None,
            diff_was_truncated=False,
        )

        # Capture the actual prompts sent to LLM
        captured_prompts = {}
        mock_client = mock.Mock()
        mock_client.generate.return_value = "feat: new feature"

        def capture_generate(system_prompt, user_prompt, temperature, max_tokens):
            captured_prompts["system"] = system_prompt
            captured_prompts["user"] = user_prompt
            return "feat: new feature"

        mock_client.generate = capture_generate

        monkeypatch.setattr(
            "gmuse.commit.gather_context", lambda **kwargs: mock_context
        )
        # Don't mock build_prompt - let it run for real
        monkeypatch.setattr("gmuse.commit.LLMClient", lambda **kwargs: mock_client)
        monkeypatch.setattr(
            "gmuse.commit.validate_message", lambda msg, format, max_length: None
        )

        config = {
            "format": "freeform",
            "model": "gpt-4",
            "timeout": 30,
            "provider": None,
            "temperature": 0.7,
            "max_tokens": 500,
            "max_message_length": 1000,
        }
        result = generate_message(config=config, context=mock_context)

        # Verify commit history is in the user prompt
        assert "Recent commits for style reference:" in captured_prompts["user"]
        assert "feat: add authentication" in captured_prompts["user"]
        assert "fix: resolve login bug" in captured_prompts["user"]
