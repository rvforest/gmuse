"""Custom exceptions for gmuse.

This module defines all custom exception types used throughout the gmuse application.
All exceptions inherit from GmuseError, allowing callers to catch all application
errors with a single except clause if desired.

Exception Hierarchy:
    GmuseError
    ├── ConfigError
    ├── NotAGitRepositoryError
    ├── NoStagedChangesError
    ├── LLMError
    └── InvalidMessageError
"""


class GmuseError(Exception):
    """Base exception for all gmuse errors.

    All custom exceptions in gmuse inherit from this class, allowing callers
    to catch any gmuse-specific error with a single except clause:

        try:
            result = generate_message(config)
        except GmuseError as e:
            print(f"gmuse error: {e}")
    """


class ConfigError(GmuseError):
    """Raised when configuration is invalid or cannot be loaded.

    This error is raised in the following situations:

    - Invalid TOML syntax in config.toml
    - Invalid config values (e.g., negative history_depth)
    - Config file permission errors
    - Unknown or unsupported configuration options
    """


class NotAGitRepositoryError(GmuseError):
    """Raised when the current directory is not a git repository.

    This error is raised when:

    - Running gmuse outside a git repository
    - Git is not installed on the system
    - The .git directory is corrupted or missing
    """


class NoStagedChangesError(GmuseError):
    """Raised when there are no staged changes to generate a message for.

    This error is raised when:

    - User runs `gmuse` with no files staged
    - All staged changes have been unstaged
    - The staging area is empty
    """


class LLMError(GmuseError):
    """Raised when LLM API call fails or returns invalid response.

    This error is raised for:

    - No API key configured for any provider
    - Network timeout during API call
    - Invalid or malformed API response
    - Rate limiting by the provider
    - Model not found or unsupported
    - Provider-specific API errors
    """


class InvalidMessageError(GmuseError):
    """Raised when generated commit message fails validation.

    This error is raised when:

    - Message is empty or whitespace-only
    - Message exceeds maximum length limit
    - Message doesn't match required format (e.g., conventional commits)
    - Message contains invalid characters
    """


def _env_var_name(prefix: str) -> str:
    return "_".join((prefix, "API", "KEY"))


class CredentialError(GmuseError):
    """Raised when credential storage or lookup fails."""


class CredentialLookupTimeout(CredentialError):
    """Raised when credential lookup exceeds the allowed time budget."""


class KeyringUnavailableError(CredentialError):
    """Raised when no secure keyring backend is available."""


class InsecureKeyringError(CredentialError):
    """Raised when the active keyring backend is insecure."""


def build_missing_credential_message(variable_name: str | None = None) -> str:
    """Build an actionable missing-credential error message."""

    if variable_name:
        return (
            "No API credential is configured for the selected provider.\n\n"
            "For interactive use, run:\n"
            f"  gmuse auth set {variable_name}\n\n"
            "For CI/CD or headless environments, use environment variables:\n"
            f"  export {variable_name}='sk-...'"
        )

    return (
        "No LLM provider API key configured.\n\n"
        "For interactive use, run:\n"
        f"  gmuse auth set {_env_var_name('OPENAI')}\n\n"
        "For CI/CD or headless environments, use environment variables:\n"
        f"  export {_env_var_name('OPENAI')}='sk-...'\n"
        f"  export {_env_var_name('ANTHROPIC')}='sk-ant-...'"
    )


def build_no_secure_keyring_message() -> str:
    """Build an actionable message for missing secure keyring support."""
    return (
        "No secure system keyring is available.\n\n"
        "Use environment variables instead for this environment:\n"
        f"  export {_env_var_name('OPENAI')}='sk-...'"
    )


def build_insecure_keyring_message() -> str:
    """Build an actionable message for insecure keyring backends."""
    return (
        "Active keyring backend is insecure and cannot be used.\n\n"
        "gmuse refuses plaintext or null keyring backends. Use environment variables instead."
    )


def build_overwrite_message(variable_name: str) -> str:
    """Build the message shown when a credential already exists."""
    return (
        f"Credential for {variable_name} already exists.\n\n"
        "Re-run with --force or confirm overwrite in an interactive terminal."
    )


def build_provider_validation_message(provider: str) -> str:
    """Build the message shown when provider validation fails."""
    return f"Could not validate credentials for provider '{provider}'."
