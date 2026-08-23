"""Structural tests for the maintainer eval foundation models."""

from datetime import datetime, timezone
from typing import Literal

import pytest
from pydantic import ValidationError

import tools.evals.gmuse_evals as eval_api
from tools.evals.gmuse_evals.models import (
    CoverageSummary,
    EvalCase,
    EvalFixture,
    EvalRubric,
    EvalSuite,
    FixtureFile,
    FixtureHistoryCommit,
    FixtureProvenance,
    SCHEMA_VERSION,
    SuiteCoveragePolicy,
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
        "branch_name": None,
        "repository_instructions": None,
        "selection_rationale": "Exercises the docs path.",
    }
    values.update(overrides)
    return EvalFixture.model_validate(values)


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


def test_case_and_suite_models_reject_invalid_structural_values() -> None:
    with pytest.raises(ValidationError):
        EvalCase.model_validate(
            {
                "id": "case",
                "revision": 1,
                "fixture_id": "fixture-one",
                "rubric_id": "rubric-one",
                "formats": ["unsupported"],
                "history_depth": 0,
                "include_branch": False,
                "user_hint": None,
                "max_chars": None,
                "tags": [],
            }
        )

    with pytest.raises(ValidationError):
        EvalSuite(
            id="smoke",
            version="1.0",
            suite_kind="smoke",
            case_ids=["case-one", "case-one"],
            coverage_policy=SuiteCoveragePolicy(),
        )


def test_report_contains_typed_coverage_and_timestamp() -> None:
    report = ValidationReport(
        schema_version="1.0",
        suite_id="smoke",
        suite_version="1.0",
        status="passed",
        coverage=CoverageSummary(),
        validated_at=datetime.now(timezone.utc),
    )

    assert report.errors == []
    assert report.coverage.dimensions


def test_rubric_defaults_are_reviewable_and_explicit() -> None:
    rubric = EvalRubric(
        id="rubric-one",
        version="1.0",
        required_concepts=["documentation"],
        forbidden_concepts=[],
        allowed_conventional_types=["docs"],
        allowed_scopes=[],
        example_good=[],
        example_bad=[],
        quality_notes=None,
        safety_notes=None,
    )

    assert rubric.example_good == []


def test_asset_schema_versions_are_supported_and_defaults_are_preserved() -> None:
    assert (
        EvalRubric(
            id="rubric",
            version="1.0",
            required_concepts=[],
            forbidden_concepts=[],
            allowed_conventional_types=[],
            allowed_scopes=[],
            example_good=[],
            example_bad=[],
        ).schema_version
        == SCHEMA_VERSION
    )
    assert (
        EvalCase(
            id="case",
            revision=1,
            fixture_id="fixture",
            rubric_id="rubric",
            formats=["freeform"],
            include_branch=False,
            tags=[],
        ).schema_version
        == SCHEMA_VERSION
    )
    assert (
        EvalSuite(
            id="suite",
            version="1.0",
            suite_kind="custom",
            case_ids=["case"],
            coverage_policy=SuiteCoveragePolicy(),
        ).schema_version
        == SCHEMA_VERSION
    )


@pytest.mark.parametrize("model_name", ["fixture", "rubric", "case", "suite"])
def test_unknown_asset_schema_versions_are_rejected(model_name: str) -> None:
    constructors = {
        "fixture": lambda: _fixture(schema_version="999.0"),
        "rubric": lambda: EvalRubric(
            schema_version="999.0",
            id="rubric",
            version="1.0",
            required_concepts=[],
            forbidden_concepts=[],
            allowed_conventional_types=[],
            allowed_scopes=[],
            example_good=[],
            example_bad=[],
        ),
        "case": lambda: EvalCase(
            schema_version="999.0",
            id="case",
            revision=1,
            fixture_id="fixture",
            rubric_id="rubric",
            formats=["freeform"],
            include_branch=False,
            tags=[],
        ),
        "suite": lambda: EvalSuite(
            schema_version="999.0",
            id="suite",
            version="1.0",
            suite_kind="custom",
            case_ids=["case"],
            coverage_policy=SuiteCoveragePolicy(),
        ),
    }

    with pytest.raises(ValidationError, match="schema_version"):
        constructors[model_name]()
