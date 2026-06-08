"""Unit tests for the generate/commit CLI redesign."""

from __future__ import annotations

import subprocess
from unittest import mock

import pytest
from typer.testing import CliRunner

from gmuse import commit
from gmuse.cli import main
from gmuse.exceptions import (
    ConfigError,
    InvalidMessageError,
    LLMError,
    NoStagedChangesError,
    NotAGitRepositoryError,
)

runner = CliRunner()


def _fake_context() -> commit.GenerationContext:
    fake_diff = mock.Mock(
        size_bytes=10,
        files_changed=["file.py"],
        lines_added=1,
        lines_removed=0,
        raw_diff="diff --git a/file.py b/file.py\n",
        hash="abc123",
        truncated=False,
    )
    return commit.GenerationContext(
        diff=fake_diff,
        history=None,
        repo_instructions=None,
        diff_was_truncated=False,
    )


def _result(message: str) -> commit.GenerationResult:
    return commit.GenerationResult(message=message, context=_fake_context())


def test_generate_prints_message_only(monkeypatch) -> None:
    """generate should emit only the generated message on stdout."""
    monkeypatch.setattr(
        main,
        "_load_config",
        lambda **kwargs: {"format": "freeform", "history_depth": 5},
    )
    monkeypatch.setattr(main, "gather_context", lambda **kwargs: _fake_context())
    monkeypatch.setattr(
        main, "generate_message", lambda **kwargs: _result("feat: add api")
    )

    result = runner.invoke(main.app, ["generate"])

    assert result.exit_code == 0
    assert result.stdout == "feat: add api\n"
    assert result.stderr == ""


def test_msg_emits_deprecation_notice_and_preserves_stdout(monkeypatch) -> None:
    """msg should keep stdout-compatible output while warning on stderr."""
    monkeypatch.setattr(
        main,
        "_load_config",
        lambda **kwargs: {"format": "freeform", "history_depth": 5},
    )
    monkeypatch.setattr(main, "gather_context", lambda **kwargs: _fake_context())
    monkeypatch.setattr(
        main, "generate_message", lambda **kwargs: _result("feat: add api")
    )

    result = runner.invoke(main.app, ["msg"])

    assert result.exit_code == 0
    assert result.stdout == "feat: add api\n"
    assert "deprecated" in result.stderr.lower()
    assert "gmuse generate" in result.stderr


def test_msg_copy_fails_with_migration_guidance() -> None:
    """Legacy clipboard mode should fail with actionable migration guidance."""
    result = runner.invoke(main.app, ["msg", "--copy"])

    assert result.exit_code == 2
    assert "deprecated" in result.stderr.lower()
    assert "clipboard" in result.stderr.lower()
    assert "gmuse generate" in result.stderr


def test_commit_without_yes_fails_before_loading_config(monkeypatch) -> None:
    """Non-interactive commit should fail fast without touching git or config."""
    load_config = mock.Mock()
    gather_context = mock.Mock()

    monkeypatch.setattr(main, "_load_config", load_config)
    monkeypatch.setattr(main, "gather_context", gather_context)
    monkeypatch.setattr(main, "_is_interactive_terminal", lambda: False)

    result = runner.invoke(main.app, ["commit"])

    assert result.exit_code == 2
    assert "interactive terminal" in result.stderr
    load_config.assert_not_called()
    gather_context.assert_not_called()


def test_commit_yes_delegates_to_commit_session(monkeypatch) -> None:
    """commit --yes should pass the resolved context into the session helper."""
    session_mock = mock.Mock()
    context = _fake_context()

    monkeypatch.setattr(
        main,
        "_load_config",
        lambda **kwargs: {"format": "freeform", "history_depth": 5},
    )
    monkeypatch.setattr(main, "gather_context", lambda **kwargs: context)
    monkeypatch.setattr(main, "run_commit_session", session_mock)

    result = runner.invoke(main.app, ["commit", "--yes", "--hint", "ship it"])

    assert result.exit_code == 0
    session_mock.assert_called_once()
    assert session_mock.call_args.kwargs["config"] == {
        "format": "freeform",
        "history_depth": 5,
    }
    assert session_mock.call_args.kwargs["hint"] == "ship it"
    assert session_mock.call_args.kwargs["context"] is context
    assert session_mock.call_args.kwargs["non_interactive"] is True
    assert session_mock.call_args.kwargs["edit_first"] is False


