"""Coverage policy and deterministic summary tests."""

from tools.evals.gmuse_evals.load import EvalAssets
from tools.evals.gmuse_evals.models import (
    COVERAGE_DIMENSIONS,
    EvalCase,
    EvalFixture,
    EvalRubric,
    EvalSuite,
    FixtureFile,
    FixtureHistoryCommit,
    FixtureProvenance,
    SuiteCoveragePolicy,
)
from tools.evals.gmuse_evals.validate import validate_assets


def _assets(
    policy: SuiteCoveragePolicy,
    *,
    history_depth: int | None = 0,
    history: list[FixtureHistoryCommit] | None = None,
) -> EvalAssets:
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
        history=history or [],
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
        history_depth=history_depth,
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
    result = validate_assets(
        _assets(SuiteCoveragePolicy()), "custom", reconstruct=False
    )

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


def test_empty_advisory_dimension_reports_one_warning() -> None:
    assets = _assets(SuiteCoveragePolicy(advisory_dimensions=["format"]))
    assets.cases.clear()

    result = validate_assets(assets, "custom", reconstruct=False)

    assert [issue.code for issue in result.report.warnings] == ["coverage_gap"]


def test_history_coverage_distinguishes_zero_positive_and_default_depth() -> None:
    history = [FixtureHistoryCommit(subject=f"docs: {index}") for index in range(5)]

    not_used = validate_assets(
        _assets(SuiteCoveragePolicy(), history_depth=0, history=history),
        "custom",
        reconstruct=False,
    )
    used = validate_assets(
        _assets(SuiteCoveragePolicy(), history_depth=1, history=history),
        "custom",
        reconstruct=False,
    )
    defaulted = validate_assets(
        _assets(SuiteCoveragePolicy(), history_depth=None, history=history),
        "custom",
        reconstruct=False,
    )

    assert not_used.report.coverage.dimensions["history"] == ["not-used"]
    assert used.report.coverage.dimensions["history"] == ["used"]
    assert defaulted.report.coverage.dimensions["history"] == ["used"]


def test_history_depth_larger_than_fixture_history_fails_before_reconstruction(
    monkeypatch,
) -> None:
    import tools.evals.gmuse_evals.validate as validation

    def fail_reconstruction(_fixture):
        raise AssertionError("reconstruction should not run")

    monkeypatch.setattr(validation, "reconstruct_fixture", fail_reconstruction)
    result = validate_assets(_assets(SuiteCoveragePolicy(), history_depth=1), "custom")

    assert result.report.status == "failed"
    assert any(
        issue.code == "history_depth_exceeds_fixture" for issue in result.report.errors
    )
