"""Structural tests for the canonical evaluator models."""

from datetime import datetime, timezone
from typing import Literal

import pytest
from pydantic import ValidationError

import tools.evals.gmuse_evals as eval_api
from tests.eval_helpers import make_profile, make_rubric
from tools.evals.gmuse_evals.models import (
    CompositionGoal,
    EvalCase,
    EvalFixture,
    EvalSuite,
    FixtureFile,
    FixtureHistoryCommit,
    FixtureProvenance,
    SuiteComposition,
    ValidationReport,
)


def test_exported_eval_apis_include_usage_examples() -> None:
    for name in eval_api.__all__:
        docstring = getattr(getattr(eval_api, name), "__doc__", "") or ""
        assert "Example:" in docstring, name


def _provenance(
    origin: Literal["real", "adapted", "synthetic"] = "synthetic",
) -> FixtureProvenance:
    return FixtureProvenance(origin=origin, synthetic_notes="Generated for tests")


def _fixture(**overrides: object) -> EvalFixture:
    values: dict[str, object] = {
        "schema_version": "1.0",
        "id": "fixture-one",
        "revision": 1,
        "origin": "synthetic",
        "provenance": _provenance(),
        "ecosystem": "python",
        "change_type": "docs",
        "safety_tags": [],
        "injection_tags": [],
        "base_files": [FixtureFile(path="README.md", content="before\n")],
        "patch": "diff --git a/README.md b/README.md\n",
        "expected_staged_diff_sha256": "a" * 64,
        "expected_files_changed": ["README.md"],
        "history": [FixtureHistoryCommit(subject="Add docs")],
        "selection_rationale": "Exercises the docs path.",
    }
    values.update(overrides)
    return EvalFixture.model_validate(values)


def _case_payload(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "schema_version": "1.0",
        "id": "case",
        "revision": 1,
        "fixture_id": "fixture-one",
        "rubric_id": "rubric-one",
        "formats": ["freeform"],
        "history_depth": 0,
        "include_branch": False,
        "tags": [],
    }
    values.update(overrides)
    return values


def test_fixture_model_carries_versioned_structural_data() -> None:
    fixture = _fixture()

    assert fixture.schema_version == "1.0"
    assert fixture.base_files[0].path == "README.md"
    assert fixture.history[0].subject == "Add docs"


@pytest.mark.parametrize("path", ["/tmp/file", "../file", "a/../../file", ""])
def test_fixture_file_rejects_paths_outside_repository(path: str) -> None:
    with pytest.raises(ValidationError):
        FixtureFile(path=path, content="data")


def test_fixture_revision_and_digest_are_structurally_constrained() -> None:
    with pytest.raises(ValidationError):
        _fixture(revision=0)
    with pytest.raises(ValidationError):
        _fixture(expected_staged_diff_sha256="not-a-sha")


def test_case_and_suite_reject_invalid_or_duplicate_membership() -> None:
    with pytest.raises(ValidationError):
        EvalCase.model_validate(_case_payload(formats=["unsupported"]))
    with pytest.raises(ValidationError, match="formats must be unique"):
        EvalCase.model_validate(_case_payload(formats=["freeform", "freeform"]))
    with pytest.raises(ValidationError, match="case IDs must be unique"):
        EvalSuite(
            schema_version="1.0",
            id="smoke",
            revision=1,
            suite_kind="smoke",
            case_ids=["case-one", "case-one"],
        )


def test_report_contains_composition_and_timestamp() -> None:
    report = ValidationReport(
        schema_version="1.0",
        suite_id="smoke",
        suite_revision=1,
        status="passed",
        composition=SuiteComposition(),
        validated_at=datetime.now(timezone.utc),
    )

    assert report.errors == []
    assert report.composition.groups == []


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (EvalFixture, {}),
        (type(make_profile()), make_profile().model_dump(exclude={"schema_version"})),
        (type(make_rubric()), make_rubric().model_dump(exclude={"schema_version"})),
        (EvalCase, _case_payload(schema_version=None)),
        (
            EvalSuite,
            {
                "id": "suite",
                "revision": 1,
                "suite_kind": "custom",
                "case_ids": ["case"],
            },
        ),
    ],
)
def test_asset_schema_versions_are_required(model: type, payload: dict) -> None:
    if model is EvalFixture:
        payload = _fixture().model_dump(exclude={"schema_version"})
    elif model is EvalCase:
        payload = _case_payload()
        payload.pop("schema_version")
    with pytest.raises(ValidationError, match="schema_version"):
        model.model_validate(payload)


@pytest.mark.parametrize("version", ["", "0.9", "999.0"])
def test_unknown_asset_schema_versions_are_rejected(version: str) -> None:
    with pytest.raises(ValidationError, match="schema_version"):
        _fixture(schema_version=version)


def test_profile_has_four_anchors_and_intermediate_usability_examples() -> None:
    profile = make_profile()

    assert set(profile.dimensions[0].anchors) == {1, 2, 3, 4}
    assert {example.usability for example in profile.usability_examples} == {
        "minor_edit",
        "major_edit",
    }


def test_rubric_requires_explicit_final_schema_fields() -> None:
    with pytest.raises(ValidationError):
        make_rubric().model_validate({"id": "rubric", "revision": 1})


def test_rubric_item_ids_are_globally_unique() -> None:
    rubric = make_rubric()
    rubric.deterministic_gates[0].id = rubric.criteria[0].id

    with pytest.raises(ValidationError, match="globally unique"):
        rubric.model_validate(rubric.model_dump())


def test_composition_goal_rejects_unknown_finite_values() -> None:
    with pytest.raises(ValidationError, match="unsupported value"):
        CompositionGoal(
            selector="case.format",
            value="shell",
            minimum_cases=1,
            severity="required",
        )
