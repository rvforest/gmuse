"""Test the audit trail and overlays for manual score review."""

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from tools.evals.gmuse_evals.review_events import (
    ManualAnnotation,
    ManualOverride,
    OverrideChanges,
    ReviewEventError,
    append_review_event,
    apply_review_events,
    load_review_events,
    review_target,
)


@pytest.fixture
def score() -> dict[str, object]:
    return {
        "source": {"run_id": "candidate-run", "entry_id": "entry-1"},
        "effective_ratings": {
            "accuracy": 2,
            "message_quality": 3,
            "style_context_fit": 3,
            "usability": "minor_edit",
            "hard_failed": False,
            "derived_from": "judge_result",
        },
        "hard_failure_gates": [],
        "quality_errors": ["vague"],
        "deterministic_checks": [{"status": "pass"}],
        "judge_configuration": {"model": "judge-model"},
        "judge_result": {"accuracy": 2},
    }


def test_annotation_round_trip_leaves_original_scores_intact(
    tmp_path: Path, score: dict[str, object]
) -> None:
    annotation = ManualAnnotation(
        target=review_target(score, scored_run_id="scored-run"),
        reviewer="reviewer-1",
        rationale="Review the change description.",
    )
    assert load_review_events(tmp_path) == ()
    append_review_event(tmp_path, annotation)
    loaded = load_review_events(tmp_path)
    assert loaded == (annotation,)
    assert annotation.timestamp.tzinfo is not None

    overlay = apply_review_events(score, loaded, scored_run_id="scored-run")
    assert overlay.original == score
    assert overlay.events == (annotation,)
    assert overlay.effective_ratings == score["effective_ratings"]
    assert overlay.effective_quality_errors == ("vague",)
    assert (tmp_path / "annotations.jsonl").is_file()
    assert not (tmp_path / "overrides.jsonl").exists()


def test_overrides_apply_in_append_order_and_preserve_evidence(
    tmp_path: Path, score: dict[str, object]
) -> None:
    original = deepcopy(score)
    target = review_target(score, scored_run_id="scored-run")
    first = ManualOverride(
        target=target,
        reviewer="first",
        rationale="The diff supports the main claim.",
        changes=OverrideChanges(accuracy=4, quality_errors=()),
    )
    second = ManualOverride(
        target=target,
        reviewer="second",
        rationale="Revised assessment after checking applicable context.",
        changes=OverrideChanges(accuracy=3, style_context_fit=None, usability="usable"),
    )
    append_review_event(tmp_path, first)
    append_review_event(tmp_path, second)
    events = load_review_events(tmp_path)
    assert events == (first, second)

    overlay = apply_review_events(score, events, scored_run_id="scored-run")
    assert overlay.effective_ratings == {
        "accuracy": 3,
        "message_quality": 3,
        "style_context_fit": None,
        "usability": "usable",
        "hard_failed": False,
        "derived_from": "manual_override",
    }
    assert overlay.effective_quality_errors == ()
    assert score == overlay.original == original
    assert overlay.original is not score
    assert overlay.original["judge_result"] is not score["judge_result"]


def test_manual_gate_can_be_reversed_and_automated_gate_takes_precedence(
    score: dict[str, object],
) -> None:
    automated_gate = {
        "gate": "privacy_leak",
        "source": "deterministic_check",
        "evidence": "Output matches fixture marker.",
    }
    score["hard_failure_gates"] = [automated_gate]
    target = review_target(score, scored_run_id="scored-run")
    first = ManualOverride(
        target=target,
        reviewer="first",
        rationale="Additional manual finding.",
        changes=OverrideChanges(hard_failure_gates=("other",), usability="usable"),
    )
    second = ManualOverride(
        target=target,
        reviewer="second",
        rationale="Reviewed the additional finding.",
        changes=OverrideChanges(hard_failure_gates=()),
    )

    overlay = apply_review_events(score, [first], scored_run_id="scored-run")
    assert overlay.effective_ratings["usability"] == "unusable"
    assert overlay.effective_ratings["hard_failed"] is True
    assert [gate["gate"] for gate in overlay.effective_hard_failure_gates] == [
        "privacy_leak",
        "other",
    ]

    overlay = apply_review_events(score, [first, second], scored_run_id="scored-run")
    assert overlay.effective_hard_failure_gates == (automated_gate,)
    assert overlay.effective_ratings["usability"] == "unusable"
    assert score["hard_failure_gates"] == [automated_gate]


def test_overlay_is_bound_to_exact_scored_run_and_evidence(
    score: dict[str, object],
) -> None:
    event = ManualOverride(
        target=review_target(score, scored_run_id="scored-run"),
        reviewer="reviewer",
        rationale="Correct the judge's reading.",
        changes=OverrideChanges(accuracy=4),
    )
    overlay = apply_review_events(score, [event], scored_run_id="other-run")
    assert overlay.events == ()

    score["judge_configuration"] = {"model": "different-judge"}
    overlay = apply_review_events(score, [event], scored_run_id="scored-run")
    assert overlay.events == ()


@pytest.mark.parametrize(
    "changes", [{}, {"accuracy": 0}, {"accuracy": True}, {"hard_failed": True}]
)
def test_overrides_require_valid_nonempty_changes(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        OverrideChanges.model_validate(changes)


def test_event_requires_audit_metadata(score: dict[str, object]) -> None:
    target = review_target(score, scored_run_id="scored-run")
    with pytest.raises(ValidationError):
        ManualAnnotation(target=target, reviewer=" ", rationale="note")
    with pytest.raises(ValidationError):
        ManualAnnotation(target=target, reviewer="reviewer", rationale=" ")
    with pytest.raises(ValidationError):
        ManualAnnotation(
            target=target,
            reviewer="reviewer",
            rationale="note",
            timestamp=datetime(2026, 6, 11),
        )


def test_malformed_event_file_reports_path_and_line(tmp_path: Path) -> None:
    (tmp_path / "annotations.jsonl").write_text("invalid\n", encoding="utf-8")
    with pytest.raises(ReviewEventError, match=r"annotations\.jsonl:1"):
        load_review_events(tmp_path)


def test_persisted_event_requires_original_timestamp(
    tmp_path: Path, score: dict[str, object]
) -> None:
    annotation = ManualAnnotation(
        target=review_target(score, scored_run_id="scored-run"),
        reviewer="reviewer",
        rationale="Review this score.",
    )
    missing_timestamp = annotation.model_dump(mode="json", exclude={"timestamp"})
    (tmp_path / "annotations.jsonl").write_text(
        json.dumps(missing_timestamp) + "\n", encoding="utf-8"
    )
    with pytest.raises(ReviewEventError, match=r"annotations\.jsonl:1"):
        load_review_events(tmp_path)


def test_exact_retries_apply_once_and_conflicting_event_id_is_rejected(
    tmp_path: Path, score: dict[str, object]
) -> None:
    target = review_target(score, scored_run_id="scored-run")
    annotation = ManualAnnotation(
        target=target, reviewer="reviewer", rationale="Review this score."
    )
    append_review_event(tmp_path, annotation)
    append_review_event(tmp_path, annotation)
    assert load_review_events(tmp_path) == (annotation,)

    override = ManualOverride(
        event_id=annotation.event_id,
        target=target,
        reviewer="reviewer",
        rationale="Revise the score.",
        changes=OverrideChanges(accuracy=4),
    )
    append_review_event(tmp_path, override)
    with pytest.raises(ReviewEventError, match="Conflicting review event ID"):
        load_review_events(tmp_path)
