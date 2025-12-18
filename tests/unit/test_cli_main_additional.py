"""Additional unit tests for gmuse.cli.main.

These target error branches and small helpers that are hard to hit via
higher-level integration tests.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest import mock
from typing import Any

import pytest
import typer

from gmuse import __version__
from gmuse.cli import main
from gmuse.exceptions import (
    ConfigError,
    InvalidMessageError,
    NoStagedChangesError,
    NotAGitRepositoryError,
)


def _fake_context(*, truncated: bool = False):
    fake_diff = mock.Mock(truncated=truncated)
    return mock.Mock(diff=fake_diff, diff_was_truncated=truncated)


def test_version_callback_prints_and_exits(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(typer.Exit) as excinfo:
        main.version_callback(True)

    assert excinfo.value.exit_code == 0
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_info_works_when_config_load_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        main, "load_config", lambda: (_ for _ in ()).throw(Exception("boom"))
    )
    monkeypatch.setattr(main, "get_env_config", lambda: {"GMUSE_MODEL": "x"})

    def fake_merge_config(*, cli_args, config_file, env_vars):  # noqa: ARG001
        return {"model": "gpt-4.1", "provider": "openai"}

    monkeypatch.setattr(main, "merge_config", fake_merge_config)

    # Ensure detect_provider exists and returns something deterministic
    fake_llm = ModuleType("gmuse.llm")
    setattr(fake_llm, "detect_provider", lambda: "openai")
    monkeypatch.setitem(sys.modules, "gmuse.llm", fake_llm)

    main.info()

    captured = capsys.readouterr()
    assert "Resolved model:" in captured.out
    assert "gpt-4.1" in captured.out
    assert "Detected provider heuristics: openai" in captured.out


def test_info_handles_detect_provider_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(main, "load_config", lambda: {})
    monkeypatch.setattr(main, "get_env_config", lambda: {})
    monkeypatch.setattr(
        main, "merge_config", lambda **_: {"model": "m", "provider": None}
    )

    fake_llm = ModuleType("gmuse.llm")

    def _boom():
        raise RuntimeError("nope")

    setattr(fake_llm, "detect_provider", _boom)
    monkeypatch.setitem(sys.modules, "gmuse.llm", fake_llm)

    main.info()

    captured = capsys.readouterr()
    assert "Detected provider heuristics: None" in captured.out


@pytest.mark.parametrize(
    ("exc", "exit_code", "expected_hint"),
    [
        (ConfigError("bad"), 1, None),
        (NotAGitRepositoryError("no repo"), 1, "git init"),
        (NoStagedChangesError("no changes"), 1, "git add"),
        (InvalidMessageError("invalid"), 2, "Try again"),
    ],
)
def test_msg_error_branches_exit_with_expected_codes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    exc: Exception,
    exit_code: int,
    expected_hint: str | None,
) -> None:
    monkeypatch.setattr(main, "_load_config", lambda **_: {"copy_to_clipboard": False})

    # Raise the exception from the earliest sensible point.
    monkeypatch.setattr(main, "gather_context", lambda **_: (_ for _ in ()).throw(exc))

    with pytest.raises(typer.Exit) as excinfo:
        main.msg()

    assert excinfo.value.exit_code == exit_code

    captured = capsys.readouterr()
    assert "Error:" in captured.err
    if expected_hint is not None:
        assert expected_hint.lower() in captured.err.lower()


def test_msg_keyboard_interrupt_exits_130(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(main, "_load_config", lambda **_: {"copy_to_clipboard": False})
    monkeypatch.setattr(
        main, "gather_context", lambda **_: (_ for _ in ()).throw(KeyboardInterrupt())
    )

    with pytest.raises(typer.Exit) as excinfo:
        main.msg()

    assert excinfo.value.exit_code == 130
    captured = capsys.readouterr()
    assert "Interrupted by user" in captured.err


def test_copy_to_clipboard_generic_exception_warns(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Provide a fake pyperclip module that fails at runtime.
    fake_pyperclip = ModuleType("pyperclip")

    def _fail(_: str) -> None:
        raise RuntimeError("clipboard locked")

    setattr(fake_pyperclip, "copy", _fail)

    monkeypatch.setitem(sys.modules, "pyperclip", fake_pyperclip)

    main._copy_to_clipboard("hello")

    captured = capsys.readouterr()
    assert "could not copy" in captured.err.lower()
