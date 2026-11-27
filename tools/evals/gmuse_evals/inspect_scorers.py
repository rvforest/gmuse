"""Score saved candidate samples and write a separate Inspect log.

For offline scoring, ``score_inspect_log`` applies deterministic checks and
writes the results directly. For live judging, ``prepare_inspect_judge_plan``
verifies evidence, reuses compatible judgments, and counts the new calls.
After confirmation, ``execute_inspect_judge_plan`` runs those calls and writes
the results. Both paths use Inspect to attach the completed scoring records.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any

from . import judge
from .logs import EVAL_SCHEMA_VERSION, independent_run_id
from .run_plan import Guardrails
from .scoring import (
    JUDGE_RESPONSE_DIRECTORY,
    apply_judge_scoring,
    prepare_judge_scoring,
    record_judge_result,
    score_deterministic,
)
from .scoring_evidence import SCORING_EVIDENCE_DIRECTORY, read_private_evidence
from .taxonomy import SCORING_SCHEMA_VERSION, TAXONOMY_VERSION
from .validate import validate_suite

if TYPE_CHECKING:
    from inspect_ai.log import EvalLog

DETERMINISTIC_SCORER_NAME = "gmuse_deterministic"
JUDGE_SCORER_NAME = "gmuse_judge"
_SCORING_RUN_KEY = "gmuse_scoring"
_REUSE_FIELDS = (
    "source",
    "assessment_evidence_ref",
    "rubric_identity",
    "scoring_profile_identity",
    "fixture_asset_digest",
    "judge_input_controls",
)


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
    judge_calls: int = 0
    judge_failures: int = 0
    interrupted: bool = False


@dataclass(slots=True)
class _ScoringSample:
    """A sample's scoring record and any prompt scheduled for a new call.

    During planning, ``prompt`` is ``None`` for offline, skipped, unscorable,
    and reused samples. The record stores the outcome or reason.
    """

    record: dict[str, Any]
    prompt: judge.JudgePrompt | None = None


@dataclass(frozen=True, slots=True)
class InspectJudgePlan:
    """Verified candidate inputs and a fixed, budgeted judge configuration."""

    source: Path
    destination: Path
    log: EvalLog
    samples: dict[tuple[int | str, int], _ScoringSample]
    configuration: judge.JudgeConfiguration
    guardrails: Guardrails
    compatibility: dict[str, object]
    scoring_run_id: str

    @property
    def planned_calls(self) -> int:
        """Return the number of eligible samples without a reusable result."""
        return sum(sample.prompt is not None for sample in self.samples.values())

    @property
    def reused_count(self) -> int:
        """Return the number of results carried from the previous scoring log."""
        return sum(
            bool(sample.record.get("reused_from_scoring_run_id"))
            for sample in self.samples.values()
        )

    @property
    def rubric_revisions(self) -> tuple[str, ...]:
        """Return the rubric IDs and revisions represented in the plan."""
        return tuple(
            sorted(
                {
                    f"{identity['id']}@{identity['revision']}"
                    for sample in self.samples.values()
                    if (identity := sample.record["rubric_identity"])
                }
            )
        )


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


def _read_log(path: Path, *, digest: bool = False) -> tuple[EvalLog, str | None]:
    from inspect_ai.log import read_eval_log

    try:
        with path.open("rb") as stream:
            sha256 = (
                hashlib.file_digest(stream, "sha256").hexdigest() if digest else None
            )
            stream.seek(0)
            return read_eval_log(stream), sha256
    except Exception as error:
        raise InspectScoringError("Cannot read the requested Inspect log.") from error


def _candidate_records(
    source: Path,
    evals_dir: Path,
    *,
    configuration: judge.JudgeConfiguration | None = None,
    diagnostic_hard_failures: bool = False,
    identity_inclusion_reason: str | None = None,
    equivalent_models: tuple[tuple[str, str], ...] = (),
) -> tuple[EvalLog, str | None, dict[tuple[int | str, int], _ScoringSample]]:
    log, source_digest = _read_log(source, digest=configuration is not None)
    run_metadata = log.metadata or {}
    if run_metadata.get("gmuse_eval_schema_version") != EVAL_SCHEMA_VERSION:
        raise InspectScoringError(
            "Unsupported gmuse runner log schema. Rerun the eval with the current runner."
        )
    if not log.samples:
        raise InspectScoringError("The Inspect log has no original candidate samples.")
    if log.eval.model_roles or any(
        {DETERMINISTIC_SCORER_NAME, JUDGE_SCORER_NAME}.intersection(sample.scores or {})
        for sample in log.samples
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
        prompt = (
            prepare_judge_scoring(
                record,
                sample.metadata,
                run_metadata,
                resolved,
                source_log=source,
                configuration=configuration,
                diagnostic_hard_failures=diagnostic_hard_failures,
                identity_inclusion_reason=identity_inclusion_reason,
                equivalent_models=equivalent_models,
            )
            if configuration is not None
            else None
        )
        key = (sample.id, sample.epoch)
        if key in records:
            raise InspectScoringError(
                "The candidate log contains duplicate sample identities."
            )
        records[key] = _ScoringSample(record, prompt)
    return log, source_digest, records


def _reuse_completed(
    plan: InspectJudgePlan,
    previous_path: Path,
) -> None:
    previous, _ = _read_log(previous_path)
    manifest = (previous.metadata or {}).get(_SCORING_RUN_KEY)
    if (
        not isinstance(manifest, dict)
        or manifest.get("compatibility") != plan.compatibility
        or not isinstance(manifest.get("scoring_run_id"), str)
        or not previous.samples
    ):
        raise InspectScoringError(
            "The resume log is incompatible with the candidate log or judge configuration."
        )
    for previous_sample in previous.samples:
        sample = plan.samples.get((previous_sample.id, previous_sample.epoch))
        prior_score = (previous_sample.scores or {}).get(JUDGE_SCORER_NAME)
        prior = prior_score.metadata if prior_score is not None else None
        if (
            sample is None
            or sample.prompt is None
            or not isinstance(prior, dict)
            or prior.get("judge_status") != "completed"
            or prior.get("scoring_run_id") != manifest["scoring_run_id"]
            or any(prior.get(key) != sample.record[key] for key in _REUSE_FIELDS)
        ):
            continue
        judged = prior.get("judge_result")
        if not isinstance(judged, dict):
            continue
        raw = judged.get("raw_response_metadata")
        if not isinstance(raw, dict) or not isinstance(raw.get("sha256"), str):
            continue
        try:
            payload = read_private_evidence(
                plan.source.parent / JUDGE_RESPONSE_DIRECTORY, raw["sha256"]
            )
            result = judge.parse_judge_response(
                payload.decode("utf-8", errors="surrogatepass"),
                style_context_applicable=sample.prompt.style_context_applicable,
            )
        except (OSError, ValueError):
            continue
        locator = f"{JUDGE_RESPONSE_DIRECTORY}/{raw['sha256']}"
        expected = judge.judge_result_metadata(result, sample.prompt)
        expected["raw_response_metadata"]["locator"] = locator
        if expected != judged:
            continue
        record_judge_result(sample.record, sample.prompt, result, {"locator": locator})
        sample.record.update(
            judge_timing=prior.get("judge_timing"),
            reused_from_scoring_run_id=manifest["scoring_run_id"],
        )
        sample.prompt = None


def prepare_inspect_judge_plan(
    source: Path,
    destination: Path,
    *,
    configuration: judge.JudgeConfiguration,
    guardrails: Guardrails,
    evals_dir: Path = Path("evals"),
    diagnostic_hard_failures: bool = False,
    identity_inclusion_reason: str | None = None,
    equivalent_models: tuple[tuple[str, str], ...] = (),
    resume: Path | None = None,
) -> InspectJudgePlan:
    """Plan live judge scoring without calling a provider.

    Verify saved evidence and identify compatible results from the optional
    resume log before counting new calls. The plan requires a positive sample
    cap that covers those calls. Execution is serial. Configure the response
    token limit and timeout per call on the judge configuration.

    Raises:
        InspectScoringError: If the logs, destination, or judge options are
            invalid, or the new calls exceed the sample cap.
    """
    if not guardrails.configured():
        raise InspectScoringError(
            "Live judging requires an explicit positive --limit-samples."
        )
    if any(
        value is not None
        for value in (guardrails.max_tokens, guardrails.max_cost, guardrails.time_limit)
    ):
        raise InspectScoringError(
            "Run-wide token, cost, and time limits are unsupported by the direct judge "
            "provider path. Use --limit-samples, --max-tokens, and --timeout."
        )
    if guardrails.concurrency not in (None, 1):
        raise InspectScoringError("Live judge concurrency must be 1.")
    if identity_inclusion_reason is not None:
        identity_inclusion_reason = identity_inclusion_reason.strip()
        if not identity_inclusion_reason:
            raise InspectScoringError(
                "Diagnostic identity inclusion requires a nonblank reason."
            )
    source, destination = _paths(source, destination)
    log, digest, samples = _candidate_records(
        source,
        evals_dir,
        configuration=configuration,
        diagnostic_hard_failures=diagnostic_hard_failures,
        identity_inclusion_reason=identity_inclusion_reason,
        equivalent_models=equivalent_models,
    )
    plan = InspectJudgePlan(
        source=source,
        destination=destination,
        log=log,
        samples=samples,
        configuration=configuration.model_copy(deep=True),
        guardrails=guardrails,
        compatibility={
            "source_sha256": digest,
            "scoring_schema_version": SCORING_SCHEMA_VERSION,
            "taxonomy_version": TAXONOMY_VERSION,
            "judge_configuration": configuration.model_dump(mode="json"),
            "diagnostic_hard_failures": diagnostic_hard_failures,
            "identity_inclusion_reason": identity_inclusion_reason,
            "equivalent_models": [
                list(identity) for identity in sorted(set(equivalent_models))
            ],
        },
        scoring_run_id=independent_run_id(log.metadata["suite_id"], "scoring"),
    )
    if resume is not None:
        _reuse_completed(plan, resume.expanduser())
    _check_call_count(plan)
    return plan


def _check_call_count(plan: InspectJudgePlan) -> None:
    limit = plan.guardrails.max_samples
    if limit is None or plan.planned_calls > limit:
        raise InspectScoringError(
            f"Planned judge calls {plan.planned_calls} exceed --limit-samples {limit}."
        )


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
    samples: dict[tuple[int | str, int], _ScoringSample],
    name: str,
) -> EvalLog:
    """Attach gmuse's precomputed results to the saved Inspect samples.

    The scorer looks up each record by sample ID and epoch. Inspect uses
    ``mockllm/deterministic`` as its local model context because all judge
    calls happen before this step.
    """
    from inspect_ai import score
    from inspect_ai.scorer import Score, Scorer, Target, scorer
    from inspect_ai.solver import TaskState

    @scorer(metrics=[], name=name)
    def gmuse_score() -> Scorer:
        async def score_sample(state: TaskState, target: Target) -> Score:
            result = samples[(state.sample_id, state.epoch)].record
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
    samples: dict[tuple[int | str, int], _ScoringSample],
    destination: Path,
    *,
    attempts: int = 0,
    interrupted: bool = False,
) -> InspectScoringSummary:
    records = [sample.record for sample in samples.values()]
    scored = sum(record["scoring_status"] == "scored" for record in records)
    return InspectScoringSummary(
        total=len(records),
        scored=scored,
        unscored=len(records) - scored,
        hard_failed=sum(bool(record["hard_failure_gates"]) for record in records),
        destination=destination,
        judge_calls=attempts,
        judge_failures=sum(
            record.get("judge_status") == "failed" for record in records
        ),
        interrupted=interrupted,
    )


def execute_inspect_judge_plan(
    plan: InspectJudgePlan,
    *,
    confirmed: bool = False,
    provider_call: judge.JudgeProvider | None = None,
) -> InspectScoringSummary:
    """Execute serial, confirmed judge calls and publish a native scored log.

    On keyboard interruption, publish completed results and explicit unattempted
    entries to support resume into a new destination.
    """
    if not confirmed:
        raise InspectScoringError(
            "Explicit confirmation is required before live judge calls."
        )
    if (
        plan.configuration.model_dump(mode="json")
        != plan.compatibility["judge_configuration"]
    ):
        raise InspectScoringError("The judge configuration changed after planning.")
    _check_call_count(plan)
    call = provider_call or judge.default_judge_provider
    attempts = 0
    interrupted = False
    with _reserve_destination(plan.destination):
        for sample in plan.samples.values():
            sample.record["scoring_run_id"] = plan.scoring_run_id
            rubric = sample.record["rubric_identity"] or {}
            sample.record["judge_configuration"].update(
                guardrails=plan.guardrails.as_dict(),
                rubric_revision=rubric.get("revision"),
            )
        try:
            for sample in plan.samples.values():
                if sample.prompt is not None:
                    try:
                        read_private_evidence(
                            plan.source.parent / SCORING_EVIDENCE_DIRECTORY,
                            sample.record["assessment_evidence_ref"]["sha256"],
                        )
                    except FileNotFoundError:
                        sample.record.update(
                            judge_status="unscorable",
                            unscored_reason="missing_assessment_evidence",
                        )
                        continue
                    except (OSError, ValueError):
                        sample.record.update(
                            judge_status="unscorable",
                            unscored_reason="invalid_assessment_evidence",
                        )
                        continue
                    attempts += 1
                    apply_judge_scoring(
                        sample.record,
                        sample.prompt,
                        plan.configuration,
                        response_directory=plan.source.parent
                        / JUDGE_RESPONSE_DIRECTORY,
                        provider_call=call,
                    )
        except KeyboardInterrupt:
            interrupted = True
        scored = _attach_scores(plan.log, plan.samples, JUDGE_SCORER_NAME)
        scored.eval.metadata = {
            **(scored.eval.metadata or {}),
            _SCORING_RUN_KEY: {
                "scoring_run_id": plan.scoring_run_id,
                "source_log_name": plan.source.name,
                "compatibility": plan.compatibility,
                "guardrails": plan.guardrails.as_dict(),
                "judge_calls": attempts,
                "interrupted": interrupted,
            },
        }
        _publish(scored, plan.destination)
    return _summary(
        plan.samples, plan.destination, attempts=attempts, interrupted=interrupted
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
    log, _, samples = _candidate_records(source, evals_dir)
    with _reserve_destination(destination):
        _publish(_attach_scores(log, samples, DETERMINISTIC_SCORER_NAME), destination)
    return _summary(samples, destination)
