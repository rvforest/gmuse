"""Tests for the framework-neutral resolved-case adapter."""

from tests.eval_helpers import make_case, make_profile, make_rubric
from tools.evals.gmuse_evals.inspect_adapter import (
    EvalCaseDescriptor,
    resolved_case_to_descriptor,
    to_inspect_sample,
)
from tools.evals.gmuse_evals.models import (
    EvalFixture,
    FixtureFile,
    FixtureProvenance,
)
from tools.evals.gmuse_evals.results import ResolvedCase


def _fixture() -> EvalFixture:
    return EvalFixture(
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
        selection_rationale="adapter test",
    )


def test_descriptor_preserves_canonical_identity_and_review_metadata() -> None:
    fixture = _fixture()
    profile = make_profile()
    rubric = make_rubric(
        "rubric-id", profile_id=profile.id, include_max_chars_gate=True
    )
    rubric.revision = 2
    case = make_case(
        fixture,
        rubric,
        case_id="case-id",
        formats=["conventional"],
        max_chars=72,
        tags=["docs"],
    )
    case.revision = 4

    descriptor = resolved_case_to_descriptor(
        ResolvedCase(
            case=case,
            fixture=fixture,
            rubric=rubric,
            scoring_profile=profile,
        )
    )

    assert isinstance(descriptor, EvalCaseDescriptor)
    assert descriptor.case_id == "case-id"
    assert descriptor.case_revision == 4
    assert descriptor.fixture_revision == 3
    assert descriptor.rubric_revision == 2
    assert descriptor.scoring_profile_id == profile.id
    assert len(descriptor.rubric_digest) == 64
    assert len(descriptor.scoring_profile_digest) == 64
    assert descriptor.scoring_profile_revision == 1
    assert "rubric_version" not in descriptor.to_metadata()
    assert "scoring_profile_version" not in descriptor.to_metadata()


def test_inspect_sample_is_plain_data_without_inspect_dependency() -> None:
    fixture = _fixture()
    profile = make_profile()
    rubric = make_rubric(profile_id=profile.id)
    case = make_case(fixture, rubric, history_depth=None)

    sample = to_inspect_sample(
        ResolvedCase(
            case=case,
            fixture=fixture,
            rubric=rubric,
            scoring_profile=profile,
        )
    )

    assert sample["id"] == "case"
    assert sample["metadata"]["fixture_id"] == "fixture-id"
    assert sample["metadata"]["rubric_id"] == "rubric"
