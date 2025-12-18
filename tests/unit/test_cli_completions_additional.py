"""Additional unit tests for gmuse.cli.completions.

These focus on status mapping and edge cases around env overrides.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, cast

import pytest
import typer

from gmuse.cli import completions
from gmuse.exceptions import LLMError, NoStagedChangesError, NotAGitRepositoryError


def _parse_stdout_json(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    captured = capsys.readouterr()
    assert captured.out.strip(), "expected JSON on stdout"
    return cast(dict[str, Any], json.loads(captured.out))


def test_completions_zsh_template_error_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        completions,
        "_load_zsh_template",
        lambda: (_ for _ in ()).throw(RuntimeError("missing")),
    )

    with pytest.raises(typer.Exit) as excinfo:
        completions.completions_zsh()

    assert excinfo.value.exit_code == 1
    captured = capsys.readouterr()
    assert "missing" in captured.err


def test_completions_run_invalid_env_timeout_does_not_override(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("GMUSE_COMPLETIONS_TIMEOUT", "not-a-float")

    captured_cli_args: dict[str, object] = {}

    def fake_merge_config(*, cli_args, config_file, env_vars):  # noqa: ARG001
        captured_cli_args.update(cli_args)
        return {"timeout": cli_args["timeout"]}

    monkeypatch.setattr(
        completions, "load_config", lambda: (_ for _ in ()).throw(Exception("no file"))
    )
    monkeypatch.setattr(completions, "get_env_config", lambda: {})
    monkeypatch.setattr(completions, "merge_config", fake_merge_config)
    monkeypatch.setattr(
        completions, "get_staged_diff", lambda: SimpleNamespace(truncated=False)
    )

    class _Result:
        message = "ok"

    monkeypatch.setattr(completions, "generate_message", lambda **_: _Result())

    completions.completions_run_command(
        shell="zsh", for_command="git commit -m", timeout=1.5
    )

    assert captured_cli_args["timeout"] == 1.5

    output = _parse_stdout_json(capsys)
    assert output["status"] == "ok"


def test_completions_run_not_a_git_repo_returns_error_status(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        completions,
        "get_staged_diff",
        lambda: (_ for _ in ()).throw(NotAGitRepositoryError("no repo")),
    )

    completions.completions_run_command(
        shell="zsh", for_command="git commit -m", timeout=3.0
    )

    output = _parse_stdout_json(capsys)
    assert output["status"] == "error"
    assert output["suggestion"] == ""
    metadata = cast(dict[str, Any], output["metadata"])
    assert "Not a git repository" in str(metadata.get("error"))


def test_completions_run_no_staged_changes_returns_status(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        completions,
        "get_staged_diff",
        lambda: (_ for _ in ()).throw(NoStagedChangesError("none")),
    )

    completions.completions_run_command(
        shell="zsh", for_command="git commit -m", timeout=3.0
    )

    output = _parse_stdout_json(capsys)
    assert output["status"] == "no_staged_changes"
    assert output["suggestion"] == ""


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        ("Authentication failed: API key missing", "offline"),
        ("Request timeout", "timeout"),
        ("Other failure", "error"),
    ],
)
def test_completions_run_llmerror_status_mapping(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: str,
    expected: str,
) -> None:
    monkeypatch.setattr(
        completions, "get_staged_diff", lambda: SimpleNamespace(truncated=False)
    )
    monkeypatch.setattr(completions, "load_config", lambda: {})
    monkeypatch.setattr(completions, "get_env_config", lambda: {})
    monkeypatch.setattr(completions, "merge_config", lambda **_: {})

    def _raise(**_):
        raise LLMError(error)

    monkeypatch.setattr(completions, "generate_message", _raise)

    completions.completions_run_command(
        shell="zsh", for_command="git commit -m", timeout=3.0
    )

    output = _parse_stdout_json(capsys)
    assert output["status"] == expected
    assert output["suggestion"] == ""


def test_completions_run_unexpected_exception_is_caught(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        completions,
        "get_staged_diff",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    completions.completions_run_command(
        shell="zsh", for_command="git commit -m", timeout=3.0
    )

    output = _parse_stdout_json(capsys)
    assert output["status"] == "error"
    metadata = cast(dict[str, Any], output["metadata"])
    assert "boom" in str(metadata.get("error"))
