"""Offline scoring contracts for saved gmuse Inspect logs."""

from pathlib import Path

import pytest
from inspect_ai.log import EvalLog, read_eval_log, write_eval_log

from tools.evals.gmuse_evals.inspect_runner import run_inspect_plan
from tools.evals.gmuse_evals.inspect_scorers import (
    DETERMINISTIC_SCORER_NAME,
    InspectScoringError,
    score_inspect_log,
)
from tools.evals.gmuse_evals.run_plan import Guardrails, build_run_plan
from tools.evals.gmuse_evals.validate import validate_suite

ASSETS = Path(__file__).resolve().parents[2] / "evals"


def _read_local_log(path: Path) -> EvalLog:
    with path.open("rb") as stream:
        return read_eval_log(stream)


@pytest.fixture(scope="module")
def candidate_log(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a source log with a rejected message and a candidate timeout."""
    plan = build_run_plan(
        validate_suite(ASSETS, "smoke"),
        mode="check",
        guardrails=Guardrails(max_samples=2),
    )
    call_count = 0

    def response() -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return "x" * 100
        raise TimeoutError("simulated candidate timeout")

    run = run_inspect_plan(
        plan,
        log_dir=tmp_path_factory.mktemp("source-inspect"),
        response_generator=response,
    )
    return Path(run.logs[0].location)


def test_offline_scoring_preserves_source_and_attaches_native_evidence(
    candidate_log: Path, tmp_path: Path
) -> None:
    source_bytes = candidate_log.read_bytes()
    source = _read_local_log(candidate_log)
    destination = tmp_path / "new-directory" / "scored.eval"

    summary = score_inspect_log(candidate_log, destination, evals_dir=ASSETS)

    assert candidate_log.read_bytes() == source_bytes
    assert (summary.total, summary.scored, summary.unscored, summary.hard_failed) == (
        2,
        1,
        1,
        1,
    )
    assert summary.destination == destination
    scored = _read_local_log(destination)
    assert scored.metadata == source.metadata
    assert not scored.reductions
    assert scored.results is not None
    assert not scored.results.scores
    assert source.samples is not None and scored.samples is not None
    for original_sample, scored_sample in zip(
        source.samples, scored.samples, strict=True
    ):
        assert scored_sample.id == original_sample.id
        assert scored_sample.metadata == original_sample.metadata
        assert scored_sample.output == original_sample.output

    invalid = next(
        sample for sample in scored.samples if "generated_message" in sample.metadata
    )
    failed = next(
        sample for sample in scored.samples if sample.metadata["operational_error"]
    )
    assert invalid.scores is not None and failed.scores is not None
    invalid_score = invalid.scores[DETERMINISTIC_SCORER_NAME]
    failed_score = failed.scores[DETERMINISTIC_SCORER_NAME]
    assert invalid_score.value == "scored"
    assert invalid_score.metadata is not None
    assert invalid_score.metadata["hard_failure_gates"]
    assert "aggregate_score" not in invalid_score.metadata
    assert failed_score.value == "unscored"
    assert failed_score.metadata is not None
    assert failed_score.metadata["unscored_reason"] == "candidate_operational_failure"
    assert failed_score.metadata["hard_failure_gates"] == []


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("unknown_version", "Unsupported gmuse runner log schema"),
        ("missing_samples", "no original candidate samples"),
        ("suite_revision", "suite revision differs"),
    ],
)
def test_incompatible_runner_logs_do_not_write_output(
    candidate_log: Path, tmp_path: Path, change: str, message: str
) -> None:
    log = _read_local_log(candidate_log)
    assert log.eval.metadata is not None
    if change == "unknown_version":
        log.eval.metadata["gmuse_eval_schema_version"] = "999"
    elif change == "missing_samples":
        log.samples = None
    else:
        log.eval.metadata["suite_version"] = "999"
    source = tmp_path / "source.eval"
    write_eval_log(log, source)
    destination = tmp_path / "scored.eval"

    with pytest.raises(InspectScoringError, match=message):
        score_inspect_log(source, destination, evals_dir=ASSETS)

    assert not destination.exists()


def test_scoring_rejects_version_one_log_with_raw_context(
    candidate_log: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = candidate_log.read_bytes()
    log = _read_local_log(candidate_log)
    assert log.eval.metadata is not None
    log.metadata["gmuse_eval_schema_version"] = "1.0"
    log.metadata["effective_generation_defaults"] = {
        "temperature": 0.2,
        "hint": "legacy private hint",
        "repository_instructions": "legacy private instructions",
    }
    monkeypatch.setattr("inspect_ai.log.read_eval_log", lambda _stream: log)
    destination = tmp_path / "scored.eval"

    with pytest.raises(InspectScoringError, match="Rerun the eval"):
        score_inspect_log(candidate_log, destination, evals_dir=ASSETS)

    assert candidate_log.read_bytes() == original
    assert not destination.exists()


def test_scoring_refuses_to_replace_any_existing_log(
    candidate_log: Path, tmp_path: Path
) -> None:
    destination = tmp_path / "scored.eval"
    destination.write_bytes(b"prior log")
    with pytest.raises(InspectScoringError, match="already exists"):
        score_inspect_log(candidate_log, destination, evals_dir=ASSETS)
    with pytest.raises(InspectScoringError, match="different path"):
        score_inspect_log(candidate_log, candidate_log, evals_dir=ASSETS)

    assert destination.read_bytes() == b"prior log"
