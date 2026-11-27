"""Tests for the versioned scoring taxonomy."""

from typing import get_args

from tools.evals.gmuse_evals import schema, taxonomy


def test_scoring_versions_and_reused_asset_types() -> None:
    assert taxonomy.SCORING_SCHEMA_VERSION == "1.0"
    assert taxonomy.JUDGE_OUTPUT_SCHEMA_VERSION == 1
    assert taxonomy.JUDGE_PROMPT_VERSION == 1
    assert taxonomy.TAXONOMY_VERSION == 1
    assert taxonomy.SCHEMA_VERSION == schema.SCHEMA_VERSION
    assert taxonomy.UsabilityLabel is schema.UsabilityLabel


def test_quality_and_judge_operational_errors_are_disjoint() -> None:
    quality = set(get_args(taxonomy.QualityError))
    operational = set(get_args(taxonomy.JudgeOperationalErrorCategory))

    assert quality == {
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
    }
    assert operational == {
        "auth_error",
        "rate_limit",
        "timeout",
        "network_error",
        "context_length",
        "empty_response",
        "judge_parse_error",
        "unknown_error",
    }
    assert quality.isdisjoint(operational)


def test_hard_failure_gates_match_the_judge_contract() -> None:
    judge_gates = set(get_args(taxonomy.JudgeHardFailureGateName))
    assert judge_gates == {
        "privacy_leak",
        "severe_injection_followed",
        "production_validation_failed",
        "max_chars_exceeded",
    }
    assert set(get_args(taxonomy.HardFailureGateName)) == judge_gates | {"other"}
