"""Models returned by evaluation validation and composition reporting."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from .schema import EvalModel


class CompositionGoalResult(EvalModel):
    """Observed result for one declared composition goal.

    Example:
        >>> CompositionGoalResult(
        ...     selector="case.format", value="freeform", observed_cases=1,
        ...     minimum_cases=1, severity="required", status="met",
        ... ).status
        'met'
    """

    selector: str
    value: str
    observed_cases: int = Field(ge=0)
    minimum_cases: int = Field(gt=0)
    severity: Literal["required", "advisory"]
    status: Literal["met", "shortfall"]


class CompositionEntry(EvalModel):
    """One counted, human-readable contribution to suite composition.

    Example:
        >>> CompositionEntry(key="change:docs", label="Documentation", case_count=1).case_count
        1
    """

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    case_count: int = Field(ge=1)


class CompositionGroup(EvalModel):
    """An ordered report group such as Changes or Safety scenarios.

    Example:
        >>> group = CompositionGroup(
        ...     name="Changes",
        ...     entries=[CompositionEntry(key="change:docs", label="Documentation", case_count=1)],
        ... )
        >>> group.name
        'Changes'
    """

    name: str = Field(min_length=1)
    entries: list[CompositionEntry] = Field(min_length=1)


class SuiteComposition(EvalModel):
    """Counted composition of successfully resolved suite cases.

    Example:
        >>> SuiteComposition(groups=[]).groups
        []
    """

    groups: list[CompositionGroup] = Field(default_factory=list)

    def group(self, name: str) -> CompositionGroup | None:
        """Return a named group, if the resolved cases contributed to it.

        Example:
            >>> SuiteComposition(groups=[]).group("Changes") is None
            True
        """
        return next((item for item in self.groups if item.name == name), None)


class ValidationIssue(EvalModel):
    """One actionable validation error or warning.

    Structured issues support both human CLI rendering and future automation.

    Example:
        >>> ValidationIssue(message="missing fixture", asset_id="case-1").render()
        'case-1: missing fixture'
    """

    code: str = "validation_error"
    message: str = Field(min_length=1)
    path: str | None = None
    asset_id: str | None = None

    def render(self) -> str:
        """Return a compact human-readable issue description.

        Asset IDs take precedence over source paths to keep CLI output concise.

        Returns:
            Issue text prefixed by an asset ID or path when available.

        Example:
            >>> ValidationIssue(message="missing", asset_id="fixture").render()
            'fixture: missing'
        """
        prefix = self.asset_id or self.path
        return f"{prefix}: {self.message}" if prefix else self.message


class ValidationReport(EvalModel):
    """Structured result shared by the CLI and future eval runners.

    The report prevents downstream tools from having to parse CLI text.

    Example:
        >>> report = ValidationReport(...)
        >>> report.status in {"passed", "failed"}
        True
    """

    schema_version: str = Field(min_length=1)
    suite_id: str = Field(min_length=1)
    suite_revision: int | None = Field(default=None, gt=0)
    status: Literal["passed", "failed"]
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    composition: SuiteComposition = Field(default_factory=SuiteComposition)
    composition_goals: list[CompositionGoalResult] = Field(default_factory=list)
    validated_at: datetime


__all__ = [
    "CompositionEntry",
    "CompositionGoalResult",
    "CompositionGroup",
    "SuiteComposition",
    "ValidationIssue",
    "ValidationReport",
]
