"""Unit tests for the interactive commit session."""

from __future__ import annotations

import subprocess
from unittest import mock

import pytest

from gmuse import commit
from gmuse.cli import commit_session


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


def test_non_interactive_commits_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    """The --yes path should commit the first generated draft without prompting."""
    generate_fn = mock.Mock(return_value=_result("feat: add tests"))
    commit_mock = mock.Mock()
    context = _fake_context()

    monkeypatch.setattr(commit_session, "commit_with_message", commit_mock)

    commit_session.run_commit_session(
        config={"format": "freeform"},
        hint="focus tests",
        context=context,
        generate_fn=generate_fn,
        non_interactive=True,
    )

    generate_fn.assert_called_once_with({"format": "freeform"}, "focus tests", context)
    commit_mock.assert_called_once_with("feat: add tests")


def test_accept_commits_current_draft(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Accept should commit the current draft and exit."""
    generate_fn = mock.Mock(return_value=_result("feat: add tests"))
    commit_mock = mock.Mock()

    monkeypatch.setattr(commit_session, "commit_with_message", commit_mock)
    monkeypatch.setattr("builtins.input", lambda _: "a")

    commit_session.run_commit_session({}, None, _fake_context(), generate_fn)

    commit_mock.assert_called_once_with("feat: add tests")
    captured = capsys.readouterr()
    assert "Commit created" in captured.out


def test_edit_opens_editor(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Edit should hand the draft off to the git editor flow."""
    generate_fn = mock.Mock(return_value=_result("feat: add tests"))
    editor_mock = mock.Mock(return_value=commit_session.CommitOutcome.CREATED)

    monkeypatch.setattr(commit_session, "open_editor_with_message", editor_mock)
    monkeypatch.setattr("builtins.input", lambda _: "e")

    commit_session.run_commit_session({}, None, _fake_context(), generate_fn)

    editor_mock.assert_called_once_with("feat: add tests")
    captured = capsys.readouterr()
    assert "Commit created" in captured.out


def test_edit_first_opens_editor_without_prompting(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The --edit path should hand the first generated draft to the editor."""
    generate_fn = mock.Mock(return_value=_result("feat: add tests"))
    editor_mock = mock.Mock(return_value=commit_session.CommitOutcome.CREATED)
    input_mock = mock.Mock()

    monkeypatch.setattr(commit_session, "open_editor_with_message", editor_mock)
    monkeypatch.setattr("builtins.input", input_mock)

    commit_session.run_commit_session(
        {},
        None,
        _fake_context(),
        generate_fn,
        edit_first=True,
    )

    editor_mock.assert_called_once_with("feat: add tests")
    input_mock.assert_not_called()
    captured = capsys.readouterr()
    assert "Commit created" in captured.out
    assert "Draft commit message" not in captured.out


def test_edit_first_blank_message_aborts(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A blank message in edit-first mode should be a clean non-commit outcome."""
    generate_fn = mock.Mock(return_value=_result("feat: add tests"))
    editor_mock = mock.Mock(return_value=commit_session.CommitOutcome.ABORTED)

    monkeypatch.setattr(commit_session, "open_editor_with_message", editor_mock)

    commit_session.run_commit_session(
        {},
        None,
        _fake_context(),
        generate_fn,
        edit_first=True,
    )

    captured = capsys.readouterr()
    assert "Commit aborted" in captured.out
    assert "Error:" not in captured.err


def test_eof_aborts_without_commit(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Closed stdin should abort without creating a commit."""
    generate_fn = mock.Mock(return_value=_result("feat: add tests"))
    commit_mock = mock.Mock()

    def _raise_eof(_: str) -> str:
        raise EOFError

    monkeypatch.setattr(commit_session, "commit_with_message", commit_mock)
    monkeypatch.setattr("builtins.input", _raise_eof)

    commit_session.run_commit_session({}, None, _fake_context(), generate_fn)

    commit_mock.assert_not_called()
    captured = capsys.readouterr()
    assert "Input closed" in captured.err


def test_regenerate_replaces_draft_before_accept(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Regenerate should fetch a new draft and commit that one when accepted."""
    generate_fn = mock.Mock(
        side_effect=[_result("feat: first draft"), _result("feat: regenerated draft")]
    )
    commit_mock = mock.Mock()
    choices = iter(["r", "a"])

    monkeypatch.setattr(commit_session, "commit_with_message", commit_mock)
    monkeypatch.setattr("builtins.input", lambda _: next(choices))

    commit_session.run_commit_session({}, None, _fake_context(), generate_fn)

    assert generate_fn.call_count == 2
    commit_mock.assert_called_once_with("feat: regenerated draft")
    captured = capsys.readouterr()
    assert "Regenerating commit message" in captured.out


def test_quit_exits_without_commit(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Quit should leave the repository untouched."""
    generate_fn = mock.Mock(return_value=_result("feat: add tests"))
    commit_mock = mock.Mock()

    monkeypatch.setattr(commit_session, "commit_with_message", commit_mock)
    monkeypatch.setattr("builtins.input", lambda _: "q")

    commit_session.run_commit_session({}, None, _fake_context(), generate_fn)

    commit_mock.assert_not_called()
    captured = capsys.readouterr()
    assert "Commit aborted" in captured.out


def test_invalid_choice_reprompts(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Invalid actions should show guidance and continue prompting."""
    generate_fn = mock.Mock(return_value=_result("feat: add tests"))
    choices = iter(["nope", "q"])

    monkeypatch.setattr("builtins.input", lambda _: next(choices))

    commit_session.run_commit_session({}, None, _fake_context(), generate_fn)

    captured = capsys.readouterr()
    assert "Invalid choice" in captured.out
    assert "a, e, r, or q" in captured.out
    assert captured.out.count("Draft commit message") == 1


def test_x_is_invalid_and_reprompts(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The visible quit action is q, not x."""
    generate_fn = mock.Mock(return_value=_result("feat: add tests"))
    choices = iter(["x", "q"])

    monkeypatch.setattr("builtins.input", lambda _: next(choices))

    commit_session.run_commit_session({}, None, _fake_context(), generate_fn)

    captured = capsys.readouterr()
    assert "Invalid choice" in captured.out
    assert "Commit aborted" in captured.out


def test_edit_blank_message_aborts(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Blank edited messages should be treated as intentional aborts."""
    generate_fn = mock.Mock(return_value=_result("feat: add tests"))
    editor_mock = mock.Mock(return_value=commit_session.CommitOutcome.ABORTED)

    monkeypatch.setattr(commit_session, "open_editor_with_message", editor_mock)
    monkeypatch.setattr("builtins.input", lambda _: "e")

    commit_session.run_commit_session({}, None, _fake_context(), generate_fn)

    captured = capsys.readouterr()
    assert "Commit aborted" in captured.out
    assert "Error:" not in captured.err


def test_accept_failure_prints_git_output_without_error_wrapper(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Interactive git failures should preserve git output without subprocess text."""
    generate_fn = mock.Mock(return_value=_result("feat: add tests"))
    commit_mock = mock.Mock(
        side_effect=subprocess.CalledProcessError(
            1,
            ["git", "commit"],
            stderr="nothing to commit",
        )
    )

    monkeypatch.setattr(commit_session, "commit_with_message", commit_mock)
    monkeypatch.setattr("builtins.input", lambda _: "a")

    with pytest.raises(commit_session.typer.Exit) as exc_info:
        commit_session.run_commit_session({}, None, _fake_context(), generate_fn)

    captured = capsys.readouterr()
    assert exc_info.value.exit_code == 1
    assert "nothing to commit" in captured.err
    assert "Error:" not in captured.err
    assert "Command '[" not in captured.err
