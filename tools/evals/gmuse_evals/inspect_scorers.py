"""Plan and attach gmuse scoring to saved Inspect candidate logs."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

from .logs import EVAL_SCHEMA_VERSION
from .scoring import score_deterministic
from .validate import validate_suite

if TYPE_CHECKING:
    from inspect_ai.log import EvalLog

DETERMINISTIC_SCORER_NAME = "gmuse_deterministic"


class InspectScoringError(ValueError):
    """A saved Inspect run or output location cannot be used for scoring."""


@dataclass(frozen=True, slots=True)
class InspectScoringSummary:
    """Scoring counts and the path of the written Inspect log."""

    total: int
    scored: int
    unscored: int
    hard_failed: int
    destination: Path


def _paths(source: Path, destination: Path) -> tuple[Path, Path]:
    try:
        source = source.expanduser().resolve()
        destination = destination.expanduser().absolute()
        resolved_destination = destination.resolve()
    except (OSError, RuntimeError) as error:
        raise InspectScoringError("Cannot resolve the Inspect log paths.") from error
    if source == resolved_destination:
        raise InspectScoringError("Choose a different path for the scored log.")
    if destination.suffix != ".eval":
        raise InspectScoringError("The scored log path must end in .eval.")
    if destination.exists() or destination.is_symlink():
        raise InspectScoringError("The scored log already exists.")
    if not source.is_file():
        raise InspectScoringError("The source Inspect log must be a local file.")
    return source, destination


def _candidate_records(
    source: Path,
    evals_dir: Path,
) -> tuple[EvalLog, dict[tuple[int | str, int], dict[str, Any]]]:
    from inspect_ai.log import read_eval_log

    try:
        with source.open("rb") as stream:
            log = read_eval_log(stream)
    except Exception as error:
        raise InspectScoringError("Cannot read the requested Inspect log.") from error
    run_metadata = log.metadata or {}
    if run_metadata.get("gmuse_eval_schema_version") != EVAL_SCHEMA_VERSION:
        raise InspectScoringError(
            "Unsupported gmuse runner log schema. Rerun the eval with the current runner."
        )
    if not log.samples:
        raise InspectScoringError("The Inspect log has no original candidate samples.")
    if log.eval.model_roles or any(
        DETERMINISTIC_SCORER_NAME in (sample.scores or {}) for sample in log.samples
    ):
        raise InspectScoringError("Provide an original gmuse candidate runner log.")
    suite_id = run_metadata.get("suite_id")
    if not isinstance(suite_id, str) or not suite_id:
        raise InspectScoringError("The runner log is missing its suite identity.")
    if not isinstance(run_metadata.get("run_id"), str) or not run_metadata["run_id"]:
        raise InspectScoringError("The runner log is missing its run identity.")
    try:
        validated = validate_suite(evals_dir, suite_id)
    except (OSError, ValueError) as error:
        raise InspectScoringError("Cannot load the runner log's eval suite.") from error
    if validated.suite is None or validated.report.status != "passed":
        raise InspectScoringError("The runner log's eval suite did not validate.")
    if run_metadata.get("suite_version") != str(validated.suite.revision):
        raise InspectScoringError(
            "The eval suite revision differs from the runner log."
        )
    cases = {resolved.case.id: resolved for resolved in validated.resolved_cases}

    records = {}
    for sample in log.samples:
        case_id = sample.metadata.get("case_id")
        resolved = cases.get(case_id) if isinstance(case_id, str) else None
        record = score_deterministic(sample.metadata, run_metadata, resolved)
        key = (sample.id, sample.epoch)
        if key in records:
            raise InspectScoringError(
                "The candidate log contains duplicate sample identities."
            )
        records[key] = record
    return log, records


@contextmanager
def _reserve_destination(destination: Path) -> Iterator[None]:
    lock = destination.with_name(f".{destination.name}.lock")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise InspectScoringError(
            "The scored log path is reserved by another execution."
        ) from error
    except OSError as error:
        raise InspectScoringError(
            "Cannot reserve the scored Inspect log path."
        ) from error
    os.close(descriptor)
    try:
        if destination.exists() or destination.is_symlink():
            raise InspectScoringError("The scored log already exists.")
        yield
    finally:
        lock.unlink(missing_ok=True)


def _attach_scores(
    log: EvalLog,
    samples: dict[tuple[int | str, int], dict[str, Any]],
    name: str,
) -> EvalLog:
    from inspect_ai import score
    from inspect_ai.scorer import Score, Scorer, Target, scorer
    from inspect_ai.solver import TaskState

    @scorer(metrics=[], name=name)
    def gmuse_score() -> Scorer:
        async def score_sample(state: TaskState, target: Target) -> Score:
            result = samples[(state.sample_id, state.epoch)]
            return Score(value=result["scoring_status"], metadata=result)

        return score_sample

    try:
        return score(log, gmuse_score(), model="mockllm/deterministic", display="none")
    except Exception as error:
        raise InspectScoringError(
            "Could not score the recorded candidate samples."
        ) from error


def _publish(log: EvalLog, destination: Path) -> None:
    from inspect_ai.log import write_eval_log

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=destination.parent) as directory:
            temporary_log = Path(directory) / destination.name
            write_eval_log(log, temporary_log, format="eval")
            destination.hardlink_to(temporary_log)
    except FileExistsError as error:
        raise InspectScoringError("The scored log already exists.") from error
    except Exception as error:
        raise InspectScoringError("Cannot write the scored Inspect log.") from error


def _summary(
    samples: dict[tuple[int | str, int], dict[str, Any]],
    destination: Path,
) -> InspectScoringSummary:
    records = list(samples.values())
    scored = sum(record["scoring_status"] == "scored" for record in records)
    return InspectScoringSummary(
        total=len(records),
        scored=scored,
        unscored=len(records) - scored,
        hard_failed=sum(bool(record["hard_failure_gates"]) for record in records),
        destination=destination,
    )


def score_inspect_log(
    source: Path,
    destination: Path,
    *,
    evals_dir: Path = Path("evals"),
) -> InspectScoringSummary:
    """Score a saved candidate run without making provider calls.

    Args:
        source: An original gmuse candidate log on the local filesystem.
        destination: A new, distinct path ending in ``.eval``.
        evals_dir: Directory containing the suite and case assets.

    Returns:
        Scoring counts and the path of the new Inspect log.

    Raises:
        InspectScoringError: If the source or its suite cannot be used, or
            the destination cannot be reserved or written.
    """
    source, destination = _paths(source, destination)
    log, samples = _candidate_records(source, evals_dir)
    with _reserve_destination(destination):
        _publish(_attach_scores(log, samples, DETERMINISTIC_SCORER_NAME), destination)
    return _summary(samples, destination)
