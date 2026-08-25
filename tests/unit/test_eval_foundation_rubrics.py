"""Rubric semantics and safety metadata tests."""

import pytest

from tools.evals.gmuse_evals.load import EvalAssets
from tools.evals.gmuse_evals.models import (
    INJECTION_LOCATION_TAGS,
    INJECTION_PATTERN_TAGS,
    EvalCase,
    EvalFixture,
    EvalRubric,
    EvalSuite,
    FixtureFile,
    FixtureProvenance,
    SuiteCoveragePolicy,
)
from tools.evals.gmuse_evals.validate import validate_assets


def assets(
    *,
    safety_tags: list[str] | None = None,
    injection_tags: list[str] | None = None,
    synthetic_notes: str = "fictional test data",
    safety_notes: str | None = None,
    allowed_types: list[str] | None = None,
    patch: str = "",
) -> EvalAssets:
    fixture = EvalFixture(
        schema_version="1.0",
        id="rubric-fixture",
        revision=1,
        origin="synthetic",
        provenance=FixtureProvenance(
            origin="synthetic", synthetic_notes=synthetic_notes
        ),
        ecosystem="python",
        change_type="test",
        safety_tags=safety_tags or [],
        injection_tags=injection_tags or [],
        base_files=[FixtureFile(path="fixture.py", content="VALUE = 'safe'\n")],
        patch=patch,
        expected_staged_diff_sha256="0" * 64,
        expected_files_changed=[],
        history=[],
        branch_name=None,
        repository_instructions=None,
        selection_rationale="Exercises rubric semantics.",
    )
    rubric = EvalRubric(
        id="rubric",
        version="1.0",
        required_concepts=["test"],
        forbidden_concepts=[],
        allowed_conventional_types=allowed_types or ["test"],
        allowed_scopes=["safety"],
        example_good=["test(safety): cover fixture"],
        example_bad=["feat: expose secret"],
        safety_notes=safety_notes,
    )
    case = EvalCase(
        id="case",
        revision=1,
        fixture_id=fixture.id,
        rubric_id=rubric.id,
        formats=["conventional"],
        history_depth=0,
        include_branch=False,
        user_hint=None,
        max_chars=None,
        tags=["safety"] if safety_tags else [],
    )
    suite = EvalSuite(
        id="custom",
        version="1.0",
        suite_kind="custom",
        case_ids=[case.id],
        coverage_policy=SuiteCoveragePolicy(),
    )
    return EvalAssets(
        {fixture.id: fixture}, {rubric.id: rubric}, {case.id: case}, {suite.id: suite}
    )


def test_gmuse_conventional_types_and_scopes_are_accepted() -> None:
    result = validate_assets(
        assets(allowed_types=["fix", "test"]), "custom", reconstruct=False
    )

    assert result.report.status == "passed"


def test_unsupported_conventional_type_is_reported() -> None:
    result = validate_assets(
        assets(allowed_types=["build"]), "custom", reconstruct=False
    )

    assert "unsupported_conventional_type" in {
        issue.code for issue in result.report.errors
    }


def test_injection_requires_complete_tags_and_safety_notes() -> None:
    result = validate_assets(
        assets(safety_tags=["injection"], safety_notes=None),
        "custom",
        reconstruct=False,
    )
    codes = {issue.code for issue in result.report.errors}

    assert {"missing_injection_tags", "missing_safety_notes"} <= codes


def test_injection_subtags_require_explicit_injection_safety_tag() -> None:
    result = validate_assets(
        assets(injection_tags=["direct-instruction", "code-comment"]),
        "custom",
        reconstruct=False,
    )

    assert any(issue.code == "orphan_injection_tags" for issue in result.report.errors)


def test_injection_location_and_fake_secret_markers_are_validated() -> None:
    result = validate_assets(
        assets(
            safety_tags=["injection", "safety"],
            injection_tags=["direct-instruction", "code-comment"],
            safety_notes="The value is fake nonfunctional test data in a comment.",
            patch="""diff --git a/fixture.py b/fixture.py
--- a/fixture.py
+++ b/fixture.py
@@ -1 +1,2 @@
 VALUE = 'safe'
+# password = "fake-value"  # pragma: allowlist secret
""",
        ),
        "custom",
        reconstruct=False,
    )

    assert result.report.status == "passed"


def test_pattern_only_and_location_only_injection_tags_fail() -> None:
    pattern_only = validate_assets(
        assets(
            safety_tags=["injection"],
            injection_tags=["direct-instruction"],
            safety_notes="Inert test data.",
        ),
        "custom",
        reconstruct=False,
    )
    location_only = validate_assets(
        assets(
            safety_tags=["injection"],
            injection_tags=["code-comment"],
            safety_notes="Inert test data.",
        ),
        "custom",
        reconstruct=False,
    )

    assert "missing_injection_location" in {
        issue.code for issue in pattern_only.report.errors
    }
    assert "missing_injection_pattern" in {
        issue.code for issue in location_only.report.errors
    }


@pytest.mark.parametrize("pattern", sorted(INJECTION_PATTERN_TAGS))
@pytest.mark.parametrize("location", sorted(INJECTION_LOCATION_TAGS))
def test_supported_injection_patterns_require_supported_locations(
    pattern: str, location: str
) -> None:
    result = validate_assets(
        assets(
            safety_tags=["injection"],
            injection_tags=[pattern, location],
            safety_notes="Inert test data.",
        ),
        "custom",
        reconstruct=False,
    )

    assert result.report.status == "passed"
