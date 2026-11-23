"""Typed boundaries shared by eval validation and future runner adapters."""

from __future__ import annotations

from dataclasses import dataclass

from .models import (
    EvalCase,
    EvalFixture,
    EvalRubric,
    EvalSuite,
    ScoringProfile,
    ValidationReport,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolvedCase:
    """An eval case whose fixture, rubric, and scoring profile exist.

    Resolution does not imply that domain validation passed; callers must check
    the containing validation report before execution.

    Example:
        >>> resolved = ResolvedCase(
        ...     case=case, fixture=fixture, rubric=rubric, scoring_profile=profile
        ... )
        >>> resolved.fixture.id == resolved.case.fixture_id
        True
    """

    case: EvalCase
    fixture: EvalFixture
    rubric: EvalRubric
    scoring_profile: ScoringProfile


@dataclass(frozen=True, slots=True, kw_only=True)
class SuiteValidationResult:
    """A selected suite, its resolved cases, and its validation report.

    Example:
        >>> result = validate_suite("evals", "smoke")
        >>> result.report.status
        'passed'
    """

    suite: EvalSuite | None
    resolved_cases: tuple[ResolvedCase, ...]
    report: ValidationReport
