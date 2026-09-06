"""Models for evaluation cases, suites, and composition goals."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator

from .schema import (
    COMPOSITION_BOOLEAN_VALUES,
    COMPOSITION_SCENARIOS,
    INJECTION_LOCATION_TAGS,
    INJECTION_PATTERN_TAGS,
    SUPPORTED_FORMATS,
    EvalModel,
    FormatName,
    SuiteKind,
    validate_schema_version as validate_current_schema,
)

SUPPORTED_COMPOSITION_SELECTORS = (
    "fixture.origin",
    "fixture.ecosystem",
    "fixture.change_type",
    "fixture.source_repository",
    "case.format",
    "context.history",
    "context.branch",
    "context.hint",
    "context.max_chars",
    "safety.scenario",
    "safety.tag",
    "safety.injection_pattern",
    "safety.injection_location",
)


class EvalCase(EvalModel):
    """Bind a fixture and rubric to generation context options.

    Cases avoid duplicating fixture content across formats and context settings.

    Example:
        >>> case = EvalCase(id="docs", fixture_id="fixture", rubric_id="rubric", ...)
        >>> case.formats
        ['freeform']
    """

    schema_version: str
    id: str = Field(min_length=1)
    revision: int = Field(gt=0)
    fixture_id: str = Field(min_length=1)
    rubric_id: str = Field(min_length=1)
    formats: list[FormatName] = Field(min_length=1)
    history_depth: int | None = Field(default=None, ge=0)
    include_branch: bool
    user_hint: str | None = None
    max_chars: int | None = Field(default=None, gt=0)
    tags: list[str]

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        """Reject case documents from unsupported schema revisions."""
        return validate_current_schema(value)

    @field_validator("formats")
    @classmethod
    def validate_unique_formats(cls, value: list[FormatName]) -> list[FormatName]:
        """Ensure each case contributes at most once to a format count."""
        if len(value) != len(set(value)):
            raise ValueError("case formats must be unique")
        return value

    @field_validator("tags")
    @classmethod
    def validate_unique_tags(cls, value: list[str]) -> list[str]:
        """Keep case classification deterministic."""
        if len(value) != len(set(value)):
            raise ValueError("case tags must be unique")
        return value


class CompositionGoal(EvalModel):
    """Require or recommend a minimum count for one suite scenario.

    Example:
        >>> goal = CompositionGoal(
        ...     selector="case.format", value="conventional", minimum_cases=1,
        ...     severity="required",
        ... )
        >>> goal.minimum_cases
        1
    """

    selector: str
    value: str = Field(min_length=1)
    minimum_cases: int = Field(gt=0)
    severity: Literal["required", "advisory"]

    @field_validator("selector")
    @classmethod
    def validate_selector(cls, value: str) -> str:
        """Require one of the documented scenario selectors."""
        if value not in SUPPORTED_COMPOSITION_SELECTORS:
            raise ValueError(f"unsupported composition selector {value!r}")
        return value

    @model_validator(mode="after")
    def validate_value(self) -> CompositionGoal:
        """Reject sentinel values and values outside finite selector domains."""
        if self.value in {"none", "not-used", "not-applicable"}:
            raise ValueError("composition goals require an explicit scenario value")
        finite_values: dict[str, set[str]] = {
            "fixture.origin": {"real", "adapted", "synthetic"},
            "case.format": set(SUPPORTED_FORMATS),
            "context.history": set(COMPOSITION_BOOLEAN_VALUES),
            "context.branch": set(COMPOSITION_BOOLEAN_VALUES),
            "context.hint": set(COMPOSITION_BOOLEAN_VALUES),
            "context.max_chars": set(COMPOSITION_BOOLEAN_VALUES),
            "safety.scenario": set(COMPOSITION_SCENARIOS),
            "safety.injection_pattern": set(INJECTION_PATTERN_TAGS),
            "safety.injection_location": set(INJECTION_LOCATION_TAGS),
        }
        allowed = finite_values.get(self.selector)
        if allowed is not None and self.value not in allowed:
            raise ValueError(
                f"unsupported value {self.value!r} for selector {self.selector!r}"
            )
        return self


class EvalSuite(EvalModel):
    """A named set of ordered eval case IDs, tracked by revision.

    Stable suite membership makes focused smoke, core, and safety runs reusable.

    Example:
        >>> suite = EvalSuite(id="smoke", revision=1, suite_kind="smoke", ...)
        >>> suite.id
        'smoke'
    """

    schema_version: str
    id: str = Field(min_length=1)
    revision: int = Field(gt=0)
    suite_kind: SuiteKind
    case_ids: list[str] = Field(min_length=1)
    composition_goals: list[CompositionGoal] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        """Reject suite documents from unsupported schema revisions."""
        return validate_current_schema(value)

    @field_validator("case_ids")
    @classmethod
    def validate_unique_case_ids(cls, value: list[str]) -> list[str]:
        """Keep suite membership unambiguous."""
        if len(value) != len(set(value)):
            raise ValueError("suite case IDs must be unique")
        return value

    @model_validator(mode="after")
    def validate_composition_goals(self) -> EvalSuite:
        """Reject repeated selector/value goals."""
        seen: set[tuple[str, str]] = set()
        for goal in self.composition_goals:
            key = (goal.selector, goal.value)
            if key in seen:
                raise ValueError(
                    "composition goals may not repeat selector/value "
                    f"{goal.selector}={goal.value}"
                )
            seen.add(key)
        return self


__all__ = [
    "CompositionGoal",
    "EvalCase",
    "EvalSuite",
    "SUPPORTED_COMPOSITION_SELECTORS",
]
