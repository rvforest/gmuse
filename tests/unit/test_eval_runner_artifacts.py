from __future__ import annotations

from gmuse.commit import GenerationPromptMetadata
from tools.evals.gmuse_evals.errors import classify_error
from tools.evals.gmuse_evals.logs import build_sample_metadata, summarize_results


def test_error_classification_and_privacy_safe_metadata() -> None:
    error = classify_error(TimeoutError("slow provider"))
    assert error.category == "timeout"
    metadata = build_sample_metadata(
        entry_id="entry-1",
        case_id="case-1",
        candidate_kind="deterministic_check",
        prompt=GenerationPromptMetadata.from_prompts("system", "secret prompt"),
    )
    assert metadata["prompt_hash"]
    assert "secret prompt" not in str(metadata)


def test_summary_aggregates_validation_and_operational_counts() -> None:
    summary = summarize_results(
        [
            {"validation": {"valid": True}, "operational_error": None},
            {"validation": {"valid": False}, "operational_error": None},
            {
                "validation": {"valid": False},
                "operational_error": {"category": "timeout"},
            },
        ],
        planned_entries=3,
    )
    assert summary.completed_entries == 3
    assert summary.validation_passed == 1
    assert summary.validation_failed == 1
    assert summary.operational_errors == 1
