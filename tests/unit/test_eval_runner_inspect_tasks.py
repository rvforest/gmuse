from __future__ import annotations

from tools.evals.gmuse_evals.inspect_tasks import build_dataset, build_task
from tools.evals.gmuse_evals.runner import build_run_plan
from tools.evals.gmuse_evals.validate import validate_suite


def test_dataset_has_one_stable_sample_per_entry() -> None:
    plan = build_run_plan(validate_suite("evals", "smoke"), mode="check")
    dataset = build_dataset(plan)

    assert len(dataset) == len(plan.entries)
    assert [sample.id for sample in dataset] == [
        entry.entry_id for entry in plan.entries
    ]
    assert all(
        sample.metadata["candidate_kind"] == "deterministic_check" for sample in dataset
    )


def test_check_task_uses_local_solver() -> None:
    plan = build_run_plan(validate_suite("evals", "smoke"), mode="check")
    task = build_task(plan)

    assert task.dataset is not None
    assert task.scorer is None
    assert task.metadata["execution_mode"] == "check"
