"""Tests for comparing labeled calibration examples with mocked judge outputs."""

from dataclasses import replace
from json import dumps, loads
from pathlib import Path
from typing import Any, cast

import pytest

from tools.evals.gmuse_evals import judge
from tools.evals.gmuse_evals.calibration import (
    CALIBRATION_SCHEMA_VERSION,
    CalibrationExample,
    compatible_calibration_report_id,
    run_calibration,
)
from tools.evals.gmuse_evals.git_reconstruct import reconstruct_fixture
from tools.evals.gmuse_evals.inspect_adapter import stable_asset_digest
from tools.evals.gmuse_evals.judge import JudgeConfiguration, JudgePrompt
from tools.evals.gmuse_evals.taxonomy import JudgeHardFailureGateName, UsabilityLabel
from tools.evals.gmuse_evals.validate import validate_suite

ASSETS = Path(__file__).resolve().parents[2] / "evals"
CONFIGURATION = JudgeConfiguration(judge_provider="mock", judge_model="mock/judge")


@pytest.fixture
def example() -> CalibrationExample:
    suite = validate_suite(ASSETS, "smoke")
    case = next(
        case for case in suite.resolved_cases if case.case.id == "injection-comment"
    )
    with reconstruct_fixture(case.fixture) as repository:
        return CalibrationExample(
            example_id="review-one",
            resolved_case=case,
            staged_diff=repository.staged_diff.raw_diff,
            context={},
            generated_message="Cover untrusted fixture comments",
            format_name="freeform",
            max_chars=80,
            expected_usability="usable",
            expected_scores={
                "accuracy": 4,
                "message_quality": 4,
                "style_context_fit": None,
            },
            candidate_provider="candidate-provider",
            candidate_model="private-model-tag",
        )


def _response(
    configuration: JudgeConfiguration,
    prompt: JudgePrompt,
) -> str:
    assert configuration == CONFIGURATION
    assert "Cover untrusted fixture comments" in prompt.user_prompt
    assert "private-model-tag" not in prompt.user_prompt
    assert "candidate-provider" not in prompt.user_prompt
    return dumps(
        {
            "judge_output_schema_version": 1,
            "scores": {"accuracy": 4, "message_quality": 3, "style_context_fit": None},
            "usability": "usable",
            "hard_failure_findings": [],
            "quality_errors": [],
            "rationales": {
                "accuracy": "Matches the staged change.",
                "message_quality": "Room for a clearer description.",
                "style_context_fit": None,
                "usability": "Usable.",
            },
        }
    )


def _report(example: CalibrationExample) -> dict[str, Any]:
    return loads(
        dumps(
            run_calibration(
                [example],
                CONFIGURATION,
                expected_label_version="labels-001",
                provider_call=_response,
            )
        )
    )


def test_calibration_compares_expected_and_observed_labels(
    example: CalibrationExample,
) -> None:
    report = _report(example)
    assert report["calibration_schema_version"] == CALIBRATION_SCHEMA_VERSION
    assert report["calibration_case_count"] == 1
    assert report["expected_label_version"] == "labels-001"
    assert report["judge_configuration"] == CONFIGURATION.model_dump(mode="json")
    assert report["rubric_identity"] == {
        "id": example.resolved_case.rubric.id,
        "revision": example.resolved_case.rubric.revision,
        "digest": stable_asset_digest(example.resolved_case.rubric),
    }
    assert report["scoring_profile_identity"]["digest"] == stable_asset_digest(
        example.resolved_case.scoring_profile
    )
    [row] = report["examples"]
    assert row["expected_labels"]["scores"]["message_quality"] == 4
    assert row["judge_result"]["scores"]["message_quality"] == 3
    assert row["agreement"] == {
        "accuracy": True,
        "message_quality": False,
        "style_context_fit": True,
        "hard_failure": True,
        "usability": True,
    }
    assert report["agreement_by_dimension"]["accuracy"] == {
        "compared_count": 1,
        "matched_count": 1,
        "rate": 1.0,
    }
    assert report["agreement_by_dimension"]["message_quality"]["rate"] == 0.0
    assert report["usability_agreement"]["rate"] == 1.0
    assert report["parse_failure_count"] == 0
    assert report["operational_failure_count"] == 0
    assert report["bias_controls"]["candidate_identity_hidden"] is True


def test_failed_judge_attempts_preserve_labels_and_do_not_dilute_agreement(
    example: CalibrationExample,
) -> None:
    responses = iter(
        ("malformed diagnostic text", TimeoutError("private detail"), None)
    )

    def respond(configuration: JudgeConfiguration, prompt: JudgePrompt) -> str:
        response = next(responses)
        if isinstance(response, Exception):
            raise response
        return _response(configuration, prompt) if response is None else response

    report = run_calibration(
        [
            example,
            replace(example, example_id="timeout"),
            replace(
                example,
                example_id="scored",
                expected_scores={},
                expected_usability="unusable",
                expected_hard_failure_findings=("privacy_leak",),
            ),
        ],
        CONFIGURATION,
        expected_label_version="labels-001",
        provider_call=respond,
    )
    assert report["parse_failure_count"] == report["operational_failure_count"] == 1
    for row, category in zip(report["examples"], ("judge_parse_error", "timeout")):
        assert row["judge_result"] is None
        assert row["agreement"] is None
        assert row["judge_operational_error"]["category"] == category
        assert row["expected_labels"]["usability"] == "usable"
    assert report["agreement_by_dimension"]["accuracy"]["rate"] is None
    for summary in ("usability_agreement", "hard_failure_agreement"):
        assert report[summary] == {"compared_count": 1, "matched_count": 0, "rate": 0.0}
    assert "malformed diagnostic text" not in dumps(report)
    assert "private detail" not in dumps(report)


