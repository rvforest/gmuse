from __future__ import annotations

from tools.evals.gmuse_evals.execution import execute_entry
from tools.evals.gmuse_evals.runner import build_run_plan
from tools.evals.gmuse_evals.validate import validate_suite


def test_execution_reconstructs_repository_and_preserves_invalid_output() -> None:
    plan = build_run_plan(validate_suite("evals", "smoke"), mode="check")
    result = execute_entry(
        plan.entries[0],
        response_generator=lambda **_: "not a useful conventional result",
    )

    assert (
        result.staged_diff_digest == plan.entries[0].fixture.expected_staged_diff_sha256
    )
    assert result.message == "not a useful conventional result"
    assert result.validation.valid is True
