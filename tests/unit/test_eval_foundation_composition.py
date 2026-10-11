"""Composition collection and goal-validation tests."""

from tests.eval_helpers import make_assets, make_case, make_rubric, make_suite
from tools.evals.gmuse_evals.models import (
    CompositionGoal,
    EvalFixture,
    FixtureFile,
    FixtureHistoryCommit,
    FixtureProvenance,
)
from tools.evals.gmuse_evals.validate import validate_assets


def _fixture(history: list[FixtureHistoryCommit] | None = None) -> EvalFixture:
    return EvalFixture(
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
        selection_rationale="composition test",
    )


def _assets(
    *,
    history_depth: int | None = 0,
    history: list[FixtureHistoryCommit] | None = None,
    goals: list[CompositionGoal] | None = None,
):
    fixture = _fixture(history)
    rubric = make_rubric()
    case = make_case(fixture, rubric, history_depth=history_depth)
    suite = make_suite(case)
    suite.composition_goals = goals or []
    return make_assets(fixture, rubric=rubric, case=case, suite=suite)


def _context_entries(result) -> dict[str, int]:
    group = result.report.composition.group("Context variations")
    assert group is not None
    return {entry.label: entry.case_count for entry in group.entries}


def test_composition_uses_stable_human_readable_groups() -> None:
    result = validate_assets(_assets(), "custom", reconstruct=False)

    assert [group.name for group in result.report.composition.groups] == [
        "Changes",
        "Output formats",
        "Context variations",
        "Safety scenarios",
        "Fixture sources",
    ]
    assert _context_entries(result)["Commit history disabled"] == 1


def test_history_composition_distinguishes_zero_positive_and_default_depth() -> None:
    history = [FixtureHistoryCommit(subject=f"docs: {index}") for index in range(5)]

    disabled = validate_assets(
        _assets(history_depth=0, history=history), "custom", reconstruct=False
    )
    enabled = validate_assets(
        _assets(history_depth=1, history=history), "custom", reconstruct=False
    )
    defaulted = validate_assets(
        _assets(history_depth=None, history=history), "custom", reconstruct=False
    )

    assert _context_entries(disabled)["Commit history disabled"] == 1
    assert _context_entries(enabled)["Commit history enabled"] == 1
    assert _context_entries(defaulted)["Commit history enabled"] == 1


def test_history_depth_larger_than_fixture_history_skips_reconstruction(
    monkeypatch,
) -> None:
    import tools.evals.gmuse_evals.validate as validation

    def fail_reconstruction(_fixture):
        raise AssertionError("reconstruction should not run")

    monkeypatch.setattr(validation, "validate_reconstruction", fail_reconstruction)
    result = validate_assets(_assets(history_depth=1), "custom")

    assert result.report.status == "failed"
    assert "history_depth_exceeds_fixture" in {
        issue.code for issue in result.report.errors
    }


def test_advisory_goal_warns_and_strict_composition_promotes_it() -> None:
    goals = [
        CompositionGoal(
            selector="case.format",
            value="gitmoji",
            minimum_cases=1,
            severity="advisory",
        )
    ]

    advisory = validate_assets(_assets(goals=goals), "custom", reconstruct=False)
    strict = validate_assets(
        _assets(goals=goals),
        "custom",
        strict_composition=True,
        reconstruct=False,
    )

    assert advisory.report.status == "passed"
    assert advisory.report.composition_goals[0].observed_cases == 0
    assert advisory.report.warnings[0].code == "composition_goal_shortfall"
    assert strict.report.status == "failed"


def test_required_goal_shortfall_fails_validation() -> None:
    goals = [
        CompositionGoal(
            selector="case.format",
            value="gitmoji",
            minimum_cases=1,
            severity="required",
        )
    ]

    result = validate_assets(_assets(goals=goals), "custom", reconstruct=False)

    assert result.report.status == "failed"
    assert result.report.errors[0].code == "composition_goal_shortfall"


def test_unresolved_cases_do_not_create_composition_entries() -> None:
    assets = _assets()
    assets.fixtures.clear()

    result = validate_assets(assets, "custom", reconstruct=False)

    assert result.report.composition.groups == []
