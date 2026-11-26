from __future__ import annotations

import signal

from inspect_ai.log import read_eval_log

from tools.evals.gmuse_evals.inspect_runner import run_inspect_plan
from tools.evals.gmuse_evals.run_plan import Guardrails, build_run_plan
from tools.evals.gmuse_evals.validate import validate_suite


def test_inspect_log_contains_raw_invalid_output_and_privacy_safe_prompt_fields(
    tmp_path,
) -> None:
    plan = build_run_plan(validate_suite("evals", "smoke"), mode="check")
    execution = run_inspect_plan(plan, log_dir=tmp_path / "inspect")

    assert len(execution.results) == len(plan.entries)
    log = read_eval_log(str(execution.logs[0].location))
    assert log.metadata["gmuse_eval_schema_version"] == "1.0"
    assert log.samples is not None
    assert len(log.samples) == len(plan.entries)
    for sample in log.samples:
        assert sample.metadata["candidate_kind"] == "deterministic_check"
        assert sample.metadata["prompt_hash"]
        assert "raw_prompt" not in sample.metadata


def test_live_sample_cap_bounds_actual_production_attempts(tmp_path) -> None:
    calls = []

    def response(**kwargs):
        calls.append(kwargs)
        return "docs: update documentation"

    plan = build_run_plan(
        validate_suite("evals", "smoke"),
        mode="live",
        models=("test/model",),
        guardrails=Guardrails(max_samples=2),
    )
    execution = run_inspect_plan(
        plan, log_dir=tmp_path / "inspect", response_generator=response
    )
    assert len(calls) == 2
    assert len(execution.results) == 2
    samples = read_eval_log(str(execution.logs[0].location)).samples
    assert samples is not None
    assert len(samples) == 2


def test_interrupted_live_run_preserves_completed_sample(tmp_path) -> None:
    attempts = 0
    message = "docs: update documentation"

    def response(**kwargs) -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 2:
            signal.raise_signal(signal.SIGINT)
        return message

    plan = build_run_plan(
        validate_suite("evals", "smoke"),
        mode="live",
        models=("test/model",),
        guardrails=Guardrails(max_samples=2),
    )
    log_dir = tmp_path / "inspect"
    run_inspect_plan(plan, log_dir=log_dir, response_generator=response)

    assert attempts == 2
    (path,) = log_dir.glob("*.eval")
    log = read_eval_log(str(path))
    assert log.status == "cancelled"
    assert log.samples is not None
    (completed,) = log.samples
    assert completed.error is None
    assert completed.output.completion == message
