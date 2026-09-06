"""Unit tests for structured fixture and suite validation."""

from tests.eval_helpers import make_case, make_rubric, make_suite
from tools.evals.gmuse_evals.load import EvalAssets
from tools.evals.gmuse_evals.models import (
    EvalFixture,
    FixtureFile,
    FixtureProvenance,
)
from tools.evals.gmuse_evals.validate import validate_assets


def make_assets(
    *, digest: str = "0" * 64, paths: list[str] | None = None
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
        patch="""diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 before
+after
""",
        expected_staged_diff_sha256=digest,
        expected_files_changed=paths or ["README.md"],
        history=[],
        branch_name=None,
        repository_instructions=None,
        selection_rationale="test",
    )
    rubric = make_rubric(include_max_chars_gate=True)
    case = make_case(
        fixture,
        rubric,
        formats=["freeform", "conventional"],
        history_depth=0,
        max_chars=72,
        tags=["docs"],
    )
    suite = make_suite(case)
    from tests.eval_helpers import make_profile

    profile = make_profile()
    return EvalAssets(
        fixtures={"fixture": fixture},
        rubrics={"rubric": rubric},
        cases={"case": case},
        suites={"custom": suite},
        scoring_profiles={profile.id: profile},
    )


def test_successful_validation_reports_expected_digest_and_composition() -> None:
    initial = make_assets()
    from tools.evals.gmuse_evals.git_reconstruct import reconstruct_fixture

    with reconstruct_fixture(initial.fixtures["fixture"]) as repository:
        valid = initial.fixtures["fixture"].model_copy(
            update={"expected_staged_diff_sha256": repository.staged_diff.hash}
        )
    assets = EvalAssets(
        fixtures={"fixture": valid},
        rubrics=initial.rubrics,
        cases=initial.cases,
        suites=initial.suites,
        scoring_profiles=initial.scoring_profiles,
    )

    result = validate_assets(assets, "custom")

    assert result.report.status == "passed"
    assert result.report.errors == []
    formats = result.report.composition.group("Output formats")
    assert formats is not None
    assert [entry.label for entry in formats.entries] == ["Freeform", "Conventional"]


def test_digest_and_changed_path_mismatches_are_actionable() -> None:
    result = validate_assets(make_assets(paths=["other.md"]), "custom")

    assert result.report.status == "failed"
    messages = "\n".join(issue.render() for issue in result.report.errors)
    assert "expected" in messages or "digest" in messages


def test_missing_references_are_aggregated() -> None:
    assets = make_assets()
    case = assets.cases["case"].model_copy(
        update={"fixture_id": "missing-fixture", "rubric_id": "missing-rubric"}
    )
    result = validate_assets(
        EvalAssets(
            fixtures=assets.fixtures,
            rubrics=assets.rubrics,
            cases={"case": case},
            suites=assets.suites,
            scoring_profiles=assets.scoring_profiles,
        ),
        "custom",
        reconstruct=False,
    )

    assert result.report.status == "failed"
    assert {issue.code for issue in result.report.errors} == {"missing_fixture"}


def test_history_depth_error_skips_reconstruction(monkeypatch) -> None:
    import tools.evals.gmuse_evals.validate as validation

    assets = make_assets()
    assets = EvalAssets(
        fixtures=assets.fixtures,
        rubrics=assets.rubrics,
        cases={"case": assets.cases["case"].model_copy(update={"history_depth": 1})},
        suites=assets.suites,
        scoring_profiles=assets.scoring_profiles,
    )

    def fail_reconstruction(_fixture):
        raise AssertionError("reconstruction should not run")

    monkeypatch.setattr(validation, "validate_reconstruction", fail_reconstruction)
    result = validate_assets(assets, "custom")

    assert any(
        issue.code == "history_depth_exceeds_fixture" for issue in result.report.errors
    )
