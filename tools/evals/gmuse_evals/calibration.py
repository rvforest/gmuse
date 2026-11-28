"""Compare versioned human labels with the structured judge output."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, get_args
from uuid import uuid4

from . import judge
from .inspect_adapter import stable_asset_digest
from .judge import (
    JudgeConfiguration,
    JudgeOperationalError,
    JudgeProvider,
    build_judge_prompt,
    judge_result_metadata,
    run_judge,
)
from .results import ResolvedCase
from .taxonomy import RATING_MAX, RATING_MIN, JudgeHardFailureGateName, UsabilityLabel

CALIBRATION_SCHEMA_VERSION = 1
_DIMENSIONS = ("accuracy", "message_quality", "style_context_fit")


@dataclass(frozen=True, slots=True, kw_only=True)
class CalibrationExample:
    """A manually labeled candidate and the evidence needed for judging it.

    An omitted expected score is unannotated. An explicit null score means the
    dimension is inapplicable. An empty findings tuple means no hard failure.
    """

    example_id: str
    resolved_case: ResolvedCase
    staged_diff: str
    context: Mapping[str, object]
    generated_message: str
    format_name: str
    max_chars: int | None
    expected_usability: UsabilityLabel
    expected_hard_failure_findings: tuple[JudgeHardFailureGateName, ...] = ()
    expected_scores: Mapping[str, int | None] = field(default_factory=dict)
    candidate_provider: str | None = None
    candidate_model: str | None = None


def _asset_identities(case: ResolvedCase) -> dict[str, dict[str, object]]:
    return {
        kind: {
            "id": asset.id,
            "revision": asset.revision,
            "digest": stable_asset_digest(asset),
        }
        for kind, asset in (
            ("rubric_identity", case.rubric),
            ("scoring_profile_identity", case.scoring_profile),
        )
    }


def _agreement(matches: Sequence[bool]) -> dict[str, int | float | None]:
    matched_count = sum(matches)
    return {
        "compared_count": len(matches),
        "matched_count": matched_count,
        "rate": matched_count / len(matches) if matches else None,
    }


def _validate_example(example: CalibrationExample) -> None:
    if not example.example_id.strip():
        raise ValueError("calibration example IDs must be non-empty")
    if example.expected_usability not in get_args(UsabilityLabel):
        raise ValueError("calibration usability label must belong to the taxonomy")
    if set(example.expected_hard_failure_findings).difference(
        get_args(JudgeHardFailureGateName)
    ):
        raise ValueError("calibration hard-failure labels must belong to the taxonomy")
    for dimension, score in example.expected_scores.items():
        if dimension not in _DIMENSIONS or (
            score is not None
            and (type(score) is not int or not RATING_MIN <= score <= RATING_MAX)
        ):
            raise ValueError(
                "calibration scores must use the supported dimensions and scale"
            )
        if score is None and dimension != "style_context_fit":
            raise ValueError("only style/context fit can have an explicit null score")
    if (
        sha256(example.staged_diff.encode()).hexdigest()
        != example.resolved_case.fixture.expected_staged_diff_sha256
    ):
        raise ValueError("calibration staged diff does not match the fixture")


def run_calibration(
    examples: Sequence[CalibrationExample],
    configuration: JudgeConfiguration,
    *,
    expected_label_version: str,
    provider_call: JudgeProvider | None = None,
    limit_samples: int | None = None,
    confirmed: bool = False,
    identity_inclusion_reason: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Run labeled examples through the same prompt and parser as scoring.

    Args:
        examples: Labeled candidates sharing the exact rubric and profile.
        configuration: The judge configuration used for all examples.
        expected_label_version: Maintainer-provided annotation revision.
        provider_call: Optional judge callback for offline testing. The default
            uses the configured live provider.
        limit_samples: Positive attempt cap required with the live provider.
            It must cover the entire calibration set.
        confirmed: Must be true when using the default live provider.
        identity_inclusion_reason: Reason for including candidate identity in a
            diagnostic run. Omit this argument to hide identity.
        notes: Optional maintainer notes for the report.

    Returns:
        A versioned JSON-compatible dictionary. Rates compare successful judge
        outputs with annotated dimensions only. Failed attempts are counted
        separately and retain their expected labels.

    Raises:
        ValueError: If live calibration lacks confirmation or a positive cap
            covering the set, the set is empty, IDs repeat, the label version
            is blank, rubric or profile identities differ, or labels or
            evidence are invalid.
    """
    if provider_call is None or provider_call is judge.default_judge_provider:
        if not confirmed or type(limit_samples) is not int or limit_samples <= 0:
            raise ValueError(
                "live calibration requires confirmation and a positive sample cap"
            )
        if len(examples) > limit_samples:
            raise ValueError("calibration examples exceed the sample cap")
        provider_call = judge.default_judge_provider
    if not examples or not expected_label_version.strip():
        raise ValueError("calibration requires examples and an expected label version")
    if len({example.example_id for example in examples}) != len(examples):
        raise ValueError("calibration example IDs must be unique")
    identities = _asset_identities(examples[0].resolved_case)
    if any(
        _asset_identities(example.resolved_case) != identities
        for example in examples[1:]
    ):
        raise ValueError(
            "calibration examples must use the same rubric and scoring profile"
        )
    for example in examples:
        _validate_example(example)

    prompts = [
        build_judge_prompt(
            staged_diff=example.staged_diff,
            context=example.context,
            resolved_case=example.resolved_case,
            generated_message=example.generated_message,
            format_name=example.format_name,
            max_chars=example.max_chars,
            candidate_provider=example.candidate_provider,
            candidate_model=example.candidate_model,
            identity_inclusion_reason=identity_inclusion_reason,
        )
        for example in examples
    ]
    rows: list[dict[str, Any]] = []
    matches: dict[str, list[bool]] = {
        dimension: [] for dimension in (*_DIMENSIONS, "usability", "hard_failure")
    }
    operational_failure_count = 0
    parse_failure_count = 0
    for example, prompt in zip(examples, prompts, strict=True):
        expected_scores = dict(example.expected_scores)
        row: dict[str, Any] = {
            "example_id": example.example_id,
            "case_id": example.resolved_case.case.id,
            "case_revision": example.resolved_case.case.revision,
            "expected_labels": {
                "scores": expected_scores,
                "usability": example.expected_usability,
                "hard_failure_findings": list(example.expected_hard_failure_findings),
            },
            "judge_result": None,
            "judge_operational_error": None,
            "agreement": None,
        }
        rows.append(row)
        result = run_judge(configuration, prompt, provider_call=provider_call)
        if isinstance(result, JudgeOperationalError):
            row["judge_operational_error"] = result.model_dump(mode="json")
            if result.category == "judge_parse_error":
                parse_failure_count += 1
            else:
                operational_failure_count += 1
            continue
        observed = judge_result_metadata(result, prompt)
        row["judge_result"] = observed
        agreement = {
            dimension: expected_scores[dimension] == observed["scores"][dimension]
            for dimension in _DIMENSIONS
            if dimension in expected_scores
        }
        agreement["usability"] = example.expected_usability == result.usability
        agreement["hard_failure"] = set(example.expected_hard_failure_findings) == set(
            result.hard_failure_findings
        )
        row["agreement"] = agreement
        for dimension, matched in agreement.items():
            matches[dimension].append(matched)

    return {
        "calibration_schema_version": CALIBRATION_SCHEMA_VERSION,
        "calibration_report_id": uuid4().hex,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "judge_configuration": configuration.model_dump(mode="json"),
        **identities,
        "calibration_case_count": len(examples),
        "expected_label_version": expected_label_version,
        "agreement_by_dimension": {
            dimension: _agreement(matches[dimension]) for dimension in _DIMENSIONS
        },
        "parse_failure_count": parse_failure_count,
        "operational_failure_count": operational_failure_count,
        "hard_failure_agreement": _agreement(matches["hard_failure"]),
        "usability_agreement": _agreement(matches["usability"]),
        "bias_controls": prompts[0].input_controls.model_dump(mode="json"),
        "notes": notes,
        "examples": rows,
    }


