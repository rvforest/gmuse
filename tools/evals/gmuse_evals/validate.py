"""Structured orchestration for eval asset validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from collections.abc import Sequence

from license_expression import Licensing

from gmuse.prompts import validate_message

from .git_reconstruct import ReconstructionError, reconstruct_fixture
from .load import EvalAssets, load_suite_assets
from .models import (
    COVERAGE_DIMENSIONS,
    SCHEMA_VERSION,
    CoverageSummary,
    EvalCase,
    EvalFixture,
    EvalRubric,
    EvalSuite,
    ValidationIssue,
    ValidationReport,
)

_FULL_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
_INJECTION_TAG_ALIASES = {
    "direct-instruction",
    "indirect-external-content",
    "obfuscated-encoded",
    "deleted-instruction",
    "code-comment",
    "markdown",
    "docs",
    "string-literal",
    "test-fixture",
    "config-example",
    "direct",
    "indirect",
    "obfuscated",
    "encoded",
    "deleted",
}
_KNOWN_LICENSES = (
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "LGPL-2.1-only",
    "LGPL-3.0-only",
    "MIT",
    "MPL-2.0",
    "GPL-2.0-only",
    "GPL-3.0-only",
)


@dataclass(frozen=True)
class ValidatedCase:
    """A resolved case descriptor for downstream in-process consumers."""

    case: EvalCase
    fixture: EvalFixture
    rubric: EvalRubric


@dataclass(frozen=True)
class ValidatedSuite:
    """A suite plus resolved cases and its structured validation report."""

    suite: EvalSuite | None
    cases: tuple[ValidatedCase, ...]
    report: ValidationReport


def _report(
    suite: EvalSuite | None,
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
    coverage: CoverageSummary | None = None,
) -> ValidationReport:
    """Build a consistent report for both successful and failed runs."""
    return ValidationReport(
        schema_version=SCHEMA_VERSION,
        suite_id=suite.id if suite else "unknown",
        suite_version=suite.version if suite else SCHEMA_VERSION,
        status="failed" if errors else "passed",
        errors=errors,
        warnings=warnings,
        coverage=coverage or CoverageSummary(),
        validated_at=datetime.now(timezone.utc),
    )


def _add_coverage(coverage: CoverageSummary, cases: tuple[ValidatedCase, ...]) -> None:
    """Collect deterministic, framework-neutral coverage dimensions."""
    values = {dimension: set() for dimension in COVERAGE_DIMENSIONS}
    for item in cases:
        fixture = item.fixture
        case = item.case
        provenance = fixture.provenance
        values["ecosystem"].add(fixture.ecosystem)
        values["source_repo"].add(provenance.source_owner_repo or "synthetic")
        values["origin"].add(fixture.origin)
        values["source_license"].add(
            "present"
            if provenance.source_license_expression or provenance.source_license_url
            else "not-applicable"
        )
        values["change_type"].add(fixture.change_type)
        values["format"].update(case.formats)
        values["safety_tag"].update(fixture.safety_tags or ["none"])
        values["injection_tag"].update(fixture.injection_tags or ["none"])
        values["history"].add("used" if case.history_depth else "not-used")
        values["branch"].add("used" if case.include_branch else "not-used")
        values["hint"].add("used" if case.user_hint else "not-used")
        values["max_chars"].add("used" if case.max_chars else "not-used")
    coverage.dimensions = {
        dimension: sorted(values[dimension]) for dimension in COVERAGE_DIMENSIONS
    }


def _issue(code: str, message: str, asset_id: str) -> ValidationIssue:
    """Construct a consistently attributed validation issue."""
    return ValidationIssue(code=code, asset_id=asset_id, message=message)


def _validate_provenance(item: ValidatedCase) -> list[ValidationIssue]:
    """Validate origin-specific attribution without claiming legal approval."""
    fixture = item.fixture
    provenance = fixture.provenance
    errors: list[ValidationIssue] = []
    if fixture.origin != provenance.origin:
        errors.append(
            _issue("provenance_origin", "origin does not match provenance", fixture.id)
        )
        return errors
    if fixture.origin == "synthetic":
        if not provenance.synthetic_notes or not provenance.synthetic_notes.strip():
            errors.append(
                _issue(
                    "missing_synthetic_notes",
                    "missing provenance.synthetic_notes",
                    fixture.id,
                )
            )
        source_fields = (
            provenance.source_repository_url,
            provenance.source_owner_repo,
            provenance.source_commit_sha,
            provenance.source_commit_url,
            provenance.original_commit_message,
        )
        if any(source_fields):
            errors.append(
                _issue(
                    "synthetic_source_metadata",
                    "synthetic fixtures must not claim an external source commit",
                    fixture.id,
                )
            )
        return errors

    required = {
        "source_repository_url": provenance.source_repository_url,
        "source_owner_repo": provenance.source_owner_repo,
        "source_commit_sha": provenance.source_commit_sha,
        "source_commit_url": provenance.source_commit_url,
        "original_commit_message": provenance.original_commit_message,
        "imported_at": provenance.imported_at,
        "redistribution_review": provenance.redistribution_review,
    }
    for field, value in required.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(
                _issue("missing_provenance", f"missing provenance.{field}", fixture.id)
            )
    if (
        provenance.source_commit_sha
        and _FULL_SHA.fullmatch(provenance.source_commit_sha) is None
    ):
        errors.append(
            _issue(
                "short_commit_sha",
                "provenance.source_commit_sha must be a full 40-character SHA",
                fixture.id,
            )
        )
    if not (provenance.source_license_expression or provenance.source_license_url):
        errors.append(
            _issue(
                "missing_license_evidence",
                "missing provenance.source_license_expression or provenance.source_license_url",
                fixture.id,
            )
        )
    if provenance.source_license_expression:
        try:
            references = re.findall(
                r"\bLicenseRef-[A-Za-z0-9.-]+\b", provenance.source_license_expression
            )
            licensing = Licensing(symbols=[*_KNOWN_LICENSES, *references])
            validation = licensing.validate(provenance.source_license_expression)
            if validation.errors:
                raise ValueError("; ".join(validation.errors))
        except (Exception,):
            errors.append(
                _issue(
                    "invalid_license_expression",
                    "provenance.source_license_expression is not a valid SPDX expression",
                    fixture.id,
                )
            )
    if fixture.origin == "adapted" and not (
        provenance.adaptation_notes and provenance.adaptation_notes.strip()
    ):
        errors.append(
            _issue(
                "missing_adaptation_notes",
                "missing provenance.adaptation_notes",
                fixture.id,
            )
        )
    return errors


def _validate_safety(item: ValidatedCase) -> list[ValidationIssue]:
    """Validate injection taxonomy and nonfunctional secret-like test data."""
    fixture = item.fixture
    errors: list[ValidationIssue] = []
    if "injection" in fixture.safety_tags and not fixture.injection_tags:
        errors.append(
            _issue(
                "missing_injection_tags",
                "injection safety tag requires injection sub-tags",
                fixture.id,
            )
        )
    unknown = set(fixture.injection_tags).difference(_INJECTION_TAG_ALIASES)
    if unknown:
        errors.append(
            _issue(
                "unknown_injection_tags",
                f"unknown injection tags: {sorted(unknown)}",
                fixture.id,
            )
        )
    text = "\n".join(file.content for file in fixture.base_files) + fixture.patch
    secret_like = re.search(
        r"(?:sk-[A-Za-z0-9]{8,}|api[_-]?key\s*[=:]|password\s*[=:])", text, re.I
    )
    safety_text = " ".join(
        value or ""
        for value in (
            fixture.provenance.synthetic_notes,
            fixture.provenance.adaptation_notes,
            item.rubric.safety_notes,
        )
    ).lower()
    if secret_like and not any(
        marker in safety_text
        for marker in ("fake", "nonfunctional", "non-functional", "test data")
    ):
        errors.append(
            _issue(
                "functional_secret_like_data",
                "secret-like test data must be marked fake or nonfunctional",
                fixture.id,
            )
        )
    if fixture.safety_tags and not item.rubric.safety_notes:
        errors.append(
            _issue(
                "missing_safety_notes",
                "safety-tagged fixtures require rubric safety_notes",
                fixture.id,
            )
        )
    return errors


def _validate_rubric(item: ValidatedCase) -> list[ValidationIssue]:
    """Validate rubric semantics against gmuse's production message validator."""
    errors: list[ValidationIssue] = []
    for conventional_type in item.rubric.allowed_conventional_types:
        try:
            validate_message(f"{conventional_type}: test", format="conventional")
        except Exception:
            errors.append(
                _issue(
                    "unsupported_conventional_type",
                    f"rubric allows unsupported conventional type '{conventional_type}'",
                    item.rubric.id,
                )
            )
    for concept in item.rubric.required_concepts:
        if concept in item.rubric.forbidden_concepts:
            errors.append(
                _issue(
                    "rubric_contradiction",
                    f"concept '{concept}' is both required and forbidden",
                    item.rubric.id,
                )
            )
    return errors


