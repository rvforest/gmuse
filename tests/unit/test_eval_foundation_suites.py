"""Suite membership, format, and safety discovery tests."""

from typing import Literal

import pytest
from pydantic import ValidationError

from tests.eval_helpers import make_case, make_profile, make_rubric
from tools.evals.gmuse_evals.load import EvalAssets
from tools.evals.gmuse_evals.models import (
    EvalCase,
    EvalFixture,
    EvalSuite,
    FixtureFile,
    FixtureProvenance,
)
from tools.evals.gmuse_evals.validate import validate_assets


def _assets(
    *,
    smoke_cases: list[str] | None = None,
    core_cases: list[str] | None = None,
    suite_kind: Literal["smoke", "core", "safety", "custom"] = "smoke",
) -> EvalAssets:
    fixture = EvalFixture(
        schema_version="1.0",
        id="fixture",
        revision=1,
        origin="synthetic",
        provenance=FixtureProvenance(origin="synthetic", synthetic_notes="test"),
        ecosystem="python",
        change_type="test",
        safety_tags=["safety"] if suite_kind == "safety" else [],
        injection_tags=[],
        base_files=[FixtureFile(path="test.py", content="pass\n")],
        patch="",
        expected_staged_diff_sha256="0" * 64,
        expected_files_changed=[],
        history=[],
        branch_name=None,
        repository_instructions=None,
        selection_rationale="suite test",
    )
    profile = make_profile()
    rubric = make_rubric(
        profile_id=profile.id,
        safety_notes="Safety cases contain only inert test content."
        if suite_kind == "safety"
        else None,
    )
    case = make_case(
        fixture,
        rubric,
        case_id="case-one",
        tags=["safety"] if suite_kind == "safety" else [],
    )
    core = EvalSuite(
        schema_version="1.0",
        id="core",
        revision=1,
        suite_kind="core",
        case_ids=core_cases or ["case-one"],
    )
    selected = EvalSuite(
        schema_version="1.0",
        id="smoke" if suite_kind == "smoke" else "safety",
        revision=1,
        suite_kind=suite_kind,
        case_ids=smoke_cases or ["case-one"],
    )
    return EvalAssets(
        fixtures={fixture.id: fixture},
        rubrics={rubric.id: rubric},
        cases={case.id: case},
        suites={core.id: core, selected.id: selected},
        scoring_profiles={profile.id: profile},
    )


def test_smoke_membership_passes_only_as_core_subset() -> None:
    result = validate_assets(_assets(), "smoke", reconstruct=False)

    assert result.report.status == "passed"


def test_smoke_membership_outside_core_is_actionable() -> None:
    assets = _assets(smoke_cases=["case-one", "outside"], core_cases=["case-one"])
    result = validate_assets(assets, "smoke", reconstruct=False)

    assert "missing_case" in {issue.code for issue in result.report.errors}


def test_missing_case_reference_fails_before_reconstruction() -> None:
    assets = _assets(smoke_cases=["missing"], core_cases=["missing"])
    result = validate_assets(assets, "smoke", reconstruct=False)

    assert result.report.errors[0].code == "missing_case"


def test_duplicate_case_ids_and_unsupported_formats_are_rejected_structurally() -> None:
    with pytest.raises(ValidationError):
        EvalSuite(
            schema_version="1.0",
            id="core",
            revision=1,
            suite_kind="core",
            case_ids=["case-one", "case-one"],
        )
    with pytest.raises(ValidationError):
        EvalCase.model_validate(
            {
                "schema_version": "1.0",
                "id": "case",
                "revision": 1,
                "fixture_id": "fixture",
                "rubric_id": "rubric",
                "formats": ["shell"],
                "history_depth": 0,
                "include_branch": False,
                "user_hint": None,
                "max_chars": None,
                "tags": [],
            }
        )


def test_safety_suite_cases_remain_discoverable_by_intent() -> None:
    result = validate_assets(_assets(suite_kind="safety"), "safety", reconstruct=False)

    assert result.report.status == "passed"
    assert result.resolved_cases[0].case.tags == ["safety"]