def test_explicit_diagnostic_reason_enables_candidate_identity(
    example: CalibrationExample,
) -> None:
    def respond(configuration: JudgeConfiguration, prompt: JudgePrompt) -> str:
        assert "candidate-provider" in prompt.user_prompt
        assert "private-model-tag" in prompt.user_prompt
        return "invalid diagnostic response"

    report = run_calibration(
        [example],
        CONFIGURATION,
        expected_label_version="labels-001",
        provider_call=respond,
        identity_inclusion_reason="Check model self-preference.",
    )
    assert report["bias_controls"] == {
        "candidate_identity_hidden": False,
        "candidate_identity_inclusion_reason": "Check model self-preference.",
    }


@pytest.mark.parametrize(
    ("key", "updates"),
    [
        ("judge_configuration", {"judge_prompt_version": 2}),
        ("judge_configuration", {"judge_model": "mock/new-judge"}),
        ("judge_configuration", {"temperature": 0.8}),
        ("rubric_identity", {"id": "other"}),
        ("rubric_identity", {"revision": 2}),
        ("rubric_identity", {"digest": "other"}),
        ("scoring_profile_identity", {"revision": 2}),
        ("scoring_profile_identity", {"digest": "other"}),
        ("bias_controls", {"candidate_identity_hidden": False}),
    ],
)
def test_report_compatibility_requires_configuration_assets_and_controls(
    example: CalibrationExample,
    key: str,
    updates: dict[str, object],
) -> None:
    report = _report(example)
    current = {
        name: dict(report[name])
        for name in (
            "judge_configuration",
            "rubric_identity",
            "scoring_profile_identity",
            "bias_controls",
        )
    }
    assert (
        compatible_calibration_report_id(report, **current)
        == report["calibration_report_id"]
    )
    current[key].update(updates)
    assert compatible_calibration_report_id(report, **current) is None


@pytest.mark.parametrize(
    "updates",
    [
        {"calibration_schema_version": 2},
        {"calibration_schema_version": True},
        {"calibration_report_id": ""},
        {"bias_controls": {}},
    ],
)
def test_unsupported_report_does_not_link(
    example: CalibrationExample, updates: dict[str, object]
) -> None:
    report = _report(example)
    assert (
        compatible_calibration_report_id(
            {**report, **updates},
            judge_configuration=report["judge_configuration"],
            rubric_identity=report["rubric_identity"],
            scoring_profile_identity=report["scoring_profile_identity"],
            bias_controls=report["bias_controls"],
        )
        is None
    )


def test_calibration_validates_examples_before_calling_judge(
    example: CalibrationExample,
) -> None:
    case = example.resolved_case

    def never_called(configuration: JudgeConfiguration, prompt: JudgePrompt) -> str:
        pytest.fail("invalid calibration attempted a judge call")

    mixed_case = replace(
        case, rubric=case.rubric.model_copy(update={"notes": "changed rubric content"})
    )
    mixed_example = replace(example, example_id="mixed", resolved_case=mixed_case)
    examples_and_errors = [
        ([example, mixed_example], "same rubric and scoring profile"),
        ([example, example], "IDs must be unique"),
        ([], "requires examples"),
        ([replace(example, example_id=" ")], "IDs must be non-empty"),
        ([replace(example, expected_scores={"accuracy": None})], "explicit null"),
        (
            [replace(example, expected_scores={"accuracy": True})],
            "dimensions and scale",
        ),
        (
            [replace(example, expected_usability=cast(UsabilityLabel, "unknown"))],
            "usability label",
        ),
        (
            [
                replace(
                    example,
                    expected_hard_failure_findings=(
                        cast(JudgeHardFailureGateName, "other"),
                    ),
                )
            ],
            "hard-failure labels",
        ),
        ([replace(example, staged_diff="invalid diff")], "does not match the fixture"),
    ]
    for examples, error in examples_and_errors:
        with pytest.raises(ValueError, match=error):
            run_calibration(
                examples,
                CONFIGURATION,
                expected_label_version="labels-001",
                provider_call=never_called,
            )


def test_live_calibration_requires_confirmation_and_cap(
    example: CalibrationExample, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempted = []

    def provider(configuration: JudgeConfiguration, prompt: JudgePrompt) -> str:
        attempted.append(prompt)
        return _response(configuration, prompt)

    monkeypatch.setattr(judge, "default_judge_provider", provider)
    with pytest.raises(ValueError, match="confirmation and a positive sample cap"):
        run_calibration([example], CONFIGURATION, expected_label_version="labels-001")
    with pytest.raises(ValueError, match="exceed the sample cap"):
        run_calibration(
            [example, replace(example, example_id="another")],
            CONFIGURATION,
            expected_label_version="labels-001",
            confirmed=True,
            limit_samples=1,
        )
    assert not attempted
    report = run_calibration(
        [example],
        CONFIGURATION,
        expected_label_version="labels-001",
        confirmed=True,
        limit_samples=1,
    )
    assert len(attempted) == report["calibration_case_count"] == 1