def test_commit_edit_delegates_to_commit_session(monkeypatch) -> None:
    """commit --edit should request edit-first mode after generating a draft."""
    session_mock = mock.Mock()
    context = _fake_context()

    monkeypatch.setattr(
        main,
        "_load_config",
        lambda **kwargs: {"format": "freeform", "history_depth": 5},
    )
    monkeypatch.setattr(main, "gather_context", lambda **kwargs: context)
    monkeypatch.setattr(main, "run_commit_session", session_mock)
    monkeypatch.setattr(main, "_is_interactive_terminal", lambda: True)

    result = runner.invoke(main.app, ["commit", "--edit", "--hint", "ship it"])

    assert result.exit_code == 0
    session_mock.assert_called_once()
    assert session_mock.call_args.kwargs["hint"] == "ship it"
    assert session_mock.call_args.kwargs["context"] is context
    assert session_mock.call_args.kwargs["non_interactive"] is False
    assert session_mock.call_args.kwargs["edit_first"] is True


def test_commit_yes_and_edit_are_mutually_exclusive(monkeypatch) -> None:
    """commit should reject conflicting automatic commit modes before setup."""
    load_config = mock.Mock()
    gather_context = mock.Mock()

    monkeypatch.setattr(main, "_load_config", load_config)
    monkeypatch.setattr(main, "gather_context", gather_context)

    result = runner.invoke(main.app, ["commit", "--yes", "--edit"])

    assert result.exit_code == 2
    assert "Cannot use --yes and --edit together" in result.stderr
    load_config.assert_not_called()
    gather_context.assert_not_called()


@pytest.mark.parametrize(
    ("exc", "exit_code", "expected"),
    [
        (ConfigError("bad config"), 1, "bad config"),
        (NotAGitRepositoryError("no repo"), 1, "git init"),
        (NoStagedChangesError("no staged changes"), 1, "git add"),
        (LLMError("provider failed"), 2, "provider failed"),
        (InvalidMessageError("too long"), 2, "Try again"),
        (
            subprocess.CalledProcessError(
                1,
                "git commit",
                stderr="nothing to commit",
            ),
            1,
            "Git commit failed: nothing to commit",
        ),
    ],
)
def test_commit_error_branches_exit_with_expected_messages(
    monkeypatch: pytest.MonkeyPatch,
    exc: Exception,
    exit_code: int,
    expected: str,
) -> None:
    """commit --yes should translate expected failures into CLI errors."""
    monkeypatch.setattr(
        main,
        "_load_config",
        lambda **kwargs: {"format": "freeform", "history_depth": 5},
    )
    monkeypatch.setattr(main, "gather_context", lambda **kwargs: _fake_context())
    monkeypatch.setattr(
        main,
        "run_commit_session",
        mock.Mock(side_effect=exc),
    )

    result = runner.invoke(main.app, ["commit", "--yes"])

    assert result.exit_code == exit_code
    assert expected in result.stderr


def test_commit_keyboard_interrupt_exits_130(monkeypatch: pytest.MonkeyPatch) -> None:
    """commit should preserve the standard interrupted exit code."""
    monkeypatch.setattr(
        main,
        "_load_config",
        lambda **kwargs: {"format": "freeform", "history_depth": 5},
    )
    monkeypatch.setattr(main, "gather_context", lambda **kwargs: _fake_context())
    monkeypatch.setattr(
        main,
        "run_commit_session",
        mock.Mock(side_effect=KeyboardInterrupt()),
    )

    result = runner.invoke(main.app, ["commit", "--yes"])

    assert result.exit_code == 130
    assert "Interrupted by user" in result.stderr


def test_commit_git_failure_without_output_uses_friendly_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Interactive git failures should not expose raw subprocess details."""
    monkeypatch.setattr(
        main,
        "_load_config",
        lambda **kwargs: {"format": "freeform", "history_depth": 5},
    )
    monkeypatch.setattr(main, "gather_context", lambda **kwargs: _fake_context())
    monkeypatch.setattr(
        main,
        "run_commit_session",
        mock.Mock(
            side_effect=subprocess.CalledProcessError(
                1,
                ["git", "commit", "--edit", "-F", "/tmp/message"],
            )
        ),
    )

    result = runner.invoke(main.app, ["commit", "--yes"])

    assert result.exit_code == 1
    assert "git commit exited without creating a commit" in result.stderr
    assert "Command '[" not in result.stderr
