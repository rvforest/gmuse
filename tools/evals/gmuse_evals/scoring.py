"""Evaluate saved candidates with deterministic checks."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from .deterministic_checks import run_deterministic_checks
from .inspect_adapter import stable_asset_digest
from .results import ResolvedCase
from .taxonomy import SCORING_SCHEMA_VERSION, TAXONOMY_VERSION


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
