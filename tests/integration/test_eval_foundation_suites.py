"""Checked-in smoke/core suite policy integration coverage."""

from tools.evals.gmuse_evals.validate import validate_suite


def test_checked_in_smoke_is_a_core_subset_with_complete_references() -> None:
    smoke = validate_suite("evals", "smoke")
    core = validate_suite("evals", "core")

    assert smoke.report.status == "passed"
    assert core.report.status == "passed"
    assert smoke.suite is not None
    assert core.suite is not None
    assert set(smoke.suite.case_ids) <= set(core.suite.case_ids)
    assert {item.fixture.id for item in smoke.resolved_cases} == {
        "synthetic-docs-history",
        "synthetic-injection-comment",
    }


def test_checked_in_core_suite_has_stable_composition_and_strict_goals() -> None:
    result = validate_suite("evals", "core", strict_composition=True)

    assert result.report.status == "passed"
    assert result.report.warnings == []
    formats = result.report.composition.group("Output formats")
    assert formats is not None
    assert [entry.label for entry in formats.entries] == [
        "Freeform",
        "Conventional",
        "Gitmoji",
    ]
