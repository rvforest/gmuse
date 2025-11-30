"""Structured logging for gmuse with debug mode support.

This module provides a centralized logging configuration that can be toggled
via the GMUSE_DEBUG environment variable.

Public API:
    - setup_logger: Configure and return a logger with appropriate settings
    - get_logger: Get an existing logger or create a new one
    - configure_litellm_logging: Configure litellm library logging

Environment Variables:
    - GMUSE_DEBUG: Set to "1", "true", or "yes" to enable debug logging
"""

import logging
import os
import sys
from typing import Final, Optional

_DEBUG_ENV_VALUES: Final[frozenset[str]] = frozenset({"1", "true", "yes"})
"""Environment variable values that enable debug mode."""

_LOG_FORMAT: Final[str] = "[%(levelname)s] %(message)s"
"""Log message format (simple, no timestamps for CLI tool)."""


def setup_logger(name: str = "gmuse", level: Optional[int] = None) -> logging.Logger:
    """Configure and return a logger with appropriate settings.

    Args:
        name: Logger name, defaults to "gmuse"
        level: Logging level, defaults to INFO or DEBUG based on GMUSE_DEBUG env var

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger()
        >>> logger.debug("This only shows when GMUSE_DEBUG=1")
        >>> logger.info("This always shows")
    """
    logger = logging.getLogger(name)

    # Don't add handlers if they already exist (avoid duplicate logs)
    if logger.handlers:
        return logger

    # Determine log level from environment or parameter
    if level is None:
        debug_enabled = os.getenv("GMUSE_DEBUG", "").lower() in _DEBUG_ENV_VALUES
        level = logging.DEBUG if debug_enabled else logging.INFO

    logger.setLevel(level)

    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    formatter = logging.Formatter(_LOG_FORMAT)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def get_logger(name: str = "gmuse") -> logging.Logger:
    """Get an existing logger or create a new one with default settings.

    Args:
        name: Logger name, defaults to "gmuse"

    Returns:
        Logger instance

    Example:
        >>> from gmuse.logging import get_logger
        >>> logger = get_logger()
        >>> logger.info("Loading configuration...")
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


def configure_litellm_logging() -> None:
    """Configure litellm library logging based on debug mode.

    Suppresses litellm's verbose debug output unless GMUSE_DEBUG is enabled.
    This should be called once when the llm_client module is imported.
    """
    debug_enabled = os.getenv("GMUSE_DEBUG", "").lower() in _DEBUG_ENV_VALUES

    if debug_enabled:
        logging.getLogger("litellm").setLevel(logging.DEBUG)
    else:
        # Try to use litellm's built-in suppression first
        try:
            import litellm

            litellm.suppress_debug_info = True  # type:ignore
        except (ImportError, AttributeError):
            # Fallback: just set the log level
            pass
        logging.getLogger("litellm").setLevel(logging.WARNING)
