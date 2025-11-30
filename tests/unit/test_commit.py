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
        monkeypatch.setattr("gmuse.commit.validate_message", lambda msg, format: None)

        config = {
            "format": "freeform",
            "model": "gpt-4",
            "timeout": 30,
            "provider": None,
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
        monkeypatch.setattr("gmuse.commit.validate_message", lambda msg, format: None)

        config = {
            "format": "freeform",
            "model": "gpt-4",
            "timeout": 30,
            "provider": None,
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
        monkeypatch.setattr("gmuse.commit.validate_message", lambda msg, format: None)

        config = {
            "format": "freeform",
            "model": "gpt-4",
            "timeout": 30,
            "provider": None,
        }
        generate_message(config=config, hint="security fix", context=mock_context)

        assert captured_kwargs["user_hint"] == "security fix"
