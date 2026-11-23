"""Shared schema constants and types for offline evaluation assets."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

SCHEMA_VERSION = "1.0"
SUPPORTED_FORMATS = ("freeform", "conventional", "gitmoji")
COMPOSITION_BOOLEAN_VALUES = frozenset({"enabled", "disabled"})
COMPOSITION_SCENARIOS = frozenset({"ordinary", "injection"})

INJECTION_PATTERN_TAGS = frozenset(
    {
        "direct",
        "direct-instruction",
        "indirect",
        "indirect-external-content",
        "obfuscated",
        "obfuscated-encoded",
        "encoded",
        "deleted",
        "deleted-instruction",
    }
)
INJECTION_LOCATION_TAGS = frozenset(
    {
        "code-comment",
        "markdown",
        "docs",
        "string-literal",
        "test-fixture",
        "config-example",
    }
)
INJECTION_TAGS = INJECTION_PATTERN_TAGS | INJECTION_LOCATION_TAGS

SUPPORTED_ERROR_CATEGORIES = frozenset(
    {
        "accuracy",
        "format",
        "hallucination",
        "injection",
        "length",
        "missing_context",
        "omission",
        "safety",
        "secret_leak",
        "style",
        "unsupported_claim",
    }
)

FormatName = Literal["freeform", "conventional", "gitmoji"]
FixtureOrigin = Literal["real", "adapted", "synthetic"]
RedistributionReview = Literal["not_reviewed", "metadata_only", "approved_for_fixture"]
SuiteKind = Literal["smoke", "core", "safety", "custom"]
UsabilityLabel = Literal["usable", "minor_edit", "major_edit", "unusable"]


def validate_schema_version(value: str) -> str:
    """Require asset documents to use the current schema contract."""
    if value != SCHEMA_VERSION:
        raise ValueError(
            f"unsupported schema_version {value!r}; expected {SCHEMA_VERSION!r}"
        )
    return value


class EvalModel(BaseModel):
    """Base model that rejects accidental asset fields.

    Strict shared configuration prevents silent schema drift across asset kinds.

    Example:
        >>> class Record(EvalModel):
        ...     id: str
        >>> Record.model_validate({"id": "one", "extra": True})
        Traceback (most recent call last):
        ...
        pydantic_core._pydantic_core.ValidationError: ...
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


__all__ = [
    "COMPOSITION_BOOLEAN_VALUES",
    "COMPOSITION_SCENARIOS",
    "EvalModel",
    "FixtureOrigin",
    "FormatName",
    "INJECTION_LOCATION_TAGS",
    "INJECTION_PATTERN_TAGS",
    "INJECTION_TAGS",
    "RedistributionReview",
    "SCHEMA_VERSION",
    "SUPPORTED_ERROR_CATEGORIES",
    "SUPPORTED_FORMATS",
    "SuiteKind",
    "UsabilityLabel",
    "validate_schema_version",
]
