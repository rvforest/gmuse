"""Unit tests for gmuse.cli.auth."""

from __future__ import annotations

import sys
from unittest import mock

import pytest
import typer

from gmuse import credentials
from gmuse.cli import auth
from gmuse.credentials import BackendStatus


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


def test_auth_set_status_and_remove_cycle(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    store = _install_memory_keyring(monkeypatch)
    monkeypatch.setattr(auth.typer, "prompt", lambda *args, **kwargs: "sk-test-secret")

    auth.set_credential("OPENAI_API_KEY", force=True)
    output = capsys.readouterr().out
    assert "Stored OPENAI_API_KEY" in output

    assert store[(credentials.SERVICE_NAME, "OPENAI_API_KEY")] == "sk-test-secret"

    auth.status()
    output = capsys.readouterr().out
    assert "Credential status for gmuse" in output
    assert "OPENAI_API_KEY" in output
    assert "keyring" in output
    assert "sk-test-secret" not in output

    auth.remove_credential(["OPENAI_API_KEY"])
    output = capsys.readouterr().out
    assert "Removed 1 credential(s)" in output
    assert (credentials.SERVICE_NAME, "OPENAI_API_KEY") not in store


def test_auth_status_provider_uses_litellm_validation(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    store = _install_memory_keyring(monkeypatch)
    store[(credentials.SERVICE_NAME, "OPENAI_API_KEY")] = "sk-test-secret"
    store[(credentials.SERVICE_NAME, credentials.INDEX_USERNAME)] = "OPENAI_API_KEY"

    import litellm

    monkeypatch.setattr(
        litellm,
        "validate_environment",
        lambda model: {
            "keys_in_environment": False,
            "missing_keys": ["OPENAI_API_KEY"],
        },
    )

    auth.status("openai")
    output = capsys.readouterr().out
    assert "Credential status for provider: openai" in output
    assert "OPENAI_API_KEY" in output


def test_auth_set_rejects_insecure_backend_before_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        credentials.keyring,
        "get_keyring",
        lambda: _backend_with_module("keyrings.alt.file"),
    )
    prompt = mock.Mock(side_effect=AssertionError("prompt should not run"))
    monkeypatch.setattr(auth.typer, "prompt", prompt)

    with pytest.raises(typer.Exit) as excinfo:
        auth.set_credential("OPENAI_API_KEY", force=True)

    assert excinfo.value.exit_code == 1
    prompt.assert_not_called()


def test_auth_set_suppresses_noisy_missing_entry_stderr(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    store: dict[tuple[str, str], str] = {}

    monkeypatch.setattr(credentials, "get_backend_status", _secure_backend_status)

    def get_password(service_name: str, username: str) -> str | None:
        value = store.get((service_name, username))
        if value is None:
            sys.stderr.write(
                f"Error: python-keyring/{service_name}/{username} is not in the password store.\n"
            )
        return value

    monkeypatch.setattr(credentials.keyring, "get_password", get_password)
    monkeypatch.setattr(
        credentials.keyring,
        "set_password",
        lambda service_name, username, password: store.__setitem__(
            (service_name, username), password
        ),
    )
    monkeypatch.setattr(auth.typer, "prompt", lambda *args, **kwargs: "sk-test-secret")

    auth.set_credential("OPENAI_API_KEY", force=False)

    captured = capsys.readouterr()
    assert "Stored OPENAI_API_KEY" in captured.out
    assert captured.err == ""
    assert store[(credentials.SERVICE_NAME, "OPENAI_API_KEY")] == "sk-test-secret"
