"""Checked-in smoke suite validation contract."""

import time

from tools.evals.gmuse_evals.validate import validate_suite


def test_checked_in_smoke_suite_is_offline_and_complete() -> None:
    started = time.monotonic()

    result = validate_suite("evals", "smoke")

    assert time.monotonic() - started < 30
    assert result.report.status == "passed"
    assert len(result.cases) == 2
    assert result.report.errors == []
    assert set(result.report.coverage.dimensions) >= {
        "ecosystem",
        "source_repo",
        "origin",
        "source_license",
        "change_type",
        "format",
        "safety_tag",
        "injection_tag",
        "history",
        "branch",
        "hint",
        "max_chars",
    }
