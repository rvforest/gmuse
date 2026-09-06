"""Checked-in smoke suite validation contract."""

import time

from tools.evals.gmuse_evals.validate import validate_suite


def test_checked_in_smoke_suite_is_offline_and_complete() -> None:
    started = time.monotonic()

    result = validate_suite("evals", "smoke")

    assert time.monotonic() - started < 30
    assert result.report.status == "passed"
    assert len(result.resolved_cases) == 2
    assert result.report.errors == []
    assert [group.name for group in result.report.composition.groups] == [
        "Changes",
        "Output formats",
        "Context variations",
        "Safety scenarios",
        "Fixture sources",
    ]
    formats = result.report.composition.group("Output formats")
    assert formats is not None
    assert [(entry.label, entry.case_count) for entry in formats.entries] == [
        ("Freeform", 2),
        ("Conventional", 2),
        ("Gitmoji", 1),
    ]
    assert [goal.status for goal in result.report.composition_goals] == [
        "met",
        "met",
        "met",
        "met",
    ]
