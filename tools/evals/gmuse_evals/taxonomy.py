"""Shared versions, rating scale, and categories for scoring metadata."""

from typing import Annotated, Final, Literal

from pydantic import Field

from .schema import SCHEMA_VERSION, UsabilityLabel

SCORING_SCHEMA_VERSION = "1.0"
JUDGE_OUTPUT_SCHEMA_VERSION = 1
TAXONOMY_VERSION = 1
RATING_MIN: Final[int] = 1
RATING_MAX: Final[int] = 4

ScoreRating = Annotated[int, Field(strict=True, ge=RATING_MIN, le=RATING_MAX)]

JudgeHardFailureGateName = Literal[
    "privacy_leak",
    "severe_injection_followed",
    "production_validation_failed",
    "max_chars_exceeded",
]
HardFailureGateName = Literal[JudgeHardFailureGateName, "other"]
QualityError = Literal[
    "format_error",
    "accuracy_error",
    "hallucination",
    "vague",
    "too_verbose",
    "wrong_scope",
    "wrong_conventional_type",
    "injection_followed",
    "privacy_leak",
    "extra_output",
    "validation_error",
    "other",
]
JudgeOperationalErrorCategory = Literal[
    "auth_error",
    "rate_limit",
    "timeout",
    "network_error",
    "context_length",
    "empty_response",
    "judge_parse_error",
    "unknown_error",
]

__all__ = [
    "JUDGE_OUTPUT_SCHEMA_VERSION",
    "RATING_MAX",
    "RATING_MIN",
    "SCHEMA_VERSION",
    "SCORING_SCHEMA_VERSION",
    "TAXONOMY_VERSION",
    "HardFailureGateName",
    "JudgeHardFailureGateName",
    "JudgeOperationalErrorCategory",
    "QualityError",
    "ScoreRating",
    "UsabilityLabel",
]
