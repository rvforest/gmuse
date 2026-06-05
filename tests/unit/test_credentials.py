"""Unit tests for gmuse.credentials."""

from __future__ import annotations

import sys
from unittest import mock

import pytest

from gmuse import credentials
from gmuse.credentials import BackendStatus
from gmuse.exceptions import CredentialLookupTimeout


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


class TestMaskingAndNormalization:
    def test_mask_secret_and_normalize_env_value(self) -> None:
        assert credentials.normalize_env_value("   ") is None
        assert credentials.normalize_env_value("  secret  ") == "secret"
        assert credentials.mask_secret("short") == "******"
        assert credentials.mask_secret("12345678") == "******5678"


class TestManagedIndex:
    def test_managed_index_round_trip(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_memory_keyring(monkeypatch)

        credentials.write_managed_variables({"B", "A"})
        assert credentials.get_managed_variables() == {"A", "B"}

        credentials.add_managed_variable("C")
        assert credentials.get_managed_variables() == {"A", "B", "C"}

        credentials.remove_managed_variable("B")
        assert credentials.get_managed_variables() == {"A", "C"}

    def test_credential_exists_suppresses_noisy_missing_entry_stderr(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(credentials, "get_backend_status", _secure_backend_status)

        def get_password(service_name: str, username: str) -> str | None:
            sys.stderr.write(
                f"Error: python-keyring/{service_name}/{username} is not in the password store.\n"
            )
            return None

        monkeypatch.setattr(credentials.keyring, "get_password", get_password)

        assert credentials.credential_exists("OPENAI_API_KEY") is False
        assert capsys.readouterr().err == ""


class TestResolution:
    def test_env_falls_back_to_keyring_when_blank(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_memory_keyring(monkeypatch)
        monkeypatch.setenv("OPENAI_API_KEY", "   ")

        credentials.keyring.set_password(
            credentials.SERVICE_NAME, "OPENAI_API_KEY", "stored-secret"
        )

        resolution = credentials.resolve_credential("OPENAI_API_KEY")

        assert resolution.source == "keyring"
        assert resolution.raw_value == "stored-secret"
        assert resolution.masked_value is not None
        assert resolution.masked_value.endswith("cret")
        assert "stored-secret" not in resolution.masked_value

    def test_env_value_wins_over_keyring(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_memory_keyring(monkeypatch)
        monkeypatch.setenv("OPENAI_API_KEY", "env-secret")

        credentials.keyring.set_password(
            credentials.SERVICE_NAME, "OPENAI_API_KEY", "stored-secret"
        )

        resolution = credentials.resolve_credential("OPENAI_API_KEY")

        assert resolution.source == "env"
        assert resolution.raw_value == "env-secret"
        assert resolution.masked_value == "******cret"

    def test_provider_detection_uses_keyring_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_memory_keyring(monkeypatch)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GMUSE_MODEL", raising=False)

        credentials.keyring.set_password(
            credentials.SERVICE_NAME, "OPENAI_API_KEY", "stored-secret"
        )

        assert credentials.detect_provider_from_credentials() == "openai"

    def test_completion_timeout_is_reported(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            credentials,
            "_read_keyring_value",
            mock.Mock(side_effect=CredentialLookupTimeout("timed out")),
        )

        resolution = credentials.resolve_credential(
            "OPENAI_API_KEY",
            completion_timeout=0.2,
            managed_index=set(),
        )

        assert resolution.source == "timeout"


class TestBackendStatus:
    def test_fail_backend_is_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            credentials.keyring,
            "get_keyring",
            lambda: _backend_with_module("keyring.backends.fail"),
        )

        status = credentials.get_backend_status()

        assert status.is_available is False
        assert status.is_secure is False

    def test_alt_backend_is_insecure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            credentials.keyring,
            "get_keyring",
            lambda: _backend_with_module("keyrings.alt.file"),
        )

        status = credentials.get_backend_status()

        assert status.is_available is True
        assert status.is_secure is False
