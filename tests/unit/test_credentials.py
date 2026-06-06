"""Unit tests for gmuse.credentials."""

from __future__ import annotations

import sys
from unittest import mock

import pytest
from keyring.errors import KeyringError, NoKeyringError

from gmuse import credentials
from gmuse.credentials import BackendStatus
from gmuse.exceptions import (
    CredentialLookupTimeout,
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


class TestMaskingAndNormalization:
    def test_mask_secret_and_normalize_env_value(self) -> None:
        assert credentials.normalize_env_value("   ") is None
        assert credentials.normalize_env_value("  secret  ") == "secret"
        assert credentials.mask_secret(None) is None
        assert credentials.mask_secret("short") == "*****"
        assert credentials.mask_secret("12345678") == "********"
        assert credentials.mask_secret("123456789012") == "******9012"


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
        assert resolution.masked_value == "**********"

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
    def test_backend_status_no_keyring(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_no_keyring() -> object:
            raise NoKeyringError()

        monkeypatch.setattr(credentials.keyring, "get_keyring", raise_no_keyring)

        status = credentials.get_backend_status()

        assert status.backend_name == "unavailable"
        assert status.backend_module == "keyring.backends.fail"
        assert status.is_available is False
        assert status.is_secure is False

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

    def test_null_backend_is_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            credentials.keyring,
            "get_keyring",
            lambda: _backend_with_module("keyring.backends.null"),
        )

        status = credentials.get_backend_status()

        assert status.is_available is False
        assert status.is_secure is False

    def test_secure_backend_is_available_and_secure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            credentials.keyring,
            "get_keyring",
            lambda: _backend_with_module("keyring.backends.secretservice"),
        )

        status = credentials.get_backend_status()

        assert status.is_available is True
        assert status.is_secure is True


