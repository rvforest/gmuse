"""Tests for scoring recorded candidate metadata without a judge."""

from copy import deepcopy
from pathlib import Path

import pytest

from tools.evals.gmuse_evals.inspect_adapter import stable_asset_digest
from tools.evals.gmuse_evals.logs import build_run_metadata, build_sample_metadata
from tools.evals.gmuse_evals.results import ResolvedCase
from tools.evals.gmuse_evals.scoring import score_deterministic
from tools.evals.gmuse_evals.validate import validate_suite

ASSETS = Path(__file__).resolve().parents[2] / "evals"


@pytest.fixture
def resolved_case() -> ResolvedCase:
    result = validate_suite(ASSETS, "smoke")
    return next(
        case for case in result.resolved_cases if case.case.id == "injection-comment"
    )


@pytest.fixture
def run_metadata() -> dict[str, object]:
    return build_run_metadata(
        execution_mode="check",
        suite_id="smoke",
        suite_version="1",
        selected_case_ids=["injection-comment"],
        prompt_version="1.0.0",
    )


@pytest.fixture
def sample_metadata(resolved_case: ResolvedCase) -> dict[str, object]:
    case = resolved_case
    sample = build_sample_metadata(
        entry_id="injection-comment:freeform:deterministic-check",
        case_id=case.case.id,
        case_revision=case.case.revision,
        candidate_kind="deterministic_check",
        fixture_id=case.fixture.id,
        fixture_revision=case.fixture.revision,
        fixture_digest=case.fixture.expected_staged_diff_sha256,
        rubric_id=case.rubric.id,
        rubric_version=case.rubric.revision,
        staged_diff_digest=case.fixture.expected_staged_diff_sha256,
        generation={"format": "freeform", "max_chars": 80},
        validation={"valid": True},
        generated_message="Cover untrusted fixture comments",
    )
    sample["prompt_sha256"] = "original-prompt-hash"
    return sample


def test_offline_score_preserves_source_and_records_assets(
    sample_metadata: dict[str, object],
    run_metadata: dict[str, object],
    resolved_case: ResolvedCase,
) -> None:
    original = deepcopy(sample_metadata)
    record = score_deterministic(sample_metadata, run_metadata, resolved_case)

    assert sample_metadata == original
    assert record["scoring_status"] == "scored"
    assert record["unscored_reason"] is None
    assert record["source"]["run_id"] == run_metadata["run_id"]
    assert record["source"]["entry_id"] == sample_metadata["entry_id"]
    assert record["source"]["prompt_sha256"] == "original-prompt-hash"
    assert record["rubric_identity"] == {
        "id": resolved_case.rubric.id,
        "revision": resolved_case.rubric.revision,
        "digest": stable_asset_digest(resolved_case.rubric),
    }
    assert record["scoring_profile_identity"]["id"] == resolved_case.scoring_profile.id
    assert record["effective_ratings"]["usability"] is None
    assert record["effective_ratings"]["hard_failed"] is False
    assert record["judge_result"] is None
    assert record["deterministic_checks"]
    assert "aggregate_score" not in record


def test_hard_gate_forces_unusable_without_ratings(
    sample_metadata: dict[str, object],
    run_metadata: dict[str, object],
    resolved_case: ResolvedCase,
) -> None:
    sample_metadata["production_validation"] = {"valid": False}
    record = score_deterministic(sample_metadata, run_metadata, resolved_case)

    assert record["scoring_status"] == "scored"
    assert record["effective_ratings"] == {
        "accuracy": None,
        "message_quality": None,
        "style_context_fit": None,
        "usability": "unusable",
        "hard_failed": True,
        "derived_from": "deterministic_checks",
    }
    assert "production_validation_failed" in {
        gate["gate"] for gate in record["hard_failure_gates"]
    }
    assert "validation_error" in record["quality_errors"]


def test_candidate_operational_failure_is_unscored(
    sample_metadata: dict[str, object],
    run_metadata: dict[str, object],
    resolved_case: ResolvedCase,
) -> None:
    del sample_metadata["generated_message"]
    sample_metadata["operational_error"] = {"category": "timeout"}
    sample_metadata["production_validation"] = {"valid": False}
    record = score_deterministic(sample_metadata, run_metadata, resolved_case)

    assert record["scoring_status"] == "unscored"
    assert record["unscored_reason"] == "candidate_operational_failure"
    assert record["quality_errors"] == []
    assert record["hard_failure_gates"] == []
    assert record["judge_operational_error"] is None


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("generated_message", None, "missing_generated_message"),
        ("case_revision", 2, "incompatible_case_assets"),
        ("rubric_id", "changed", "incompatible_case_assets"),
        ("staged_diff_digest", "changed", "incompatible_case_assets"),
        ("fixture_digest", "changed", "incompatible_case_assets"),
        ("production_validation", {}, "missing_production_validation"),
        ("max_chars", False, "invalid_max_chars"),
    ],
)
def test_unscored_reasons(
    sample_metadata: dict[str, object],
    run_metadata: dict[str, object],
    resolved_case: ResolvedCase,
    field: str,
    value: object,
    reason: str,
) -> None:
    sample_metadata[field] = value
    record = score_deterministic(sample_metadata, run_metadata, resolved_case)

    assert record["scoring_status"] == "unscored"
    assert record["unscored_reason"] == reason
    assert record["hard_failure_gates"] == []


def test_unavailable_source_case_is_unscored(
    sample_metadata: dict[str, object], run_metadata: dict[str, object]
) -> None:
    record = score_deterministic(sample_metadata, run_metadata, None)

    assert record["scoring_status"] == "unscored"
    assert record["unscored_reason"] == "case_assets_unavailable"
