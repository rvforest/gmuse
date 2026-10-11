"""Models for shared scoring profiles and case-specific rubrics."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator

from .schema import (
    EvalModel,
    UsabilityLabel,
    validate_schema_version as validate_current_schema,
)


class ScoringDimension(EvalModel):
    """One subjective dimension in a reusable scoring profile.

    Each dimension has four explicit anchors. The anchors describe a rating;
    they are not weights and are never combined into an aggregate score.

    Example:
        >>> ScoringDimension(
        ...     id="accuracy", label="Accuracy", description="Faithfulness",
        ...     anchors={1: "wrong", 2: "incomplete", 3: "mostly right", 4: "right"},
        ... ).anchors[4]
        'right'
    """

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)
    anchors: dict[int, str]

    @field_validator("anchors")
    @classmethod
    def validate_anchors(cls, value: dict[int, str]) -> dict[int, str]:
        """Require non-empty, distinct meanings for ratings one through four."""
        if set(value) != {1, 2, 3, 4}:
            raise ValueError(
                "scoring dimensions require exactly anchors 1, 2, 3, and 4"
            )
        if any(not text.strip() for text in value.values()):
            raise ValueError("scoring dimension anchors must be non-empty")
        if len(set(value.values())) != 4:
            raise ValueError("scoring dimension anchors must be distinct")
        return value


class UsabilityExample(EvalModel):
    """An annotated illustration of a profile-level usability label.

    Example:
        >>> UsabilityExample(
        ...     message="docs: explain validation", usability="usable",
        ...     rationale="Specific and concise.",
        ... ).usability
        'usable'
    """

    message: str = Field(min_length=1)
    usability: UsabilityLabel
    rationale: str = Field(min_length=1)


class ScoringProfile(EvalModel):
    """Reusable four-level ratings and categorical usability definitions.

    Profiles are reviewable source assets. They do not run a scorer or define
    weights, thresholds, or an aggregate metric.

    Example:
        >>> profile = ScoringProfile(
        ...     schema_version="1.0", id="profile", revision=1,
        ...     dimensions=[ScoringDimension(
        ...         id="accuracy", label="Accuracy", description="Faithfulness",
        ...         anchors={1: "wrong", 2: "incomplete", 3: "mostly right", 4: "right"},
        ...     )],
        ...     usability_labels={"usable": "ready", "minor_edit": "small",
        ...                       "major_edit": "large", "unusable": "no"},
        ...     usability_examples=[
        ...         UsabilityExample(message="small", usability="minor_edit", rationale="small"),
        ...         UsabilityExample(message="large", usability="major_edit", rationale="large"),
        ...     ],
        ... )
        >>> profile.revision
        1
    """

    schema_version: str
    id: str = Field(min_length=1)
    revision: int = Field(gt=0)
    dimensions: list[ScoringDimension] = Field(min_length=1)
    usability_labels: dict[UsabilityLabel, str]
    usability_examples: list[UsabilityExample] = Field(min_length=2)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        """Reject scoring profiles from unsupported schema revisions."""
        return validate_current_schema(value)

    @model_validator(mode="after")
    def validate_profile(self) -> ScoringProfile:
        """Require unique dimensions and illustrations for intermediate labels."""
        ids = [dimension.id for dimension in self.dimensions]
        if len(ids) != len(set(ids)):
            raise ValueError("scoring profile dimension IDs must be unique")
        if set(self.usability_labels) != {
            "usable",
            "minor_edit",
            "major_edit",
            "unusable",
        }:
            raise ValueError("scoring profiles require exactly four usability labels")
        if any(not label.strip() for label in self.usability_labels.values()):
            raise ValueError("usability label definitions must be non-empty")
        examples = {example.usability for example in self.usability_examples}
        if not {"minor_edit", "major_edit"} <= examples:
            raise ValueError(
                "scoring profiles require usability examples for minor_edit and major_edit"
            )
        return self


class RubricCriterion(EvalModel):
    """One independently assessable positive or required rubric expectation.

    Example:
        >>> criterion = RubricCriterion(
        ...     id="purpose", dimension="accuracy", importance="major",
        ...     description="Names the primary change.",
        ... )
        >>> criterion.importance
        'major'
    """

    id: str = Field(min_length=1)
    dimension: str = Field(min_length=1)
    importance: Literal["major", "minor"]
    description: str = Field(min_length=1)


class FailureCondition(EvalModel):
    """One observable undesirable outcome in a case rubric.

    Example:
        >>> condition = FailureCondition(
        ...     id="unsupported-claim", error_category="hallucination",
        ...     severity="major", description="Claims absent work.",
        ... )
        >>> condition.error_category
        'hallucination'
    """

    id: str = Field(min_length=1)
    error_category: str = Field(min_length=1)
    severity: Literal["major", "minor"]
    description: str = Field(min_length=1)


class DeterministicGate(EvalModel):
    """An objective gate whose evidence can make a result unusable.

    Semantic instruction obedience is intentionally absent: it belongs to a
    later judge-scoring feature.

    Example:
        >>> gate = DeterministicGate(
        ...     id="valid", gate="production_validation", evidence="validator",
        ... )
        >>> gate.gate
        'production_validation'
    """

    id: str = Field(min_length=1)
    gate: Literal[
        "production_validation",
        "max_chars",
        "fake_secret_leak",
        "literal_injection_marker",
    ]
    evidence: str = Field(min_length=1)


class AnnotatedExample(EvalModel):
    """A case-specific calibration example, never an exact-match target.

    Example:
        >>> example = AnnotatedExample(
        ...     message="docs: explain validation", ratings={"accuracy": 4},
        ...     usability="usable", expected_gate_ids=[], expected_failure_ids=[],
        ...     rationale="Accurate.",
        ... )
        >>> example.usability
        'usable'
    """

    message: str = Field(min_length=1)
    ratings: dict[str, int] = Field(default_factory=dict)
    usability: UsabilityLabel
    expected_gate_ids: list[str] = Field(default_factory=list)
    expected_failure_ids: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)

    @field_validator("expected_gate_ids", "expected_failure_ids")
    @classmethod
    def validate_unique_references(cls, value: list[str]) -> list[str]:
        """Reject duplicate references in one expected assessment."""
        if len(value) != len(set(value)):
            raise ValueError("example references must be unique")
        return value


class EvalRubric(EvalModel):
    """Apply one scoring profile to one evaluation case.

    A rubric contains case-specific criteria, failures, objective gates, and
    two annotated examples.

    Example:
        >>> rubric = EvalRubric(
        ...     schema_version="1.0", id="docs", revision=1,
        ...     scoring_profile_id="profile", criteria=[...],
        ...     failure_conditions=[...], deterministic_gates=[...],
        ...     examples=[..., ...],
        ... )
        >>> rubric.scoring_profile_id
        'profile'
    """

    schema_version: str
    id: str = Field(min_length=1)
    revision: int = Field(gt=0)
    scoring_profile_id: str = Field(min_length=1)
    criteria: list[RubricCriterion] = Field(min_length=1)
    failure_conditions: list[FailureCondition] = Field(min_length=1)
    deterministic_gates: list[DeterministicGate] = Field(min_length=1)
    examples: list[AnnotatedExample] = Field(min_length=2, max_length=2)
    notes: str | None = None
    safety_notes: str | None = None

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        """Reject rubric documents from unsupported schema revisions."""
        return validate_current_schema(value)

    @model_validator(mode="after")
    def validate_item_ids(self) -> EvalRubric:
        """Keep all local rubric references unique and deterministic."""
        ids = [
            *(criterion.id for criterion in self.criteria),
            *(condition.id for condition in self.failure_conditions),
            *(gate.id for gate in self.deterministic_gates),
        ]
        if len(ids) != len(set(ids)):
            raise ValueError("rubric item IDs must be globally unique")
        messages = [example.message for example in self.examples]
        if len(messages) != len(set(messages)):
            raise ValueError("rubric example messages must be unique")
        return self


__all__ = [
    "AnnotatedExample",
    "DeterministicGate",
    "EvalRubric",
    "FailureCondition",
    "RubricCriterion",
    "ScoringDimension",
    "ScoringProfile",
    "UsabilityExample",
]
