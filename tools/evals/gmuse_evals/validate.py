"""Orchestrate loading, reference resolution, and eval-domain validation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .composition import collect_suite_composition, validate_composition_goals
from .load import EvalAssets, load_suite_assets
from .models import (
    SCHEMA_VERSION,
    CompositionGoalResult,
    EvalSuite,
    SuiteComposition,
    ValidationIssue,
    ValidationReport,
)
from .results import ResolvedCase, SuiteValidationResult
from .validation_rules import (
    validate_history,
    validate_profile,
    validate_provenance,
    validate_reconstruction,
    validate_rubric,
    validate_safety,
)


def _build_report(
    suite_id: str,
    suite_revision: int | None,
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
    composition: SuiteComposition | None = None,
    composition_goals: list[CompositionGoalResult] | None = None,
) -> ValidationReport:
    """Build a consistent report for successful and failed validation."""
    return ValidationReport(
        schema_version=SCHEMA_VERSION,
        suite_id=suite_id,
        suite_revision=suite_revision,
        status="failed" if errors else "passed",
        errors=errors,
        warnings=warnings,
        composition=composition or SuiteComposition(),
        composition_goals=composition_goals or [],
        validated_at=datetime.now(timezone.utc),
    )


def _issue(code: str, message: str, asset_id: str) -> ValidationIssue:
    return ValidationIssue(code=code, asset_id=asset_id, message=message)


def _resolve_cases(
    assets: EvalAssets,
    suite: EvalSuite,
    errors: list[ValidationIssue],
) -> tuple[ResolvedCase, ...]:
    """Resolve the selected suite graph while retaining all reference errors."""
    resolved: list[ResolvedCase] = []
    load_error_ids = {issue.asset_id for issue in assets.issues}
    for case_id in suite.case_ids:
        case = assets.cases.get(case_id)
        if case is None:
            if case_id not in load_error_ids:
                errors.append(_issue("missing_case", "case does not exist", case_id))
            continue

        fixture = assets.fixtures.get(case.fixture_id)
        if fixture is None:
            if case.fixture_id not in load_error_ids:
                errors.append(
                    _issue(
                        "missing_fixture",
                        f"referenced by case {case.id}",
                        case.fixture_id,
                    )
                )
            continue

        rubric = assets.rubrics.get(case.rubric_id)
        if rubric is None:
            if case.rubric_id not in load_error_ids:
                errors.append(
                    _issue(
                        "missing_rubric",
                        f"referenced by case {case.id}",
                        case.rubric_id,
                    )
                )
            continue

        profile = assets.scoring_profiles.get(rubric.scoring_profile_id)
        if profile is None:
            if rubric.scoring_profile_id not in load_error_ids:
                errors.append(
                    _issue(
                        "missing_scoring_profile",
                        f"referenced by rubric {rubric.id}",
                        rubric.scoring_profile_id,
                    )
                )
            continue

        resolved.append(
            ResolvedCase(
                case=case,
                fixture=fixture,
                rubric=rubric,
                scoring_profile=profile,
            )
        )
    return tuple(resolved)


def _validate_smoke_subset(
    assets: EvalAssets,
    suite: EvalSuite,
    errors: list[ValidationIssue],
) -> None:
    """Require every smoke case to remain part of the core suite."""
    if suite.suite_kind != "smoke":
        return
    core = assets.suites.get("core")
    if core is None:
        if "core" not in {issue.asset_id for issue in assets.issues}:
            errors.append(
                _issue(
                    "missing_core_suite",
                    "smoke validation requires a core suite",
                    suite.id,
                )
            )
        return
    outside_core = sorted(set(suite.case_ids).difference(core.case_ids))
    if outside_core:
        errors.append(
            _issue(
                "smoke_not_core_subset",
                f"smoke cases outside core: {outside_core}",
                suite.id,
            )
        )


def _validate_resolved_cases(
    cases: tuple[ResolvedCase, ...],
    *,
    reconstruct: bool,
) -> list[ValidationIssue]:
    """Apply domain rules without repeating fixture- or profile-level errors."""
    errors: list[ValidationIssue] = []
    seen_profiles: set[str] = set()
    seen_provenance: set[str] = set()
    invalid_history_cases: set[str] = set()

    for item in cases:
        if item.scoring_profile.id not in seen_profiles:
            seen_profiles.add(item.scoring_profile.id)
            errors.extend(validate_profile(item.scoring_profile))
        if item.fixture.id not in seen_provenance:
            seen_provenance.add(item.fixture.id)
            errors.extend(validate_provenance(item.fixture))
        errors.extend(validate_safety(item))
        errors.extend(validate_rubric(item))
        history_errors = validate_history(item)
        if history_errors:
            invalid_history_cases.add(item.case.id)
            errors.extend(history_errors)

    if not reconstruct:
        return errors

    seen_reconstructions: set[str] = set()
    for item in cases:
        if item.case.id in invalid_history_cases:
            continue
        if item.fixture.id in seen_reconstructions:
            continue
        seen_reconstructions.add(item.fixture.id)
        errors.extend(validate_reconstruction(item.fixture))
    return errors


def validate_assets(
    assets: EvalAssets,
    suite_id: str = "smoke",
    *,
    strict_composition: bool = False,
    reconstruct: bool = True,
) -> SuiteValidationResult:
    """Validate a loaded suite graph without invoking model providers.

    Args:
        assets: Loaded full-catalog or selected-graph assets.
        suite_id: Stable ID of the suite to validate.
        strict_composition: Promote advisory composition shortfalls to errors.
        reconstruct: Rebuild and verify fixture repositories when true.

    Returns:
        The selected suite, resolved cases, and structured validation report.

    Example:
        >>> result = validate_assets(load_assets("evals"), "smoke")
        >>> result.report.status
        'passed'
    """
    errors = list(assets.issues)
    warnings: list[ValidationIssue] = []
    suite = assets.suites.get(suite_id)
    if suite is None:
        errors.append(
            ValidationIssue(
                code="missing_suite",
                asset_id=suite_id,
                message="suite does not exist",
            )
        )
        return SuiteValidationResult(
            suite=None,
            resolved_cases=(),
            report=_build_report(suite_id, None, errors, warnings),
        )

    resolved_cases = _resolve_cases(assets, suite, errors)
    composition = collect_suite_composition(resolved_cases)
    errors.extend(_validate_resolved_cases(resolved_cases, reconstruct=reconstruct))
    _validate_smoke_subset(assets, suite, errors)

    goal_results, goal_errors, goal_warnings = validate_composition_goals(
        suite,
        resolved_cases,
        strict=strict_composition,
    )
    errors.extend(goal_errors)
    warnings.extend(goal_warnings)
    report = _build_report(
        suite.id,
        suite.revision,
        errors,
        warnings,
        composition,
        goal_results,
    )
    return SuiteValidationResult(
        suite=suite,
        resolved_cases=resolved_cases,
        report=report,
    )


def validate_suite(
    evals_dir: Path | str = "evals",
    suite_id: str = "smoke",
    *,
    strict_composition: bool = False,
) -> SuiteValidationResult:
    """Load and validate one suite's selected asset graph offline.

    Args:
        evals_dir: Root directory containing eval assets.
        suite_id: Stable suite ID to validate.
        strict_composition: Promote advisory composition shortfalls to errors.

    Returns:
        The selected suite, resolved cases, and structured validation report.

    Raises:
        EvalLoadError: If discovery or the selected suite cannot be parsed.

    Example:
        >>> validate_suite("evals", "smoke").report.status
        'passed'
    """
    assets, _ = load_suite_assets(evals_dir, suite_id, strict=False)
    return validate_assets(
        assets,
        suite_id,
        strict_composition=strict_composition,
    )
