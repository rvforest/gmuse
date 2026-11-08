from __future__ import annotations

from pathlib import Path

import pytest

from tools.evals.gmuse_evals.runner import (
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

    empty = validated.__class__(validated.suite, (), validated.report)
    with pytest.raises(RunPlanError, match="no matching"):
        build_run_plan(empty, mode="check")


def test_live_plan_requires_guardrail_and_expands_models() -> None:
    validated = validate_suite("evals", "smoke")
    with pytest.raises(RunPlanError, match="guardrail"):
        build_run_plan(validated, mode="live", models=("test/model",))

    plan = build_run_plan(
        validated,
        mode="live",
        models=("test/model", "other/model"),
        guardrails=Guardrails(max_samples=2),
    )
    assert len(plan.entries) == 2
    assert {entry.model for entry in plan.entries} == {"test/model", "other/model"}
