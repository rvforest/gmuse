"""Tests for offline checks on recorded candidate output."""

from dataclasses import asdict, replace

import pytest
from pydantic import ValidationError

from tools.evals.gmuse_evals.deterministic_checks import run_deterministic_checks
from tools.evals.gmuse_evals.fixture_models import EvalFixture
from tools.evals.gmuse_evals.results import ResolvedCase
from tools.evals.gmuse_evals.validate import validate_suite


@pytest.fixture(scope="module")
def safety_case() -> ResolvedCase:
    return next(
        case
        for case in validate_suite("evals", "core").resolved_cases
        if case.case.id == "injection-comment"
    )


def test_uses_recorded_validation_without_copying_its_message() -> None:
    validation = {"valid": False, "message": "Got: test-sensitive-candidate"}
    checks, gates = run_deterministic_checks(
        message="test-sensitive-candidate", validation=validation, max_chars=None
    )

    assert checks[0].check_id == "production_validation"
    assert checks[0].status == "fail"
    assert checks[0].quality_errors == ("validation_error",)
    assert [gate.gate for gate in gates] == ["production_validation_failed"]
    assert "test-sensitive-candidate" not in repr((checks, gates))
    assert validation["message"] == "Got: test-sensitive-candidate"


@pytest.mark.parametrize(
    ("message", "validation"),
    [
        (None, {"valid": False}),
        ("fix: resolve bug", None),
        ("fix: resolve bug", {}),
        ("fix: resolve bug", {"valid": False, "category": "operational"}),
    ],
)
def test_missing_or_unreached_validation_does_not_fail(
    message: str | None, validation: dict[str, object] | None
) -> None:
    checks, gates = run_deterministic_checks(
        message=message, validation=validation, max_chars=None
    )

    assert checks[0].status == "not_applicable"
    assert checks[0].evidence
    assert not gates


def test_recorded_rejection_of_empty_output_is_a_failure() -> None:
    checks, gates = run_deterministic_checks(
        message="", validation={"valid": False}, max_chars=72
    )

    assert checks[0].status == "fail"
    assert [gate.gate for gate in gates] == ["production_validation_failed"]


def test_no_candidate_output_leaves_all_checks_inapplicable(
    safety_case: ResolvedCase,
) -> None:
    checks, gates = run_deterministic_checks(
        message=None,
        validation={"valid": False},
        max_chars=1,
        case=safety_case,
    )

    assert {check.status for check in checks} == {"not_applicable"}
    assert not gates


@pytest.mark.parametrize(
    ("max_chars", "status"),
    [(None, "not_applicable"), (5, "pass"), (4, "fail")],
)
def test_length_counts_unicode_characters_and_whitespace(
    max_chars: int | None, status: str
) -> None:
    checks, gates = run_deterministic_checks(
        message=" 💡e\u0301\n", validation={"valid": True}, max_chars=max_chars
    )

    length = next(check for check in checks if check.check_id == "max_chars")
    assert length.status == status
    assert [gate.gate for gate in gates] == (
        ["max_chars_exceeded"] if status == "fail" else []
    )


def test_marker_matches_are_literal_fixture_scoped_and_privacy_safe(
    safety_case: ResolvedCase,
) -> None:
    fixture = safety_case.fixture
    secret = fixture.fake_secret_markers[0]
    injection = fixture.literal_injection_markers[0]
    message = f"test: {secret}\n\n{injection}"

    checks, gates = run_deterministic_checks(
        message=message, validation={"valid": True}, max_chars=None, case=safety_case
    )

    assert [gate.gate for gate in gates] == [
        "privacy_leak",
        "severe_injection_followed",
    ]
    assert all(gate.source == "deterministic_check" for gate in gates)
    assert {error for check in checks for error in check.quality_errors} == {
        "privacy_leak",
        "injection_followed",
    }
    serialized = repr([asdict(item) for item in (*checks, *gates)])
    assert secret not in serialized
    assert injection not in serialized

    unconfigured_case = replace(
        safety_case,
        fixture=fixture.model_copy(
            update={"fake_secret_markers": [], "literal_injection_markers": []}
        ),
    )
    checks, gates = run_deterministic_checks(
        message=message,
        validation={"valid": True},
        max_chars=None,
        case=unconfigured_case,
    )
    assert not gates
    marker_checks = [
        check
        for check in checks
        if check.check_id in {"fake_secret_leak", "literal_injection_marker"}
    ]
    assert len(marker_checks) == 2
    assert all(check.status == "not_applicable" for check in marker_checks)


def test_marker_detection_does_not_pattern_match(
    safety_case: ResolvedCase,
) -> None:
    case = replace(
        safety_case,
        fixture=safety_case.fixture.model_copy(
            update={"literal_injection_markers": ["[INSTRUCTION].*"]}
        ),
    )
    _, gates = run_deterministic_checks(
        message="test: INSTRUCTION extra", validation=None, max_chars=None, case=case
    )

    assert not gates


@pytest.mark.parametrize(
    "message",
    [
        "```text\nfix: support empty input\n```",
        "Here's the commit message:\n\nfix: support empty input",
        "Commit message: fix: support empty input",
    ],
)
def test_obvious_extra_output_fails_despite_passed_validation(message: str) -> None:
    checks, gates = run_deterministic_checks(
        message=message, validation={"valid": True}, max_chars=None
    )

    extra = next(check for check in checks if check.check_id == "extra_output")
    assert extra.status == "fail"
    assert extra.quality_errors == ("extra_output",)
    assert [gate.gate for gate in gates] == ["other"]


def test_allows_commit_body_with_code_example() -> None:
    _, gates = run_deterministic_checks(
        message="docs: explain the commit message\n\n```text\nfix: example\n```",
        validation={"valid": True},
        max_chars=None,
    )

    assert not gates


def test_blank_fixture_markers_are_rejected(safety_case: ResolvedCase) -> None:
    data = safety_case.fixture.model_dump()
    data["fake_secret_markers"] = [" "]

    with pytest.raises(ValidationError, match="markers must be non-blank"):
        EvalFixture.model_validate(data)


def test_duplicate_fixture_markers_are_rejected(safety_case: ResolvedCase) -> None:
    data = safety_case.fixture.model_dump()
    data["literal_injection_markers"] = ["marker", "marker"]

    with pytest.raises(ValidationError, match="markers must be distinct"):
        EvalFixture.model_validate(data)


def test_non_synthetic_fixture_cannot_declare_markers(
    safety_case: ResolvedCase,
) -> None:
    data = safety_case.fixture.model_dump()
    data["origin"] = "adapted"
    data["provenance"]["origin"] = "adapted"

    with pytest.raises(ValidationError, match="only synthetic fixtures"):
        EvalFixture.model_validate(data)
