from __future__ import annotations

import pytest

from tools.evals.gmuse_evals.results import SuiteValidationResult
from tools.evals.gmuse_evals.run_plan import (
    Guardrails,
    RunPlanError,
    build_run_plan,
)
from tools.evals.gmuse_evals.validate import validate_suite


def test_smoke_plan_expands_each_case_and_format() -> None:
    validated = validate_suite("evals", "smoke")
    plan = build_run_plan(validated, mode="check")

    assert len(plan.entries) == 5
    assert [entry.case_id for entry in plan.entries] == [
        "docs-history",
        "docs-history",
        "injection-comment",
        "injection-comment",
        "injection-comment",
    ]
    assert len({entry.entry_id for entry in plan.entries}) == 5
    assert all(entry.candidate_kind == "deterministic_check" for entry in plan.entries)


def test_check_plan_rejects_model_and_empty_selection() -> None:
    validated = validate_suite("evals", "smoke")
    with pytest.raises(RunPlanError, match="only valid"):
        build_run_plan(validated, mode="check", models=("gpt-test",))

    empty = SuiteValidationResult(
        suite=validated.suite, resolved_cases=(), report=validated.report
    )
    with pytest.raises(RunPlanError, match="no matching"):
        build_run_plan(empty, mode="check")


def test_live_plan_requires_guardrail_and_expands_models() -> None:
    validated = validate_suite("evals", "smoke")
    assert validated.suite is not None
    with pytest.raises(RunPlanError, match="guardrail"):
        build_run_plan(validated, mode="live", models=("test/model",))

    plan = build_run_plan(
        validated,
        mode="live",
        models=("test/model", "other/model"),
        guardrails=Guardrails(max_samples=10, concurrency=1),
    )
    assert plan.suite_id == "smoke"
    assert plan.suite_version == str(validated.suite.revision)
    assert plan.selected_case_ids == ("docs-history", "injection-comment")
    assert plan.models == ("test/model", "other/model")
    assert plan.planned_entries == len(plan.entries) == 10
    assert plan.guardrails == Guardrails(max_samples=10, concurrency=1)


@pytest.mark.parametrize(
    ("limits", "message"),
    [
        (Guardrails(max_samples=5, max_tokens=10), "unsupported"),
        (Guardrails(max_samples=5, max_cost=1), "unsupported"),
        (Guardrails(max_samples=5, time_limit=1), "unsupported"),
        (Guardrails(max_samples=5, concurrency=2), "concurrency must be 1"),
        (Guardrails(max_samples=0), "greater than zero"),
    ],
)
def test_live_plan_rejects_invalid_limits(limits: Guardrails, message: str) -> None:
    validated = validate_suite("evals", "smoke")
    with pytest.raises(RunPlanError, match=message):
        build_run_plan(
            validated, mode="live", models=("test/model",), guardrails=limits
        )


@pytest.mark.parametrize("mode", ["check", "live"])
def test_capped_plan_retains_full_matrix_size(mode) -> None:
    validated = validate_suite("evals", "smoke")
    plan = build_run_plan(
        validated,
        mode=mode,
        models=("test/model",) if mode == "live" else (),
        guardrails=Guardrails(max_samples=2),
    )
    assert len(plan.entries) == 2
    assert plan.planned_entries == 5


def test_live_plan_rejects_empty_selections() -> None:
    validated = validate_suite("evals", "smoke")
    limits = Guardrails(max_samples=5)
    with pytest.raises(RunPlanError, match="--model is required"):
        build_run_plan(validated, mode="live", guardrails=limits)

    empty = SuiteValidationResult(
        suite=validated.suite, resolved_cases=(), report=validated.report
    )
    with pytest.raises(RunPlanError, match="no matching cases"):
        build_run_plan(empty, mode="live", models=("test/model",), guardrails=limits)
