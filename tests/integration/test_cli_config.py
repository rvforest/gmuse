"""Integration tests for `gmuse config` commands."""

from __future__ import annotations

import builtins
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Generator
from unittest import mock

import pytest
from typer.testing import CliRunner

import gmuse.config as gmuse_config
from gmuse.cli.main import app

runner = CliRunner()


@pytest.fixture
def git_repo() -> Generator[Path, None, None]:
    """Create a temporary git repository for CLI config integration tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path


@pytest.fixture
def git_repo_with_history(git_repo: Path) -> Path:
    """Create a git repository with initial commit history."""
    test_file = git_repo / "README.md"
    test_file.write_text("# Test Project\n")

    subprocess.run(
        ["git", "add", "README.md"], cwd=git_repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=git_repo,
        check=True,
        capture_output=True,
    )

    return git_repo


def _stage_file(repo: Path, filename: str, content: str) -> None:
    """Stage a file in the repository."""
    file_path = repo / filename
    file_path.write_text(content)
    subprocess.run(["git", "add", filename], cwd=repo, check=True, capture_output=True)


def _config_path(xdg_home: Path) -> Path:
    return xdg_home / "gmuse" / "config.toml"


def test_config_view_no_config_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 0
    assert str(_config_path(tmp_path)) in result.stdout
    assert "No global configuration file found." in result.stdout
    assert "--- Effective Configuration ---" in result.stdout


def test_config_view_existing_config_file_shows_contents_and_merged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        'model = "gpt-4o-mini"\nformat = "conventional"\n', encoding="utf-8"
    )

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 0
    assert "--- File Contents ---" in result.stdout
    assert 'model = "gpt-4o-mini"' in result.stdout
    assert "--- Effective Configuration ---" in result.stdout
    assert "model" in result.stdout
    assert "config file" in result.stdout


def test_config_view_invalid_toml_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("invalid toml [[[\n", encoding="utf-8")

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 1
    assert "Error: Invalid TOML syntax" in result.stderr


def test_config_view_unreadable_file_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('model = "gpt-4"\n', encoding="utf-8")

    # Simulate permission error for both raw-view and tomllib load.
    original_read_text = Path.read_text

    def fake_read_text(self: Path, *args, **kwargs):  # type: ignore[no-untyped-def]
        if self == config_path:
            raise PermissionError("Permission denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    original_open = builtins.open

    def fake_open(file, mode="r", *args, **kwargs):  # type: ignore[no-untyped-def]
        if Path(file) == config_path and "r" in mode:
            raise PermissionError("Permission denied")
        return original_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 1
    assert "Error: Cannot read config file" in result.stderr


def test_config_set_creates_directories_and_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "set", "format", "conventional"])

    assert result.exit_code == 0
    assert _config_path(tmp_path).exists()
    assert "Set 'format'" in result.stdout


def test_config_set_then_view_persists_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    set_result = runner.invoke(app, ["config", "set", "history_depth", "15"])
    assert set_result.exit_code == 0

    view_result = runner.invoke(app, ["config", "view"])
    assert view_result.exit_code == 0
    assert "history_depth = 15" in view_result.stdout


def test_config_set_unknown_key_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "set", "unknown_key", "value"])

    assert result.exit_code == 1
    assert "Unknown configuration key" in result.stderr


def test_config_set_invalid_value_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    result = runner.invoke(app, ["config", "set", "history_depth", "100"])

    assert result.exit_code == 1
    assert "history_depth must be between" in result.stderr
    assert "Allowed range: 0-50" in result.stderr


def test_config_set_unwritable_file_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    # Ensure the directory exists; then force writes to fail.
    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    def fake_replace(src, dst):  # type: ignore[no-untyped-def]
        raise PermissionError("Permission denied")

    monkeypatch.setattr(gmuse_config.os, "replace", fake_replace)

    result = runner.invoke(app, ["config", "set", "format", "conventional"])

    assert result.exit_code == 1
    assert "Error: Cannot write config file" in result.stderr


def test_config_view_highlights_env_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("GMUSE_INCLUDE_BRANCH", "true")

    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("include_branch = false\n", encoding="utf-8")

    result = runner.invoke(app, ["config", "view"])

    assert result.exit_code == 0
    assert "⚠ overrides file" in result.stdout


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="Platform-specific permission semantics"
)
def test_config_set_preserves_unrelated_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        '# comment\n[section]\nother = 1\nformat = "freeform"\n',
        encoding="utf-8",
    )

    set_result = runner.invoke(app, ["config", "set", "format", "conventional"])
    assert set_result.exit_code == 0

    text = config_path.read_text(encoding="utf-8")
    assert "[section]" in text
    assert "other = 1" in text


def test_msg_uses_backend_from_config_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    git_repo_with_history: Path,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        'backend = "anthropic"\nmodel = "claude-haiku-4-5"\n',
        encoding="utf-8",
    )

    _stage_file(git_repo_with_history, "test.py", "test content")

    with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
        mock_client = mock.Mock()
        mock_client.generate.return_value = "Update test file"
        mock_client_class.return_value = mock_client

        with mock.patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}, clear=False
        ):
            old_cwd = os.getcwd()
            os.chdir(git_repo_with_history)
            try:
                result = runner.invoke(app, ["msg"])
            finally:
                os.chdir(old_cwd)

        assert result.exit_code == 0
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs.get("backend") == "anthropic"
        assert call_kwargs.get("model") == "claude-haiku-4-5"


def test_msg_backend_flag_overrides_env_and_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    git_repo_with_history: Path,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    config_path = _config_path(tmp_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('backend = "openai"\n', encoding="utf-8")

    _stage_file(git_repo_with_history, "test.py", "test content")

    with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
        mock_client = mock.Mock()
        mock_client.generate.return_value = "Update test file"
        mock_client_class.return_value = mock_client

        with mock.patch.dict(
            os.environ,
            {"GMUSE_BACKEND": "anthropic", "COHERE_API_KEY": "test"},
            clear=False,
        ):
            old_cwd = os.getcwd()
            os.chdir(git_repo_with_history)
            try:
                result = runner.invoke(
                    app,
                    ["msg", "--backend", "cohere", "--model", "command-light"],
                )
            finally:
                os.chdir(old_cwd)

        assert result.exit_code == 0
        call_kwargs = mock_client_class.call_args[1]
        assert call_kwargs.get("backend") == "cohere"
        assert call_kwargs.get("model") == "command-light"


def test_msg_backend_model_mismatch_fails_before_request(
    git_repo_with_history: Path,
) -> None:
    _stage_file(git_repo_with_history, "test.py", "test content")

    with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
        with mock.patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}, clear=False
        ):
            old_cwd = os.getcwd()
            os.chdir(git_repo_with_history)
            try:
                result = runner.invoke(
                    app,
                    ["msg", "--backend", "anthropic", "--model", "gpt-4"],
                )
            finally:
                os.chdir(old_cwd)

        assert result.exit_code == 2
        assert "cannot serve model" in result.stderr
        mock_client_class.assert_not_called()


def test_msg_backend_missing_credentials_fails_before_request(
    git_repo_with_history: Path,
) -> None:
    _stage_file(git_repo_with_history, "test.py", "test content")

    with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
        with mock.patch.dict(os.environ, {}, clear=True):
            old_cwd = os.getcwd()
            os.chdir(git_repo_with_history)
            try:
                result = runner.invoke(
                    app,
                    ["msg", "--backend", "anthropic", "--model", "claude-haiku-4-5"],
                )
            finally:
                os.chdir(old_cwd)

        assert result.exit_code == 2
        assert "missing credentials" in result.stderr
        mock_client_class.assert_not_called()
