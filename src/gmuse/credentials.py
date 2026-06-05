"""Secure credential storage and resolution helpers for gmuse."""

from __future__ import annotations

import contextlib
import os
import threading
from dataclasses import dataclass
from typing import Callable, Final, Literal, TypeVar

import keyring
import litellm
from keyring.errors import KeyringError, NoKeyringError

from gmuse.exceptions import (
    CredentialLookupTimeout,
    InsecureKeyringError,
    KeyringUnavailableError,
    build_insecure_keyring_message,
    build_missing_credential_message,
    build_no_secure_keyring_message,
)

SERVICE_NAME: Final[str] = "gmuse"
INDEX_USERNAME: Final[str] = "__gmuse_index__"
COMPLETION_LOOKUP_TIMEOUT_SECONDS: Final[float] = 0.2
_KEYRING_STDERR_LOCK = threading.Lock()

_T = TypeVar("_T")

CredentialSource = Literal["env", "keyring", "missing", "timeout"]

_PROVIDER_CREDENTIAL_VARIABLES: Final[dict[str, tuple[str, ...]]] = {
    "openai": ("OPENAI_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "cohere": ("COHERE_API_KEY",),
    "azure": ("AZURE_API_KEY",),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
}


@dataclass(slots=True)
class CredentialResolution:
    """Represents the effective value of a credential variable."""

    variable_name: str
    source: CredentialSource
    raw_value: str | None
    masked_value: str | None
    is_managed: bool


@dataclass(slots=True)
class BackendStatus:
    """Represents the current keyring backend status."""

    backend_name: str
    backend_module: str
    is_available: bool
    is_secure: bool
    failure_reason: str | None


def normalize_env_value(value: str | None) -> str | None:
    """Treat empty and whitespace-only values as missing."""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def mask_secret(value: str | None) -> str | None:
    """Mask a credential value for safe display."""
    N_STARS = 6
    if value is None:
        return None
    if len(value) < 8:
        return "*" * N_STARS
    return f"{'*' * N_STARS}{value[-4:]}"


def _call_keyring(operation: Callable[[], _T]) -> _T:
    """Run a keyring operation without leaking backend stderr to the user."""
    with _KEYRING_STDERR_LOCK:
        with open(os.devnull, "w", encoding="utf-8") as devnull:
            with contextlib.redirect_stderr(devnull):
                return operation()


def get_backend_status() -> BackendStatus:
    """Return a normalized view of the active keyring backend."""
    try:
        backend = keyring.get_keyring()
    except NoKeyringError:
        return BackendStatus(
            backend_name="unavailable",
            backend_module="keyring.backends.fail",
            is_available=False,
            is_secure=False,
            failure_reason=build_no_secure_keyring_message(),
        )

    backend_name = backend.__class__.__name__
    backend_module = backend.__class__.__module__

    if backend_module.startswith("keyrings.alt"):
        return BackendStatus(
            backend_name=backend_name,
            backend_module=backend_module,
            is_available=True,
            is_secure=False,
            failure_reason=build_insecure_keyring_message(),
        )

    if backend_module.startswith("keyring.backends.null"):
        return BackendStatus(
            backend_name=backend_name,
            backend_module=backend_module,
            is_available=False,
            is_secure=False,
            failure_reason=build_insecure_keyring_message(),
        )

    if backend_module.startswith("keyring.backends.fail"):
        return BackendStatus(
            backend_name=backend_name,
            backend_module=backend_module,
            is_available=False,
            is_secure=False,
            failure_reason=build_no_secure_keyring_message(),
        )

    return BackendStatus(
        backend_name=backend_name,
        backend_module=backend_module,
        is_available=True,
        is_secure=True,
        failure_reason=None,
    )


def ensure_secure_backend() -> BackendStatus:
    """Validate that the active backend is both available and secure."""
    status = get_backend_status()
    if not status.is_available:
        raise KeyringUnavailableError(
            status.failure_reason or build_no_secure_keyring_message()
        )
    if not status.is_secure:
        raise InsecureKeyringError(
            status.failure_reason or build_insecure_keyring_message()
        )
    return status


def _read_keyring_value(
    variable_name: str, *, timeout: float | None = None
) -> str | None:
    """Read a keyring value, optionally bounding the lookup time."""
    if timeout is None:
        try:
            return _call_keyring(
                lambda: keyring.get_password(SERVICE_NAME, variable_name)
            )
        except (KeyringError, NoKeyringError):
            return None

    result: dict[str, object] = {}
    done = threading.Event()

    def worker() -> None:
        try:
            result["value"] = _call_keyring(
                lambda: keyring.get_password(SERVICE_NAME, variable_name)
            )
        except Exception as exc:  # noqa: BLE001
            result["error"] = exc
        finally:
            done.set()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    if not done.wait(timeout):
        raise CredentialLookupTimeout(
            f"Credential lookup for {variable_name} timed out after {timeout} seconds."
        )

    value = result.get("value")
    if isinstance(value, str):
        return value
    return None


def get_managed_variables(*, timeout: float | None = None) -> set[str]:
    """Read the managed-variable index from keyring."""
    index = _read_keyring_value(INDEX_USERNAME, timeout=timeout)
    if not index:
        return set()

    return {item.strip() for item in index.split(",") if item.strip()}


def write_managed_variables(variables: set[str]) -> None:
    """Persist the managed-variable index to keyring."""
    ensure_secure_backend()

    cleaned = sorted({variable.strip() for variable in variables if variable.strip()})
    if not cleaned:
        try:
            _call_keyring(lambda: keyring.delete_password(SERVICE_NAME, INDEX_USERNAME))
        except (KeyringError, NoKeyringError):
            return
        return

    try:
        _call_keyring(
            lambda: keyring.set_password(
                SERVICE_NAME, INDEX_USERNAME, ",".join(cleaned)
            )
        )
    except (KeyringError, NoKeyringError) as exc:
        raise KeyringUnavailableError(str(exc)) from exc


def add_managed_variable(variable_name: str) -> None:
    """Add a variable to the managed index."""
    managed = get_managed_variables()
    managed.add(variable_name)
    write_managed_variables(managed)


def remove_managed_variable(variable_name: str) -> None:
    """Remove a variable from the managed index."""
    managed = get_managed_variables()
    managed.discard(variable_name)
    write_managed_variables(managed)


def store_credential(variable_name: str, secret: str) -> None:
    """Store a credential in the secure keyring."""
    ensure_secure_backend()

    try:
        _call_keyring(lambda: keyring.set_password(SERVICE_NAME, variable_name, secret))
    except (KeyringError, NoKeyringError) as exc:
        raise KeyringUnavailableError(str(exc)) from exc

    add_managed_variable(variable_name)


def delete_credential(variable_name: str) -> bool:
    """Delete a stored credential and update the managed index."""
    ensure_secure_backend()

    try:
        existing = _call_keyring(
            lambda: keyring.get_password(SERVICE_NAME, variable_name)
        )
    except (KeyringError, NoKeyringError) as exc:
        raise KeyringUnavailableError(str(exc)) from exc

    if existing is None:
        return False

    try:
        _call_keyring(lambda: keyring.delete_password(SERVICE_NAME, variable_name))
    except (KeyringError, NoKeyringError) as exc:
        raise KeyringUnavailableError(str(exc)) from exc

    remove_managed_variable(variable_name)
    return True


def credential_exists(variable_name: str) -> bool:
    """Return whether a credential exists in the secure keyring."""
    try:
        return (
            _call_keyring(lambda: keyring.get_password(SERVICE_NAME, variable_name))
            is not None
        )
    except (KeyringError, NoKeyringError):
        return False


def get_provider_credential_variables(provider: str) -> tuple[str, ...]:
    """Return the credential variables typically associated with a provider."""
    fallback = _PROVIDER_CREDENTIAL_VARIABLES.get(provider, ())

    try:
        validation = litellm.validate_environment(f"{provider}/*")
    except Exception:  # noqa: BLE001
        return fallback

    missing_keys = validation.get("missing_keys")
    if not isinstance(missing_keys, list):
        return fallback

    candidate_keys = tuple(
        key for key in missing_keys if isinstance(key, str) and key.strip()
    )
    return candidate_keys or fallback


def resolve_credential(
    variable_name: str,
    *,
    completion_timeout: float | None = None,
    managed_index: set[str] | None = None,
) -> CredentialResolution:
    """Resolve a single credential from env vars or keyring."""
    managed = managed_index if managed_index is not None else get_managed_variables()

    env_value = normalize_env_value(os.getenv(variable_name))
    if env_value is not None:
        return CredentialResolution(
            variable_name=variable_name,
            source="env",
            raw_value=env_value,
            masked_value=mask_secret(env_value),
            is_managed=variable_name in managed,
        )

    try:
        keyring_value = _read_keyring_value(variable_name, timeout=completion_timeout)
    except CredentialLookupTimeout:
        return CredentialResolution(
            variable_name=variable_name,
            source="timeout",
            raw_value=None,
            masked_value=None,
            is_managed=variable_name in managed,
        )

    if keyring_value is not None:
        return CredentialResolution(
            variable_name=variable_name,
            source="keyring",
            raw_value=keyring_value,
            masked_value=mask_secret(keyring_value),
            is_managed=variable_name in managed,
        )

    return CredentialResolution(
        variable_name=variable_name,
        source="missing",
        raw_value=None,
        masked_value=None,
        is_managed=variable_name in managed,
    )


def resolve_provider_credential(
    provider: str,
    *,
    completion_timeout: float | None = None,
) -> CredentialResolution | None:
    """Resolve the credential for a provider-backed LLM provider."""
    variable_names = get_provider_credential_variables(provider)
    if not variable_names:
        return None

    managed = get_managed_variables()
    for variable_name in variable_names:
        resolution = resolve_credential(
            variable_name,
            completion_timeout=completion_timeout,
            managed_index=managed,
        )
        if resolution.source in {"env", "keyring"}:
            return resolution
        if resolution.source == "timeout":
            return resolution

    first_variable = variable_names[0]
    return CredentialResolution(
        variable_name=first_variable,
        source="missing",
        raw_value=None,
        masked_value=None,
        is_managed=first_variable in managed,
    )


def detect_provider_from_credentials(
    *,
    completion_timeout: float | None = None,
) -> str | None:
    """Detect a provider from env vars or keyring-backed credentials."""
    if normalize_env_value(os.getenv("OPENAI_API_KEY")):
        return "openai"
    if normalize_env_value(os.getenv("ANTHROPIC_API_KEY")):
        return "anthropic"
    if normalize_env_value(os.getenv("COHERE_API_KEY")):
        return "cohere"
    if normalize_env_value(os.getenv("AZURE_API_KEY")):
        return "azure"
    if normalize_env_value(os.getenv("GEMINI_API_KEY")) or normalize_env_value(
        os.getenv("GOOGLE_API_KEY")
    ):
        return "gemini"

    for provider in _PROVIDER_CREDENTIAL_VARIABLES:
        resolution = resolve_provider_credential(
            provider,
            completion_timeout=completion_timeout,
        )
        if resolution is None:
            continue
        if resolution.source in {"env", "keyring"}:
            return provider
        if resolution.source == "timeout":
            raise CredentialLookupTimeout(
                f"Credential lookup for provider '{provider}' timed out after {completion_timeout} seconds."
            )

    return None


def build_missing_credential_error(variable_name: str | None = None) -> str:
    """Build the standard missing-credential guidance."""
    return build_missing_credential_message(variable_name)


def build_backend_error_message(status: BackendStatus) -> str:
    """Convert backend status into a user-facing error message."""
    if not status.is_available:
        return status.failure_reason or build_no_secure_keyring_message()
    if not status.is_secure:
        return status.failure_reason or build_insecure_keyring_message()
    return ""