def compatible_calibration_report_id(
    report: Mapping[str, object] | None,
    *,
    judge_configuration: Mapping[str, object],
    rubric_identity: Mapping[str, object],
    scoring_profile_identity: Mapping[str, object],
    bias_controls: Mapping[str, object],
) -> str | None:
    """Return the report ID if it describes the current judge and assets.

    Args:
        report: A previously generated calibration report, if provided.
        judge_configuration: Serialized configuration for the current judge.
        rubric_identity: Current rubric ID, revision, and content digest.
        scoring_profile_identity: Current profile ID, revision, and digest.
        bias_controls: Input controls for the current judge. Identity visibility
            must match the calibration run.

    Returns:
        The supplied report ID, or None when no compatible report exists.
    """
    if (
        report is None
        or type(report.get("calibration_schema_version")) is not int
        or report["calibration_schema_version"] != CALIBRATION_SCHEMA_VERSION
        or report.get("judge_configuration") != judge_configuration
        or report.get("rubric_identity") != rubric_identity
        or report.get("scoring_profile_identity") != scoring_profile_identity
    ):
        return None
    expected_hidden = bias_controls.get("candidate_identity_hidden")
    report_controls = report.get("bias_controls")
    if (
        type(expected_hidden) is not bool
        or not isinstance(report_controls, Mapping)
        or report_controls.get("candidate_identity_hidden") is not expected_hidden
    ):
        return None
    report_id = report.get("calibration_report_id")
    return report_id if isinstance(report_id, str) and report_id.strip() else None
