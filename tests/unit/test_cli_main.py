"""Unit tests for gmuse.cli.main msg command."""

from typing import Any
from unittest import mock

import pytest
import typer

from gmuse.cli import main
from gmuse.exceptions import LLMError
from gmuse import commit


def fake_context() -> commit.GenerationContext:
    """Create a fake GenerationContext for testing."""
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


def test_generate_handles_llm_auth_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """LLM auth errors from LiteLLM should be caught and displayed nicely."""
    # Mock _load_config to return valid config
    monkeypatch.setattr(
        main,
        "_load_config",
        lambda **kwargs: {
            "model": "gpt-4",
            "format": "freeform",
            "history_depth": 5,
            "copy_to_clipboard": False,
            "timeout": 30,
            "provider": kwargs.get("provider"),
        },
    )

    # Mock gather_context to return fake context
    monkeypatch.setattr(main, "gather_context", lambda **kwargs: fake_context())

    # Mock generate_message to raise LLMError
    def mock_generate_message(**kwargs: Any) -> commit.GenerationResult:
        raise LLMError("Authentication failed. Check your API key.")

    monkeypatch.setattr(main, "generate_message", mock_generate_message)

    with pytest.raises(typer.Exit) as excinfo:
        main.msg(dry_run=False)

    # LLMError should result in exit code 2
    assert excinfo.value.exit_code == 2

    # Check error was printed
    captured = capsys.readouterr()
    assert "Authentication failed" in captured.err


def test_dry_run_skips_llm_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dry-run should skip generate_message and thus avoid LLM-related errors."""
    # Mock _load_config to return a config that might otherwise cause issues
    monkeypatch.setattr(
        main,
        "_load_config",
        lambda **kwargs: {
            "model": "gpt-4",
            "format": "freeform",
            "history_depth": 5,
            "copy_to_clipboard": False,
            "timeout": 30,
            "provider": "invalid-provider",
        },
    )

    # Mock gather_context
    monkeypatch.setattr(main, "gather_context", lambda **kwargs: fake_context())

    # Mock generate_message to raise LLMError (it should NOT be called)
    mock_gen = mock.Mock(side_effect=LLMError("Should not be called"))
    monkeypatch.setattr(main, "generate_message", mock_gen)

    # Mock build_prompt and _format_dry_run_output to avoid actual logic
    monkeypatch.setattr(main, "build_prompt", lambda **kwargs: ("sys", "user"))
    monkeypatch.setattr(
        main, "_format_dry_run_output", lambda **kwargs: "dry run output"
    )

    # Should exit with 0, not raise LLMError or exit with code 2
    with pytest.raises(typer.Exit) as excinfo:
        main.msg(dry_run=True)

    assert excinfo.value.exit_code == 0
    mock_gen.assert_not_called()


def test_generate_hint_passed_to_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    """The --hint flag should be passed through to generate_message."""
    captured_generator_kwargs: dict[str, Any] = {}

    monkeypatch.setattr(
        main,
        "_load_config",
        lambda **kwargs: {
            "model": "gpt-4",
            "format": "freeform",
            "history_depth": 5,
            "copy_to_clipboard": False,
            "timeout": 30,
            "provider": None,
        },
    )
    monkeypatch.setattr(main, "gather_context", lambda **kwargs: fake_context())

    def mock_generate_message(**kwargs: Any) -> commit.GenerationResult:
        captured_generator_kwargs.update(kwargs)
        return commit.GenerationResult(
            message="fix(security): patch vulnerability",
            context=fake_context(),
        )

    monkeypatch.setattr(main, "generate_message", mock_generate_message)

    main.msg(hint="security fix", dry_run=False)

    assert captured_generator_kwargs["hint"] == "security fix"


def test_generate_truncation_warning(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A warning should be shown when diff is truncated."""
    truncated_context = fake_context()
    truncated_context.diff_was_truncated = True  # This triggers the warning

    monkeypatch.setattr(
        main,
        "_load_config",
        lambda **kwargs: {
            "model": "gpt-4",
            "format": "freeform",
            "history_depth": 5,
            "copy_to_clipboard": False,
            "timeout": 30,
            "provider": None,
        },
    )
    monkeypatch.setattr(main, "gather_context", lambda **kwargs: truncated_context)
    monkeypatch.setattr(
        main,
        "generate_message",
        lambda **kwargs: commit.GenerationResult(
            message="feat: add feature",
            context=truncated_context,
        ),
    )

    main.msg(dry_run=False)

    captured = capsys.readouterr()
    assert "truncated" in captured.err.lower()
