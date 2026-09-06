"""Concise builders for canonical schema-1.0 eval test assets."""

from __future__ import annotations

from tools.evals.gmuse_evals.load import EvalAssets
from tools.evals.gmuse_evals.models import (
    AnnotatedExample,
    DeterministicGate,
    EvalCase,
    EvalFixture,
    EvalRubric,
    EvalSuite,
    FailureCondition,
    RubricCriterion,
    ScoringDimension,
    ScoringProfile,
    UsabilityExample,
)


def make_profile(profile_id: str = "profile") -> ScoringProfile:
    """Return a minimal complete scoring profile."""
    return ScoringProfile(
        schema_version="1.0",
        id=profile_id,
        revision=1,
        dimensions=[
            ScoringDimension(
                id="accuracy",
                label="Accuracy",
                description="Faithfulness to the staged change.",
                anchors={
                    1: "Incorrect",
                    2: "Materially incomplete",
                    3: "Mostly accurate",
                    4: "Accurate and specific",
                },
            )
        ],
        usability_labels={
            "usable": "Ready to use",
            "minor_edit": "Needs a small edit",
            "major_edit": "Needs a substantial edit",
            "unusable": "Cannot be used",
        },
        usability_examples=[
            UsabilityExample(
                message="docs: clarify behavior",
                usability="minor_edit",
                rationale="Accurate but imprecise.",
            ),
            UsabilityExample(
                message="update things",
                usability="major_edit",
                rationale="Too vague for review.",
            ),
        ],
    )


def make_rubric(
    rubric_id: str = "rubric",
    *,
    profile_id: str = "profile",
    safety_notes: str | None = None,
    include_max_chars_gate: bool = False,
) -> EvalRubric:
    """Return a minimal complete rubric using the requested profile."""
    gates = [
        DeterministicGate(
            id="message-valid",
            gate="production_validation",
            evidence="Use production validation.",
        )
    ]
    if include_max_chars_gate:
        gates.append(
            DeterministicGate(
                id="within-limit",
                gate="max_chars",
                evidence="Compare against case max_chars.",
            )
        )
    return EvalRubric(
        schema_version="1.0",
        id=rubric_id,
        revision=1,
        scoring_profile_id=profile_id,
        criteria=[
            RubricCriterion(
                id="describes-change",
                dimension="accuracy",
                importance="major",
                description="Describes the primary staged change.",
            )
        ],
        failure_conditions=[
            FailureCondition(
                id="unsupported-claim",
                error_category="hallucination",
                severity="major",
                description="Makes a material unsupported claim.",
            )
        ],
        deterministic_gates=gates,
        examples=[
            AnnotatedExample(
                message="docs: explain validation",
                ratings={"accuracy": 4},
                usability="usable",
                rationale="Accurate and specific.",
            ),
            AnnotatedExample(
                message="feat: add an absent provider",
                ratings={"accuracy": 1},
                usability="unusable",
                expected_failure_ids=["unsupported-claim"],
                rationale="Makes an unsupported claim.",
            ),
        ],
        safety_notes=safety_notes,
    )


def make_case(
    fixture: EvalFixture,
    rubric: EvalRubric,
    *,
    case_id: str = "case",
    formats: list[str] | None = None,
    history_depth: int | None = 0,
    max_chars: int | None = None,
    tags: list[str] | None = None,
) -> EvalCase:
    """Return a case binding the supplied fixture and rubric."""
    return EvalCase.model_validate(
        {
            "schema_version": "1.0",
            "id": case_id,
            "revision": 1,
            "fixture_id": fixture.id,
            "rubric_id": rubric.id,
            "formats": formats or ["freeform"],
            "history_depth": history_depth,
            "include_branch": False,
            "max_chars": max_chars,
            "tags": tags or [],
        }
    )


def make_suite(case: EvalCase, suite_id: str = "custom") -> EvalSuite:
    """Return a custom suite containing one case."""
    return EvalSuite(
        schema_version="1.0",
        id=suite_id,
        revision=1,
        suite_kind="custom",
        case_ids=[case.id],
    )


def make_assets(
    fixture: EvalFixture,
    *,
    rubric: EvalRubric | None = None,
    profile: ScoringProfile | None = None,
    case: EvalCase | None = None,
    suite: EvalSuite | None = None,
) -> EvalAssets:
    """Return a complete in-memory catalog around one fixture."""
    profile = profile or make_profile()
    rubric = rubric or make_rubric(profile_id=profile.id)
    case = case or make_case(fixture, rubric)
    suite = suite or make_suite(case)
    return EvalAssets(
        fixtures={fixture.id: fixture},
        rubrics={rubric.id: rubric},
        cases={case.id: case},
        suites={suite.id: suite},
        scoring_profiles={profile.id: profile},
    )
