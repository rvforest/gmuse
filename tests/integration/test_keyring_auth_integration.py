"""Integration coverage for gmuse auth and keyring-backed message generation."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest import mock

import pytest
from typer.testing import CliRunner

from gmuse import credentials
from gmuse.cli.main import app
from gmuse.credentials import BackendStatus

runner = CliRunner()


def _secure_backend_status() -> BackendStatus:
    return BackendStatus(
        backend_name="SecretServiceKeyring",
        backend_module="keyring.backends.secretservice",
        is_available=True,
        is_secure=True,
        failure_reason=None,
    )


def _install_memory_keyring(
    monkeypatch: pytest.MonkeyPatch,
) -> dict[tuple[str, str], str]:
    store: dict[tuple[str, str], str] = {}

    monkeypatch.setattr(credentials, "get_backend_status", _secure_backend_status)
    monkeypatch.setattr(
        credentials.keyring,
        "set_password",
        lambda service_name, username, password: store.__setitem__(
            (service_name, username), password
        ),
    )
    monkeypatch.setattr(
        credentials.keyring,
        "get_password",
        lambda service_name, username: store.get((service_name, username)),
    )
    monkeypatch.setattr(
        credentials.keyring,
        "delete_password",
        lambda service_name, username: store.pop((service_name, username), None),
    )
    return store


def _backend_with_module(module_name: str) -> object:
    backend_type = type("Backend", (), {})
    backend_type.__module__ = module_name
    return backend_type()


def test_auth_set_then_msg_uses_keyring(
    git_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _install_memory_keyring(monkeypatch)

    staged_file = git_repo / "feature.py"
    staged_file.write_text("def hello():\n    return 'Hello'\n")
    subprocess.run(
        ["git", "add", "feature.py"], cwd=git_repo, check=True, capture_output=True
    )

    with mock.patch("gmuse.commit.LLMClient") as mock_client_class:
        mock_client = mock.Mock()
        mock_client.generate.return_value = "feat: add hello"
        mock_client_class.return_value = mock_client

        set_result = runner.invoke(
            app,
            ["auth", "set", "OPENAI_API_KEY"],
            input="sk-test-secret\n",
            catch_exceptions=False,
            env={**os.environ, "TERM": "dumb"},
        )
        assert set_result.exit_code == 0
        assert store[(credentials.SERVICE_NAME, "OPENAI_API_KEY")] == "sk-test-secret"

        status_result = runner.invoke(
            app,
            ["auth", "status"],
            catch_exceptions=False,
            env={**os.environ, "TERM": "dumb"},
        )
        assert status_result.exit_code == 0
        assert "OPENAI_API_KEY" in status_result.stdout
        assert "sk-test-secret" not in status_result.stdout

        old_cwd = os.getcwd()
        os.chdir(git_repo)
        try:
            with mock.patch.dict(os.environ, {}, clear=True):
                msg_result = runner.invoke(app, ["msg"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)

        assert msg_result.exit_code == 0
        assert "feat: add hello" in msg_result.stdout

        remove_result = runner.invoke(
            app,
            ["auth", "remove", "OPENAI_API_KEY"],
            catch_exceptions=False,
            env={**os.environ, "TERM": "dumb"},
        )
        assert remove_result.exit_code == 0
        assert (credentials.SERVICE_NAME, "OPENAI_API_KEY") not in store


def test_auth_set_rejects_insecure_backend_before_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        credentials.keyring,
        "get_keyring",
        lambda: _backend_with_module("keyrings.alt.file"),
    )
    prompt = mock.Mock(side_effect=AssertionError("prompt should not run"))
    monkeypatch.setattr("gmuse.cli.auth.typer.prompt", prompt)

    result = runner.invoke(
        app,
        ["auth", "set", "OPENAI_API_KEY"],
        catch_exceptions=False,
        env={**os.environ, "TERM": "dumb"},
    )

    assert result.exit_code == 1
    assert "insecure and cannot be used" in result.stderr
    prompt.assert_not_called()
