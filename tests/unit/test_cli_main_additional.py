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
        main, "merge_config", lambda **_: {"model": "m"}
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


def test_load_config_calls_load_env_merge_and_validate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_load_config should call load_config/get_env_config/merge_config/validate_config.

    This specifically covers the internal line that loads the config file.
    """

    called: dict[str, Any] = {
        "load_config": False,
        "get_env_config": False,
        "validate_config": False,
        "cli_args": None,
        "config_file": None,
        "env_vars": None,
    }

    def fake_load_config() -> dict[str, Any]:
        called["load_config"] = True
        return {"model": "from-file"}

    def fake_get_env_config() -> dict[str, Any]:
        called["get_env_config"] = True
        return {"GMUSE_MODEL": "from-env"}

    def fake_merge_config(*, cli_args, config_file, env_vars):
        called["cli_args"] = dict(cli_args)
        called["config_file"] = dict(config_file)
        called["env_vars"] = dict(env_vars)
        return {"model": cli_args.get("model") or "merged"}

    def fake_validate_config(_: dict[str, Any]) -> None:
        called["validate_config"] = True

    monkeypatch.setattr(main, "load_config", fake_load_config)
    monkeypatch.setattr(main, "get_env_config", fake_get_env_config)
    monkeypatch.setattr(main, "merge_config", fake_merge_config)
    monkeypatch.setattr(main, "validate_config", fake_validate_config)

    config = main._load_config(model="cli-model", copy=True, include_branch=True)

    assert called["load_config"] is True
    assert called["get_env_config"] is True
    assert called["validate_config"] is True
    assert called["cli_args"] == {
        "model": "cli-model",
        "copy_to_clipboard": True,
        "include_branch": True,
    }
    assert called["config_file"] == {"model": "from-file"}
    assert called["env_vars"] == {"GMUSE_MODEL": "from-env"}
    assert config["model"] == "cli-model"
