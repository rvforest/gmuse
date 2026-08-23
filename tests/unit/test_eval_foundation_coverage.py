"""Coverage policy and deterministic summary tests."""

from tools.evals.gmuse_evals.load import EvalAssets
from tools.evals.gmuse_evals.models import (
    COVERAGE_DIMENSIONS,
    EvalCase,
    EvalFixture,
    EvalRubric,
    EvalSuite,
    FixtureFile,
    FixtureProvenance,
    SuiteCoveragePolicy,
)
from tools.evals.gmuse_evals.validate import validate_assets


def _assets(policy: SuiteCoveragePolicy) -> EvalAssets:
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
        base_files=[FixtureFile(path="README.md", content="before\n")],
        patch="",
        expected_staged_diff_sha256="0" * 64,
        expected_files_changed=[],
        history=[],
        branch_name=None,
        repository_instructions=None,
        selection_rationale="coverage test",
    )
    rubric = EvalRubric(
        id="rubric",
        version="1.0",
        required_concepts=[],
        forbidden_concepts=[],
        allowed_conventional_types=["docs"],
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
        history_depth=0,
        include_branch=False,
        user_hint=None,
        max_chars=None,
        tags=[],
    )
    suite = EvalSuite(
        id="custom",
        version="1.0",
        suite_kind="custom",
        case_ids=[case.id],
        coverage_policy=policy,
    )
    return EvalAssets(
        {fixture.id: fixture}, {rubric.id: rubric}, {case.id: case}, {suite.id: suite}
    )


def test_coverage_contains_every_dimension_in_stable_order() -> None:
    result = validate_assets(_assets(SuiteCoveragePolicy()), "custom", reconstruct=False)

    assert list(result.report.coverage.dimensions) == list(COVERAGE_DIMENSIONS)


def test_advisory_minimums_warn_and_strict_balance_promotes_them() -> None:
    policy = SuiteCoveragePolicy(
        advisory_dimensions=["format"], minimum_case_counts={"format": 2}
    )
    advisory = validate_assets(_assets(policy), "custom", reconstruct=False)
    strict = validate_assets(
        _assets(policy), "custom", strict_balance=True, reconstruct=False
    )

    assert advisory.report.status == "passed"
    assert advisory.report.warnings
    assert strict.report.status == "failed"
    assert strict.report.errors


def test_required_minimums_fail_validation() -> None:
    policy = SuiteCoveragePolicy(
        required_dimensions=["format"], minimum_case_counts={"format": 2}
    )
    result = validate_assets(_assets(policy), "custom", reconstruct=False)

    assert result.report.status == "failed"
    assert any(issue.code == "minimum_coverage" for issue in result.report.errors)
