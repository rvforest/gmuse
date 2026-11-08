from __future__ import annotations

from tools.evals.gmuse_evals.execution import execute_entry
from tools.evals.gmuse_evals.runner import build_run_plan
from tools.evals.gmuse_evals.validate import validate_suite


def test_production_context_contains_history_branch_hint_and_instructions() -> None:
    plan = build_run_plan(validate_suite("evals", "smoke"), mode="check")
    entry = plan.entries[0]
    result = execute_entry(entry, response_generator=lambda **_: "Update docs")

    assert result.context is not None
    assert result.context.history is not None
    assert result.context.branch_info is not None
    assert result.context.branch_info.branch_type == "feature"
    assert result.context.repo_instructions is not None
    assert entry.generation.hint
    assert entry.generation.max_chars == 72
    assert result.staged_diff_digest == entry.fixture.expected_staged_diff_sha256


def test_invalid_message_is_retained_with_validation_failure() -> None:
    plan = build_run_plan(validate_suite("evals", "smoke"), mode="check")
    entry = next(
        item for item in plan.entries if item.generation.format == "conventional"
    )
    result = execute_entry(entry, response_generator=lambda **_: "raw invalid output")

    assert result.message == "raw invalid output"
    assert result.validation.valid is False
    assert result.operational_error is None
