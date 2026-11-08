"""Stable operational error categories for eval result artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from gmuse.exceptions import (
    CredentialError,
    LLMError,
    NoStagedChangesError,
    NotAGitRepositoryError,
)

ErrorCategory = Literal[
    "authentication",
    "rate_limit",
    "timeout",
    "network",
    "context_length",
    "empty_response",
    "fixture_setup",
    "unknown",
]


@dataclass(frozen=True, slots=True)
class OperationalError:
    """Serializable operational failure independent of message validation."""

    category: ErrorCategory
    message: str
    exception_type: str

    def as_dict(self) -> dict[str, str]:
        """Return JSON-compatible error metadata."""
        return {
            "category": self.category,
            "message": self.message,
            "exception_type": self.exception_type,
        }


def classify_error(error: BaseException) -> OperationalError:
    """Translate provider and fixture failures into deterministic categories."""
    text = str(error).lower()
    name = type(error).__name__
    if isinstance(error, (CredentialError,)) or any(
        marker in text
        for marker in ("api key", "authentication", "unauthorized", "forbidden")
    ):
        category: ErrorCategory = "authentication"
    elif any(
        marker in text
        for marker in ("rate limit", "ratelimit", "too many requests", "429")
    ):
        category = "rate_limit"
    elif isinstance(error, TimeoutError) or "timeout" in text or "timed out" in text:
        category = "timeout"
    elif any(
        marker in text for marker in ("network", "connection", "dns", "unreachable")
    ):
        category = "network"
    elif any(
        marker in text
        for marker in ("context length", "context_length", "maximum context")
    ):
        category = "context_length"
    elif "empty response" in text or "empty completion" in text:
        category = "empty_response"
    elif (
        isinstance(error, (NoStagedChangesError, NotAGitRepositoryError))
        or "fixture" in text
    ):
        category = "fixture_setup"
    elif isinstance(error, LLMError) and "empty" in text:
        category = "empty_response"
    else:
        category = "unknown"
    return OperationalError(category, str(error), name)


__all__ = ["ErrorCategory", "OperationalError", "classify_error"]
