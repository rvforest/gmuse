"""Compatibility tests for the framework-neutral validated-case adapter."""

from tools.evals.gmuse_evals.inspect_adapter import (
    ValidatedCaseDescriptor,
    to_inspect_sample,
    validated_case_to_descriptor,
)
from tools.evals.gmuse_evals.models import (
    EvalCase,
    EvalFixture,
    EvalRubric,
    FixtureFile,
    FixtureProvenance,
)
from tools.evals.gmuse_evals.validate import ValidatedCase


def test_descriptor_preserves_stable_identity_and_review_metadata() -> None:
    fixture = EvalFixture(
        schema_version="1.0",
        id="fixture-id",
        revision=3,
        origin="synthetic",
        provenance=FixtureProvenance(origin="synthetic", synthetic_notes="test"),
        ecosystem="python",
        change_type="docs",
        safety_tags=[],
        injection_tags=[],
        base_files=[FixtureFile(path="README.md", content="before\n")],
        patch="",
        expected_staged_diff_sha256="a" * 64,
        expected_files_changed=[],
        history=[],
        branch_name=None,
        repository_instructions=None,
        selection_rationale="adapter test",
    )
    rubric = EvalRubric(
        id="rubric-id",
        version="2.1",
        required_concepts=["docs"],
        forbidden_concepts=[],
        allowed_conventional_types=["docs"],
        allowed_scopes=["guide"],
        example_good=["docs: update guide"],
        example_bad=[],
    )
    case = EvalCase(
        id="case-id",
        revision=4,
        fixture_id=fixture.id,
        rubric_id=rubric.id,
        formats=["conventional"],
        history_depth=0,
        include_branch=False,
        user_hint=None,
        max_chars=72,
        tags=["docs"],
    )

    descriptor = validated_case_to_descriptor(ValidatedCase(case, fixture, rubric))

    assert isinstance(descriptor, ValidatedCaseDescriptor)
    assert descriptor.case_id == "case-id"
    assert descriptor.case_revision == 4
    assert descriptor.fixture_revision == 3
    assert descriptor.expected_staged_diff_sha256 == "a" * 64
    assert descriptor.rubric_version == "2.1"


def test_inspect_sample_is_plain_data_without_inspect_dependency() -> None:
    fixture = EvalFixture(
        schema_version="1.0",
        id="fixture",
        revision=1,
        origin="synthetic",
        provenance=FixtureProvenance(origin="synthetic", synthetic_notes="test"),
        ecosystem="python",
        change_type="docs",
        safety_tags=[],
        injection_tags=[],
        base_files=[],
        patch="",
        expected_staged_diff_sha256="b" * 64,
        expected_files_changed=[],
        history=[],
        branch_name=None,
        repository_instructions=None,
        selection_rationale="adapter test",
    )
    rubric = EvalRubric(
        id="rubric",
        version="1.0",
        required_concepts=[],
        forbidden_concepts=[],
        allowed_conventional_types=[],
        allowed_scopes=[],
        example_good=[],
        example_bad=[],
    )
    case = EvalCase(
        id="case",
        revision=1,
        fixture_id=fixture.id,
        rubric_id=rubric.id,
        formats=["freeform"],
        history_depth=None,
        include_branch=False,
        user_hint=None,
        max_chars=None,
        tags=[],
    )

    sample = to_inspect_sample(ValidatedCase(case, fixture, rubric))

    assert sample["id"] == "case"
    assert sample["metadata"]["fixture_id"] == "fixture"
    assert sample["metadata"]["rubric_id"] == "rubric"
