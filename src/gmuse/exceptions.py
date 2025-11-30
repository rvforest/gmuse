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