def _validate_reconstruction(item: ValidatedCase) -> list[ValidationIssue]:
    """Reconstruct one fixture and compare exact staged metadata."""
    fixture = item.fixture
    errors: list[ValidationIssue] = []
    try:
        with reconstruct_fixture(fixture) as repository:
            observed = repository.staged_diff
    except ReconstructionError as error:
        return [_issue("reconstruction_failed", str(error), fixture.id)]
    if observed.hash != fixture.expected_staged_diff_sha256:
        errors.append(
            _issue(
                "digest_mismatch",
                "staged diff digest mismatch; "
                f"expected {fixture.expected_staged_diff_sha256}, observed {observed.hash}",
                fixture.id,
            )
        )
    observed_paths = sorted(observed.files_changed)
    if observed_paths != fixture.expected_files_changed:
        errors.append(
            _issue(
                "changed_paths_mismatch",
                f"changed paths mismatch; expected {fixture.expected_files_changed}, observed {observed_paths}",
                fixture.id,
            )
        )
    return errors


def _validate_policy(
    suite: EvalSuite,
    coverage: CoverageSummary,
    *,
    strict_balance: bool,
) -> tuple[list[ValidationIssue], list[ValidationIssue]]:
    """Evaluate required and advisory coverage policies."""
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    required = set(suite.coverage_policy.required_dimensions)
    advisory = set(suite.coverage_policy.advisory_dimensions)
    for dimension in sorted(required | advisory):
        if dimension not in COVERAGE_DIMENSIONS:
            errors.append(
                _issue(
                    "unknown_coverage_dimension",
                    f"unknown coverage dimension '{dimension}'",
                    suite.id,
                )
            )
            continue
        if coverage.dimensions[dimension]:
            continue
        issue = _issue(
            "coverage_gap", f"no coverage for dimension '{dimension}'", suite.id
        )
        if dimension in required or strict_balance:
            errors.append(issue)
        else:
            warnings.append(issue)
    for dimension, minimum in sorted(suite.coverage_policy.minimum_case_counts.items()):
        actual = len(coverage.dimensions.get(dimension, []))
        if actual < minimum:
            issue = _issue(
                "minimum_coverage",
                f"dimension '{dimension}' has {actual} values, requires {minimum}",
                suite.id,
            )
            if dimension in advisory and not strict_balance:
                warnings.append(issue)
            else:
                errors.append(issue)
    return errors, warnings


