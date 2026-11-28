"""Evaluate saved candidates with deterministic checks and a rubric judge."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gmuse.credentials import infer_provider_from_model

from . import judge
from .calibration import compatible_calibration_report_id
from .deterministic_checks import run_deterministic_checks
from .inspect_adapter import stable_asset_digest
from .results import ResolvedCase
from .scoring_evidence import (
    ScoringEvidenceError,
    recover_scoring_evidence,
    store_private_evidence,
)
from .taxonomy import SCORING_SCHEMA_VERSION, TAXONOMY_VERSION

JUDGE_RESPONSE_DIRECTORY = ".gmuse-judge-responses"

_SOURCE_SAMPLE_FIELDS = (
    "entry_id",
    "case_id",
    "case_revision",
    "fixture_id",
    "fixture_revision",
    "fixture_digest",
    "staged_diff_digest",
    "candidate_kind",
    "candidate_model",
    "generation_config",
    "prompt_hash",
    "prompt_sha256",
)


def _matches_case(sample: Mapping[str, object], case: ResolvedCase) -> bool:
    expected = {
        "case_id": case.case.id,
        "case_revision": case.case.revision,
        "fixture_id": case.fixture.id,
        "fixture_revision": case.fixture.revision,
        "fixture_digest": case.fixture.expected_staged_diff_sha256,
        "staged_diff_digest": case.fixture.expected_staged_diff_sha256,
        "rubric_id": case.rubric.id,
        "rubric_version": case.rubric.revision,
    }
    return all(sample.get(key) == value for key, value in expected.items())


def score_deterministic(
    sample_metadata: Mapping[str, object],
    run_metadata: Mapping[str, object],
    resolved_case: ResolvedCase | None,
) -> dict[str, Any]:
    """Describe offline scoring for a single saved Inspect candidate.

    Args:
        sample_metadata: Original runner metadata, including validation and output.
        run_metadata: Source run metadata containing the run and suite identity.
        resolved_case: Validated assets matching the source case, if available.

    Returns:
        JSON-compatible scoring metadata. The source sample retains its
        original output and validation. A hard failure yields unusable status.
        Subjective ratings remain empty in offline mode.

    Example:
        >>> score_deterministic({}, {}, None)["unscored_reason"]
        'missing_generated_message'
    """
    record: dict[str, Any] = {
        "scoring_schema_version": SCORING_SCHEMA_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "scoring_mode": "deterministic",
        "scoring_status": "unscored",
        "unscored_reason": None,
        "source": {
            "run_id": run_metadata.get("run_id"),
            "suite_id": run_metadata.get("suite_id"),
            "suite_version": run_metadata.get("suite_version"),
            **{key: sample_metadata.get(key) for key in _SOURCE_SAMPLE_FIELDS},
        },
        "rubric_identity": None,
        "scoring_profile_identity": None,
        "fixture_asset_digest": None,
        "assessment_evidence_ref": None,
        "deterministic_checks": [],
        "hard_failure_gates": [],
        "quality_errors": [],
        "operational_errors": [],
        "judge_configuration": None,
        "judge_result": None,
        "judge_operational_error": None,
        "judge_input_controls": None,
        "self_judged": None,
        "calibration_report_id": None,
        "effective_ratings": {
            "accuracy": None,
            "message_quality": None,
            "style_context_fit": None,
            "usability": None,
            "hard_failed": None,
            "derived_from": None,
        },
    }

    message = sample_metadata.get("generated_message")
    if not isinstance(message, str):
        record["unscored_reason"] = (
            "candidate_operational_failure"
            if sample_metadata.get("operational_error")
            else "missing_generated_message"
        )
        return record

    if resolved_case is None:
        record["unscored_reason"] = "case_assets_unavailable"
        return record
    if not _matches_case(sample_metadata, resolved_case):
        record["unscored_reason"] = "incompatible_case_assets"
        return record

    validation = sample_metadata.get("production_validation")
    if (
        not isinstance(validation, Mapping)
        or type(validation.get("valid")) is not bool
        or validation.get("category") == "operational"
    ):
        record["unscored_reason"] = "missing_production_validation"
        return record

    max_chars = sample_metadata.get("max_chars")
    if "max_chars" not in sample_metadata or (
        max_chars is not None and (type(max_chars) is not int or max_chars <= 0)
    ):
        record["unscored_reason"] = "invalid_max_chars"
        return record

    checks, gates = run_deterministic_checks(
        message=message,
        validation=validation,
        max_chars=max_chars,
        case=resolved_case,
    )
    rubric = resolved_case.rubric
    profile = resolved_case.scoring_profile
    record.update(
        scoring_status="scored",
        rubric_identity={
            "id": rubric.id,
            "revision": rubric.revision,
            "digest": stable_asset_digest(rubric),
        },
        scoring_profile_identity={
            "id": profile.id,
            "revision": profile.revision,
            "digest": stable_asset_digest(profile),
        },
        fixture_asset_digest=stable_asset_digest(resolved_case.fixture),
        deterministic_checks=[
            {**asdict(check), "quality_errors": list(check.quality_errors)}
            for check in checks
        ],
        hard_failure_gates=[asdict(gate) for gate in gates],
        quality_errors=sorted(
            {category for check in checks for category in check.quality_errors}
        ),
    )
    record["effective_ratings"].update(
        usability="unusable" if gates else None,
        hard_failed=bool(gates),
        derived_from="deterministic_checks",
    )
    return record


def prepare_judge_scoring(
    record: dict[str, Any],
    sample: Mapping[str, object],
    run_metadata: Mapping[str, object],
    resolved_case: ResolvedCase | None,
    *,
    source_log: Path,
    configuration: judge.JudgeConfiguration,
    diagnostic_hard_failures: bool,
    identity_inclusion_reason: str | None,
    equivalent_models: tuple[tuple[str, str], ...],
    calibration_report: Mapping[str, object] | None,
) -> judge.JudgePrompt | None:
    """Prepare a verified judge request and enrich a deterministic score record.

    A missing request always leaves an explicit eligibility or unscorable reason
    on the record. This function performs local verification without calling a judge.
    """
    record.update(
        scoring_mode="judge",
        judge_status="unscorable",
        judge_configuration=configuration.model_dump(mode="json"),
    )
    if record["scoring_status"] == "unscored" or resolved_case is None:
        return None
    if record["hard_failure_gates"] and not diagnostic_hard_failures:
        record["judge_status"] = "skipped_hard_failure"
        return None
    try:
        evidence = recover_scoring_evidence(
            source_log, sample, run_metadata, resolved_case
        )
    except ScoringEvidenceError as error:
        record.update(scoring_status="unscored", unscored_reason=error.reason)
        return None

    message = sample.get("generated_message")
    format_name = sample.get("format")
    max_chars = sample.get("max_chars")
    generation = sample.get("generation_config")
    if (
        not isinstance(message, str)
        or not isinstance(format_name, str)
        or (max_chars is not None and type(max_chars) is not int)
        or not isinstance(generation, Mapping)
        or generation.get("format") != format_name
        or generation.get("max_chars") != max_chars
    ):
        record.update(
            scoring_status="unscored", unscored_reason="invalid_generation_context"
        )
        return None
    model = sample.get("candidate_model")
    candidate_model = model if isinstance(model, str) else None
    candidate_provider = (
        infer_provider_from_model(candidate_model) if candidate_model else None
    )
    if identity_inclusion_reason and candidate_model is None:
        record.update(
            scoring_status="unscored", unscored_reason="missing_candidate_identity"
        )
        return None
    prompt = judge.build_judge_prompt(
        staged_diff=evidence.staged_diff,
        context=evidence.context,
        resolved_case=resolved_case,
        generated_message=message,
        format_name=format_name,
        max_chars=max_chars,
        candidate_provider=candidate_provider,
        candidate_model=candidate_model,
        identity_inclusion_reason=identity_inclusion_reason,
    )
    flags = judge.judge_identity_flags(
        configuration,
        candidate_provider=candidate_provider,
        candidate_model=candidate_model,
        equivalent_models=equivalent_models,
    )
    record.update(
        scoring_status="unscored",
        unscored_reason="judge_not_attempted",
        judge_status="pending",
        rubric_identity=evidence.rubric_identity,
        scoring_profile_identity=evidence.scoring_profile_identity,
        assessment_evidence_ref=evidence.reference,
        judge_input_controls=prompt.input_controls.model_dump(mode="json"),
        self_judged=flags.self_judged,
        same_model_family=flags.same_model_family,
    )
    record["calibration_report_id"] = compatible_calibration_report_id(
        calibration_report,
        judge_configuration=configuration.model_dump(mode="json"),
        rubric_identity=evidence.rubric_identity,
        scoring_profile_identity=evidence.scoring_profile_identity,
        bias_controls={
            "candidate_identity_hidden": prompt.input_controls.candidate_identity_hidden
        },
    )
    return prompt


def apply_judge_scoring(
    record: dict[str, Any],
    prompt: judge.JudgePrompt,
    configuration: judge.JudgeConfiguration,
    *,
    response_directory: Path,
    provider_call: judge.JudgeProvider,
) -> None:
    """Attempt one configured judge call and record its result or failure."""
    started = datetime.now(timezone.utc).isoformat()
    judged = judge.run_judge(configuration, prompt, provider_call=provider_call)
    finished = datetime.now(timezone.utc).isoformat()
    record["judge_timing"] = {"started_at": started, "finished_at": finished}
    response_ref = None
    if judged.raw_response is not None:
        try:
            digest = store_private_evidence(
                response_directory,
                judged.raw_response.encode("utf-8", errors="surrogatepass"),
            )
            response_ref = {
                "sha256": digest,
                "locator": f"{response_directory.name}/{digest}",
            }
        except (OSError, UnicodeError):
            record.update(
                judge_status="failed",
                unscored_reason="judge_response_storage_error",
                operational_errors=["unknown_error"],
                judge_operational_error={
                    "category": "unknown_error",
                    "message": "Could not preserve the judge response.",
                },
            )
            return
    if isinstance(judged, judge.JudgeOperationalError):
        metadata = judged.model_dump(mode="json")
        if response_ref is not None:
            metadata["raw_response_metadata"] = response_ref
        record.update(
            judge_status="failed",
            unscored_reason=judged.category,
            operational_errors=[judged.category],
            judge_operational_error=metadata,
        )
        return

    record_judge_result(record, prompt, judged, response_ref or {})


def record_judge_result(
    record: dict[str, Any],
    prompt: judge.JudgePrompt,
    judged: judge.JudgeResult,
    response_ref: Mapping[str, str],
) -> None:
    """Apply a validated live or reused result with hard gate precedence."""
    metadata = judge.judge_result_metadata(judged, prompt)
    metadata["raw_response_metadata"].update(response_ref)
    gates = [
        {
            "gate": gate,
            "source": "judge_result",
            "evidence": "The rubric judge identified this hard failure.",
        }
        for gate in judged.hard_failure_findings
    ]
    record["hard_failure_gates"].extend(gates)
    hard_failed = bool(record["hard_failure_gates"])
    record.update(
        scoring_status="scored",
        unscored_reason=None,
        judge_status="completed",
        quality_errors=sorted(
            set(record["quality_errors"]) | set(judged.quality_errors)
        ),
        judge_result=metadata,
        effective_ratings={
            **metadata["scores"],
            "usability": "unusable" if hard_failed else judged.usability,
            "hard_failed": hard_failed,
            "derived_from": "judge_result",
        },
    )
