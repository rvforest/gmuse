"""Shared versions and categories for judge scoring and its metadata."""

from typing import Literal

from .schema import SCHEMA_VERSION, UsabilityLabel

SCORING_SCHEMA_VERSION = "1.0"
JUDGE_OUTPUT_SCHEMA_VERSION = 1
JUDGE_PROMPT_VERSION = 1
TAXONOMY_VERSION = 1

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
    "JUDGE_PROMPT_VERSION",
    "SCHEMA_VERSION",
    "SCORING_SCHEMA_VERSION",
    "TAXONOMY_VERSION",
    "HardFailureGateName",
    "JudgeHardFailureGateName",
    "JudgeOperationalErrorCategory",
    "QualityError",
    "UsabilityLabel",
]