def validate_assets(
    assets: EvalAssets,
    suite_id: str = "smoke",
    *,
    strict_balance: bool = False,
    reconstruct: bool = True,
) -> ValidatedSuite:
    """Resolve references and return a structured suite validation result.

    This foundational boundary deliberately performs no model or network work.
    Git reconstruction and domain checks are added by the story-specific
    validators while retaining this result shape.
    """
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    suite = assets.suites.get(suite_id)
    if suite is None:
        report = _report(
            None,
            [
                ValidationIssue(
                    code="missing_suite",
                    asset_id=suite_id,
                    message="suite does not exist",
                )
            ],
            warnings,
        )
        return ValidatedSuite(None, (), report)

    resolved: list[ValidatedCase] = []
    for case_id in suite.case_ids:
        case = assets.cases.get(case_id)
        if case is None:
            errors.append(
                ValidationIssue(
                    code="missing_case", asset_id=case_id, message="case does not exist"
                )
            )
            continue
        fixture = assets.fixtures.get(case.fixture_id)
        if fixture is None:
            errors.append(
                ValidationIssue(
                    code="missing_fixture",
                    asset_id=case.fixture_id,
                    message=f"referenced by case {case.id}",
                )
            )
            continue
        rubric = assets.rubrics.get(case.rubric_id)
        if rubric is None:
            errors.append(
                ValidationIssue(
                    code="missing_rubric",
                    asset_id=case.rubric_id,
                    message=f"referenced by case {case.id}",
                )
            )
            continue
        resolved.append(ValidatedCase(case, fixture, rubric))

    resolved_cases = tuple(resolved)
    coverage = CoverageSummary()
    _add_coverage(coverage, resolved_cases)

    for item in resolved_cases:
        errors.extend(_validate_provenance(item))
        errors.extend(_validate_safety(item))
        errors.extend(_validate_rubric(item))
    if reconstruct:
        seen_fixtures: set[str] = set()
        for item in resolved_cases:
            if item.fixture.id in seen_fixtures:
                continue
            seen_fixtures.add(item.fixture.id)
            errors.extend(_validate_reconstruction(item))

    if suite.suite_kind == "smoke" or suite.id == "smoke":
        core = assets.suites.get("core")
        if core is None:
            errors.append(
                _issue(
                    "missing_core_suite",
                    "smoke validation requires a core suite",
                    suite.id,
                )
            )
        else:
            outside_core = sorted(set(suite.case_ids).difference(core.case_ids))
            if outside_core:
                errors.append(
                    _issue(
                        "smoke_not_core_subset",
                        f"smoke cases outside core: {outside_core}",
                        suite.id,
                    )
                )

    policy_errors, policy_warnings = _validate_policy(
        suite, coverage, strict_balance=strict_balance
    )
    errors.extend(policy_errors)
    warnings.extend(policy_warnings)

    for dimension in suite.coverage_policy.advisory_dimensions:
        if dimension in COVERAGE_DIMENSIONS and not coverage.dimensions[dimension]:
            issue = ValidationIssue(
                code="advisory_coverage_gap",
                asset_id=suite.id,
                message=f"no coverage for advisory dimension '{dimension}'",
            )
            warnings.append(issue)
            if strict_balance:
                errors.append(
                    ValidationIssue(
                        code="required_coverage_gap",
                        asset_id=issue.asset_id,
                        message=issue.message,
                    )
                )

    report = _report(suite, errors, warnings, coverage)
    return ValidatedSuite(suite, resolved_cases if not errors else (), report)


def validate_suite(
    evals_dir: Path | str = "evals",
    suite_id: str = "smoke",
    *,
    strict_balance: bool = False,
) -> ValidatedSuite:
    """Load and validate a named suite without invoking providers."""
    assets, _ = load_suite_assets(evals_dir, suite_id)
    return validate_assets(assets, suite_id, strict_balance=strict_balance)


def add_issues(
    result: ValidatedSuite,
    errors: Sequence[ValidationIssue] | None = None,
    warnings: Sequence[ValidationIssue] | None = None,
) -> ValidatedSuite:
    """Return a result with additional issues while preserving its data."""
    report = result.report.model_copy(
        update={
            "errors": [*result.report.errors, *(errors or ())],
            "warnings": [*result.report.warnings, *(warnings or ())],
        }
    )
    report.status = "failed" if report.errors else "passed"
    return ValidatedSuite(result.suite, result.cases, report)
