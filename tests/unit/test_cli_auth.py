"""Unit tests for gmuse.cli.auth."""

from __future__ import annotations

import sys
from unittest import mock

import pytest
import typer

from gmuse import credentials
from gmuse.cli import auth
from gmuse.credentials import BackendStatus
from gmuse.exceptions import (
    CredentialError,
    InsecureKeyringError,
    KeyringUnavailableError,
)


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


def test_auth_helpers_print_hints_and_empty_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit):
        auth._exit_with_error("boom", hint="use this")

    output = capsys.readouterr()
    assert "Error: boom" in output.err
    assert "use this" in output.err

    auth._print_table("Credential status", [])
    output = capsys.readouterr()
    assert "No stored credentials found." in output.out


def test_auth_set_rejects_blank_variable_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompt = mock.Mock()
    monkeypatch.setattr(auth.typer, "prompt", prompt)

    with pytest.raises(typer.Exit):
        auth.set_credential("   ", force=True)

    prompt.assert_not_called()


def test_auth_set_handles_unavailable_backend(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        auth,
        "ensure_secure_backend",
        mock.Mock(side_effect=KeyringUnavailableError("unavailable")),
    )
    prompt = mock.Mock()
    monkeypatch.setattr(auth.typer, "prompt", prompt)

    with pytest.raises(typer.Exit):
        auth.set_credential("OPENAI_API_KEY", force=True)

    prompt.assert_not_called()
    assert "Error: unavailable" in capsys.readouterr().err


def test_auth_set_decline_overwrite_and_abort_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth, "ensure_secure_backend", lambda: None)
    monkeypatch.setattr(auth, "credential_exists", lambda variable_name: True)
    monkeypatch.setattr(auth.typer, "confirm", lambda *args, **kwargs: False)

    with pytest.raises(typer.Exit):
        auth.set_credential("OPENAI_API_KEY", force=False)

    monkeypatch.setattr(auth, "credential_exists", lambda variable_name: False)
    monkeypatch.setattr(auth.typer, "prompt", mock.Mock(side_effect=EOFError()))

    with pytest.raises(typer.Exit):
        auth.set_credential("OPENAI_API_KEY", force=True)


def test_auth_set_confirm_abort_and_blank_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth, "ensure_secure_backend", lambda: None)
    monkeypatch.setattr(auth, "credential_exists", lambda variable_name: True)
    monkeypatch.setattr(auth.typer, "confirm", mock.Mock(side_effect=typer.Abort()))

    with pytest.raises(typer.Exit):
        auth.set_credential("OPENAI_API_KEY", force=False)

    monkeypatch.setattr(auth, "credential_exists", lambda variable_name: False)
    monkeypatch.setattr(auth.typer, "prompt", lambda *args, **kwargs: "   ")

    with pytest.raises(typer.Exit):
        auth.set_credential("OPENAI_API_KEY", force=True)


def test_auth_set_reports_store_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth, "ensure_secure_backend", lambda: None)
    monkeypatch.setattr(auth.typer, "prompt", lambda *args, **kwargs: "sk-test")
    monkeypatch.setattr(
        auth,
        "store_credential",
        mock.Mock(side_effect=CredentialError("boom")),
    )

    with pytest.raises(typer.Exit):
        auth.set_credential("OPENAI_API_KEY", force=True)


def test_auth_status_provider_validation_failure_and_missing_key_append(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import litellm

    monkeypatch.setattr(
        litellm,
        "validate_environment",
        mock.Mock(return_value={"missing_keys": [123, "EXTRA_API_KEY"]}),
    )
    monkeypatch.setattr(
        auth, "get_provider_credential_variables", lambda provider: ("OPENAI_API_KEY",)
    )
    monkeypatch.setattr(auth, "get_managed_variables", lambda: set())
    monkeypatch.setattr(
        auth,
        "resolve_credential",
        lambda variable_name, managed_index=None: mock.Mock(
            source="missing", masked_value=None
        ),
    )

    auth.status("openai")

    output = capsys.readouterr().out
    assert "Credential status for provider: openai" in output
    assert "EXTRA_API_KEY" in output


def test_auth_status_validation_error_exits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import litellm

    monkeypatch.setattr(
        litellm,
        "validate_environment",
        mock.Mock(side_effect=Exception("boom")),
    )

    with pytest.raises(typer.Exit):
        auth.status("openai")


def test_auth_remove_empty_and_delete_error_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(typer.Exit):
        auth.remove_credential([])

    monkeypatch.setattr(
        auth,
        "ensure_secure_backend",
        mock.Mock(side_effect=KeyringUnavailableError("unavailable")),
    )

    with pytest.raises(typer.Exit):
        auth.remove_credential(["OPENAI_API_KEY"])

    monkeypatch.setattr(auth, "ensure_secure_backend", lambda: None)
    delete_mock = mock.Mock(side_effect=CredentialError("boom"))
    monkeypatch.setattr(auth, "delete_credential", delete_mock)

    with pytest.raises(typer.Exit):
        auth.remove_credential(["OPENAI_API_KEY"])


def test_auth_remove_handles_backend_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        auth,
        "ensure_secure_backend",
        mock.Mock(side_effect=KeyringUnavailableError("custom unavailable guidance")),
    )

    with pytest.raises(typer.Exit):
        auth.remove_credential(["OPENAI_API_KEY"])

    assert "Error: custom unavailable guidance" in capsys.readouterr().err


def test_auth_remove_handles_insecure_backend(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        auth,
        "ensure_secure_backend",
        mock.Mock(side_effect=InsecureKeyringError("custom insecure guidance")),
    )

    with pytest.raises(typer.Exit):
        auth.remove_credential(["OPENAI_API_KEY"])

    assert "Error: custom insecure guidance" in capsys.readouterr().err


def test_auth_remove_reports_missing_credentials(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(auth, "ensure_secure_backend", lambda: None)
    delete_mock = mock.Mock(return_value=False)
    monkeypatch.setattr(auth, "delete_credential", delete_mock)

    auth.remove_credential(["OPENAI_API_KEY"])

    output = capsys.readouterr().out
    assert "No stored credential found for OPENAI_API_KEY." in output
    assert delete_mock.call_count == 1


def test_auth_remove_skips_blank_names_and_reports_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(auth, "ensure_secure_backend", lambda: None)
    delete_mock = mock.Mock(return_value=True)
    monkeypatch.setattr(auth, "delete_credential", delete_mock)

    auth.remove_credential([" ", "OPENAI_API_KEY"])

    assert delete_mock.call_count == 1
    assert delete_mock.call_args.args == ("OPENAI_API_KEY",)
    output = capsys.readouterr().out
    assert "Removed 1 credential(s)" in output
