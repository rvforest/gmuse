"""Rubric semantics and safety metadata tests."""

import pytest

from tests.eval_helpers import make_assets, make_case, make_profile, make_rubric
from tools.evals.gmuse_evals.load import load_assets
from tools.evals.gmuse_evals.models import (
    INJECTION_LOCATION_TAGS,
    INJECTION_PATTERN_TAGS,
    EvalFixture,
    FixtureFile,
    FixtureProvenance,
)
from tools.evals.gmuse_evals.validate import validate_assets


def assets(
    *,
    safety_tags: list[str] | None = None,
    injection_tags: list[str] | None = None,
    synthetic_notes: str = "fictional test data",
    safety_notes: str | None = None,
    patch: str = "",
):
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
        selection_rationale="Exercises rubric semantics.",
    )
    profile = make_profile()
    rubric = make_rubric(profile_id=profile.id, safety_notes=safety_notes)
    case = make_case(
        fixture,
        rubric,
        formats=["conventional"],
        tags=["safety"] if safety_tags else [],
    )
    return make_assets(fixture, profile=profile, rubric=rubric, case=case)


def test_injection_requires_complete_tags_and_safety_notes() -> None:
    result = validate_assets(
        assets(safety_tags=["injection"], safety_notes=None),
        "custom",
        reconstruct=False,
    )

    assert {"missing_injection_tags", "missing_safety_notes"} <= {
        issue.code for issue in result.report.errors
    }


def test_injection_subtags_require_explicit_injection_safety_tag() -> None:
    result = validate_assets(
        assets(injection_tags=["direct-instruction", "code-comment"]),
        "custom",
        reconstruct=False,
    )

    assert "orphan_injection_tags" in {issue.code for issue in result.report.errors}


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


def test_failed_deterministic_gate_requires_unusable_example() -> None:
    loaded = load_assets("evals")
    loaded.rubrics["docs-history"].examples[0].expected_gate_ids = ["message-valid"]

    result = validate_assets(loaded, "smoke", reconstruct=False)

    assert "failed_gate_requires_unusable" in {
        issue.code for issue in result.report.errors
    }


def test_failure_example_must_reference_a_major_failure() -> None:
    loaded = load_assets("evals")
    rubric = loaded.rubrics["docs-history"]
    rubric.failure_conditions[0].severity = "minor"

    result = validate_assets(loaded, "smoke", reconstruct=False)

    assert "missing_failure_example" in {issue.code for issue in result.report.errors}


def test_max_chars_gate_must_match_case_configuration() -> None:
    fixture = assets().fixtures["rubric-fixture"]
    profile = make_profile()
    rubric = make_rubric(profile_id=profile.id, include_max_chars_gate=True)
    case = make_case(fixture, rubric, max_chars=None)

    result = validate_assets(
        make_assets(fixture, profile=profile, rubric=rubric, case=case),
        "custom",
        reconstruct=False,
    )

    assert "inapplicable_max_chars_gate" in {
        issue.code for issue in result.report.errors
    }
