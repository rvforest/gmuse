"""Origin-aware provenance validation tests."""

from datetime import datetime, timezone

import pytest

from tools.evals.gmuse_evals.load import EvalAssets
from tools.evals.gmuse_evals.models import (
    EvalCase,
    EvalFixture,
    EvalRubric,
    EvalSuite,
    FixtureFile,
    FixtureProvenance,
    SuiteCoveragePolicy,
)
from tools.evals.gmuse_evals.validate import validate_assets


def _assets(provenance: FixtureProvenance) -> EvalAssets:
    fixture = EvalFixture(
        schema_version="1.0",
        id="provenance-fixture",
        revision=1,
        origin=provenance.origin,
        provenance=provenance,
        ecosystem="python",
        change_type="docs",
        safety_tags=[],
        injection_tags=[],
        base_files=[FixtureFile(path="README.md", content="before\n")],
        patch="",
        expected_staged_diff_sha256="0" * 64,
        expected_files_changed=[],
        history=[],
        branch_name=None,
        repository_instructions=None,
        selection_rationale="Checks origin-specific provenance.",
    )
    rubric = EvalRubric(
        id="provenance-rubric",
        version="1.0",
        required_concepts=[],
        forbidden_concepts=[],
        allowed_conventional_types=["docs"],
        allowed_scopes=[],
        example_good=[],
        example_bad=[],
    )
    case = EvalCase(
        id="provenance-case",
        revision=1,
        fixture_id=fixture.id,
        rubric_id=rubric.id,
        formats=["freeform"],
        history_depth=0,
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
        coverage_policy=SuiteCoveragePolicy(),
    )
    return EvalAssets(
        {fixture.id: fixture},
        {rubric.id: rubric},
        {case.id: case},
        {suite.id: suite},
    )


def _real_provenance(**overrides: object) -> FixtureProvenance:
    values: dict[str, object] = {
        "origin": "real",
        "source_repository_url": "https://github.com/example/project",
        "source_owner_repo": "example/project",
        "source_commit_sha": "a" * 40,
        "source_commit_url": "https://github.com/example/project/commit/" + "a" * 40,
        "source_license_expression": "MIT",
        "redistribution_review": "metadata_only",
        "original_commit_message": "docs: update guide",
        "imported_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return FixtureProvenance.model_validate(values)


@pytest.mark.parametrize(
    ("provenance", "expected_status"),
    [
        (FixtureProvenance(origin="synthetic", synthetic_notes="fictional"), "passed"),
        (_real_provenance(), "passed"),
        (
            _real_provenance(
                origin="adapted", adaptation_notes="Rephrased source paths."
            ),
            "passed",
        ),
        (
            FixtureProvenance(
                origin="adapted", synthetic_notes="not enough provenance"
            ),
            "failed",
        ),
    ],
)
def test_provenance_origins_have_explicit_requirements(
    provenance: FixtureProvenance, expected_status: str
) -> None:
    if provenance.origin == "adapted" and provenance.source_repository_url is None:
        provenance = _real_provenance(origin="adapted")
    result = validate_assets(_assets(provenance), "custom", reconstruct=False)

    assert result.report.status == expected_status


@pytest.mark.parametrize(
    "source_license_url",
    ["", "   ", "ftp://example.com/LICENSE", "../LICENSE", "/LICENSE"],
)
def test_real_fixture_rejects_invalid_license_references(
    source_license_url: str,
) -> None:
    provenance = _real_provenance(
        source_license_expression=None,
        source_license_url=source_license_url,
    )

    result = validate_assets(_assets(provenance), "custom", reconstruct=False)

    assert any(
        issue.code == "invalid_license_reference" for issue in result.report.errors
    )


@pytest.mark.parametrize(
    "source_license_url",
    ["LICENSE", "docs/licenses/source.txt", "https://example.com/LICENSE"],
)
def test_real_fixture_accepts_url_or_safe_repository_license_path(
    source_license_url: str,
) -> None:
    provenance = _real_provenance(
        source_license_expression=None,
        source_license_url=source_license_url,
    )

    result = validate_assets(_assets(provenance), "custom", reconstruct=False)

    assert result.report.status == "passed"


def test_real_provenance_reports_all_missing_attribution_fields() -> None:
    result = validate_assets(
        _assets(FixtureProvenance(origin="real")), "custom", reconstruct=False
    )
    messages = "\n".join(issue.message for issue in result.report.errors)

    assert "source_repository_url" in messages
    assert "source_license_expression" in messages
    assert "redistribution_review" in messages
    assert "original_commit_message" in messages


def test_real_provenance_rejects_short_sha_and_invalid_spdx() -> None:
    provenance = _real_provenance(
        source_commit_sha="abc123",
        source_license_expression="DefinitelyNotAn SPDX Expression",
    )

    result = validate_assets(_assets(provenance), "custom", reconstruct=False)
    codes = {issue.code for issue in result.report.errors}

    assert {"short_commit_sha", "invalid_license_expression"} <= codes


@pytest.mark.parametrize(
    "expression",
    [
        "0BSD",
        "Python-2.0",
        "GPL-2.0-only WITH Classpath-exception-2.0",
        "LicenseRef-Test",
    ],
)
def test_complete_spdx_catalog_and_license_refs_are_accepted(expression: str) -> None:
    result = validate_assets(
        _assets(_real_provenance(source_license_expression=expression)),
        "custom",
        reconstruct=False,
    )

    assert not any(
        issue.code == "invalid_license_expression" for issue in result.report.errors
    )


@pytest.mark.parametrize("field", ["source_repository_url", "source_commit_url"])
@pytest.mark.parametrize(
    "value", ["github.com/example/project", "ftp://example.com/project"]
)
def test_repository_and_commit_urls_must_be_absolute_http_urls(
    field: str, value: str
) -> None:
    result = validate_assets(
        _assets(_real_provenance(**{field: value})),
        "custom",
        reconstruct=False,
    )

    assert any(
        issue.code == "invalid_source_url" and field in issue.message
        for issue in result.report.errors
    )