class TestKeyringTimeoutsAndErrors:
    def test_ensure_secure_backend_raises_for_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            credentials,
            "get_backend_status",
            lambda: BackendStatus(
                backend_name="unavailable",
                backend_module="keyring.backends.fail",
                is_available=False,
                is_secure=False,
                failure_reason=None,
            ),
        )

        with pytest.raises(KeyringUnavailableError):
            credentials.ensure_secure_backend()

    def test_ensure_secure_backend_raises_for_insecure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            credentials,
            "get_backend_status",
            lambda: BackendStatus(
                backend_name="NullKeyring",
                backend_module="keyring.backends.null",
                is_available=True,
                is_secure=False,
                failure_reason=None,
            ),
        )

        with pytest.raises(InsecureKeyringError):
            credentials.ensure_secure_backend()

    def test_read_keyring_value_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class NeverDoneEvent:
            def wait(self, timeout: float) -> bool:
                return False

            def set(self) -> None:
                pass

        class NoOpThread:
            def __init__(self, target: object, daemon: bool) -> None:
                self.target = target
                self.daemon = daemon

            def start(self) -> None:
                pass

        monkeypatch.setattr(credentials.threading, "Event", NeverDoneEvent)
        monkeypatch.setattr(credentials.threading, "Thread", NoOpThread)

        with pytest.raises(CredentialLookupTimeout):
            credentials._read_keyring_value("OPENAI_API_KEY", timeout=0.01)

    def test_read_keyring_value_returns_none_when_worker_errors(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            credentials.keyring,
            "get_password",
            mock.Mock(side_effect=KeyringError("boom")),
        )

        assert credentials._read_keyring_value("OPENAI_API_KEY", timeout=1.0) is None

    def test_read_keyring_value_returns_value_with_timeout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = _install_memory_keyring(monkeypatch)
        store[(credentials.SERVICE_NAME, "OPENAI_API_KEY")] = "stored-secret"

        assert (
            credentials._read_keyring_value("OPENAI_API_KEY", timeout=1.0)
            == "stored-secret"
        )

    def test_read_keyring_value_without_timeout_returns_none_on_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            credentials.keyring,
            "get_password",
            mock.Mock(side_effect=KeyringError("boom")),
        )

        assert credentials._read_keyring_value("OPENAI_API_KEY") is None

    def test_write_managed_variables_ignores_delete_errors_on_empty_index(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_memory_keyring(monkeypatch)
        monkeypatch.setattr(
            credentials.keyring,
            "delete_password",
            mock.Mock(side_effect=KeyringError("missing index")),
        )

        credentials.write_managed_variables(set())

    def test_write_managed_variables_raises_on_persist_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_memory_keyring(monkeypatch)
        monkeypatch.setattr(
            credentials.keyring,
            "set_password",
            mock.Mock(side_effect=KeyringError("persist failed")),
        )

        with pytest.raises(KeyringUnavailableError):
            credentials.write_managed_variables({"OPENAI_API_KEY"})

    def test_write_managed_variables_clears_empty_index(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = _install_memory_keyring(monkeypatch)
        store[(credentials.SERVICE_NAME, credentials.INDEX_USERNAME)] = "OPENAI_API_KEY"

        credentials.write_managed_variables(set())

        assert credentials.get_managed_variables() == set()

    def test_store_credential_raises_when_keyring_write_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_memory_keyring(monkeypatch)
        monkeypatch.setattr(
            credentials.keyring,
            "set_password",
            mock.Mock(side_effect=KeyringError("boom")),
        )

        with pytest.raises(KeyringUnavailableError):
            credentials.store_credential("OPENAI_API_KEY", "secret")

    def test_store_credential_updates_managed_index(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = _install_memory_keyring(monkeypatch)

        credentials.store_credential("OPENAI_API_KEY", "secret")

        assert store[(credentials.SERVICE_NAME, "OPENAI_API_KEY")] == "secret"
        assert credentials.get_managed_variables() == {"OPENAI_API_KEY"}

    def test_delete_credential_missing_and_lookup_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_memory_keyring(monkeypatch)

        monkeypatch.setattr(
            credentials.keyring,
            "get_password",
            lambda service_name, username: None,
        )
        assert credentials.delete_credential("OPENAI_API_KEY") is False

        monkeypatch.setattr(
            credentials.keyring,
            "get_password",
            mock.Mock(side_effect=KeyringError("lookup failed")),
        )

        with pytest.raises(KeyringUnavailableError):
            credentials.delete_credential("OPENAI_API_KEY")

    def test_delete_credential_success_removes_managed_index(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = _install_memory_keyring(monkeypatch)
        store[(credentials.SERVICE_NAME, "OPENAI_API_KEY")] = "stored-secret"
        credentials.write_managed_variables({"OPENAI_API_KEY"})

        assert credentials.delete_credential("OPENAI_API_KEY") is True
        assert (credentials.SERVICE_NAME, "OPENAI_API_KEY") not in store
        assert credentials.get_managed_variables() == set()

    def test_delete_credential_raises_when_delete_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_memory_keyring(monkeypatch)

        monkeypatch.setattr(
            credentials.keyring,
            "get_password",
            lambda service_name, username: "stored-secret",
        )
        monkeypatch.setattr(
            credentials.keyring,
            "delete_password",
            mock.Mock(side_effect=KeyringError("delete failed")),
        )

        with pytest.raises(KeyringUnavailableError):
            credentials.delete_credential("OPENAI_API_KEY")

    def test_credential_exists_returns_false_on_keyring_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            credentials.keyring,
            "get_password",
            mock.Mock(side_effect=KeyringError("lookup failed")),
        )

        assert credentials.credential_exists("OPENAI_API_KEY") is False


class TestProviderResolution:
    def test_provider_variable_lookup_falls_back_for_invalid_validation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            credentials.litellm,
            "validate_environment",
            mock.Mock(side_effect=Exception("boom")),
        )
        assert credentials.get_provider_credential_variables("openai") == (
            "OPENAI_API_KEY",
        )

        monkeypatch.setattr(
            credentials.litellm,
            "validate_environment",
            mock.Mock(return_value={"missing_keys": "not-a-list"}),
        )
        assert credentials.get_provider_credential_variables("azure") == (
            "AZURE_API_KEY",
        )

        monkeypatch.setattr(
            credentials.litellm,
            "validate_environment",
            mock.Mock(return_value={"missing_keys": [" ", "GOOGLE_API_KEY", 123]}),
        )
        assert credentials.get_provider_credential_variables("gemini") == (
            "GOOGLE_API_KEY",
        )

    def test_resolve_credential_missing_when_keyring_has_no_value(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_memory_keyring(monkeypatch)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        resolution = credentials.resolve_credential("OPENAI_API_KEY")

        assert resolution.source == "missing"
        assert resolution.raw_value is None
        assert resolution.masked_value is None

    def test_resolve_provider_credential_missing_and_timeout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_memory_keyring(monkeypatch)

        missing_resolution = credentials.resolve_provider_credential("openai")
        assert missing_resolution is not None
        assert missing_resolution.source == "missing"

        assert credentials.resolve_provider_credential("unknown-provider") is None

        monkeypatch.setattr(
            credentials,
            "resolve_credential",
            lambda *args, **kwargs: credentials.CredentialResolution(
                variable_name="OPENAI_API_KEY",
                source="timeout",
                raw_value=None,
                masked_value=None,
                is_managed=False,
            ),
        )

        timeout_resolution = credentials.resolve_provider_credential("openai")
        assert timeout_resolution is not None
        assert timeout_resolution.source == "timeout"

    def test_detect_provider_from_credentials_env_and_timeout_paths(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for env_var, provider in [
            ("OPENAI_API_KEY", "openai"),
            ("ANTHROPIC_API_KEY", "anthropic"),
            ("COHERE_API_KEY", "cohere"),
            ("AZURE_API_KEY", "azure"),
            ("GEMINI_API_KEY", "gemini"),
        ]:
            monkeypatch.setenv(env_var, "stored-secret")
            assert credentials.detect_provider_from_credentials() == provider
            monkeypatch.delenv(env_var, raising=False)

        monkeypatch.setattr(
            credentials,
            "resolve_provider_credential",
            lambda provider, completion_timeout=None: credentials.CredentialResolution(
                variable_name="OPENAI_API_KEY",
                source="timeout" if provider == "openai" else "missing",
                raw_value=None,
                masked_value=None,
                is_managed=False,
            ),
        )

        with pytest.raises(CredentialLookupTimeout):
            credentials.detect_provider_from_credentials(completion_timeout=0.1)

        monkeypatch.setattr(
            credentials, "resolve_provider_credential", lambda *args, **kwargs: None
        )

        assert credentials.detect_provider_from_credentials() is None

    def test_build_backend_and_missing_credential_messages(self) -> None:
        unavailable = BackendStatus(
            backend_name="unavailable",
            backend_module="keyring.backends.fail",
            is_available=False,
            is_secure=False,
            failure_reason=None,
        )
        insecure = BackendStatus(
            backend_name="NullKeyring",
            backend_module="keyring.backends.null",
            is_available=True,
            is_secure=False,
            failure_reason="custom insecure",
        )
        secure = BackendStatus(
            backend_name="SecretServiceKeyring",
            backend_module="keyring.backends.secretservice",
            is_available=True,
            is_secure=True,
            failure_reason=None,
        )

        assert credentials.build_backend_error_message(unavailable)
        assert credentials.build_backend_error_message(insecure) == "custom insecure"
        assert credentials.build_backend_error_message(secure) == ""
        assert credentials.build_missing_credential_error("OPENAI_API_KEY")
