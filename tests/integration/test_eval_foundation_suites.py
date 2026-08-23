"""Checked-in smoke/core suite policy integration coverage."""

from tools.evals.gmuse_evals.validate import validate_suite


def test_checked_in_smoke_is_a_core_subset_with_complete_references() -> None:
    smoke = validate_suite("evals", "smoke")
    core = validate_suite("evals", "core")

    assert smoke.report.status == "passed"
    assert core.report.status == "passed"
    assert set(smoke.suite.case_ids) <= set(core.suite.case_ids)
    assert {item.fixture.id for item in smoke.cases} == {
        "synthetic-docs-history",
        "synthetic-injection-comment",
    }


def test_checked_in_core_suite_has_stable_coverage_and_strict_balance() -> None:
    result = validate_suite("evals", "core", strict_balance=True)

    assert result.report.status == "passed"
    assert result.report.warnings == []
    assert result.report.coverage.dimensions["format"] == [
        "conventional",
        "freeform",
        "gitmoji",
    ]
