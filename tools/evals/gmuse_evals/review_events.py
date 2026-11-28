"""Append manual review events and overlay them on immutable automated scores."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable, Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    model_validator,
)

from .taxonomy import HardFailureGateName, QualityError, ScoreRating, UsabilityLabel

_NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
_RATING_FIELDS = ("accuracy", "message_quality", "style_context_fit", "usability")
_EVENT_FILES = {"annotation": "annotations.jsonl", "override": "overrides.jsonl"}
_PERSISTED_EVENT_FIELDS = {"schema_version", "event_id", "timestamp"}


class ReviewEventError(ValueError):
    """A review event or its automated score cannot be interpreted safely."""


class _ReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReviewTarget(_ReviewModel):
    """Identify one exact automated result in one scored run."""

    scored_run_id: _NonBlank
    source_run_id: _NonBlank
    entry_id: _NonBlank
    score_digest: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class OverrideChanges(_ReviewModel):
    """Replace only explicitly supplied ratings, categories, and manual gates.

    Explicit None clears a rating. Empty lists clear effective quality errors
    or previously added manual gates.
    """

    accuracy: ScoreRating | None = None
    message_quality: ScoreRating | None = None
    style_context_fit: ScoreRating | None = None
    usability: UsabilityLabel | None = None
    quality_errors: tuple[QualityError, ...] = ()
    hard_failure_gates: tuple[HardFailureGateName, ...] = ()

    @model_validator(mode="after")
    def validate_changes(self) -> OverrideChanges:
        """Require at least one field change and unique category names."""
        if not self.model_fields_set:
            raise ValueError("an override must change at least one field")
        if len(set(self.quality_errors)) != len(self.quality_errors):
            raise ValueError("quality errors must be distinct")
        if len(set(self.hard_failure_gates)) != len(self.hard_failure_gates):
            raise ValueError("hard failure gates must be distinct")
        return self


class _ReviewEvent(_ReviewModel):
    schema_version: Literal[1] = 1
    event_id: UUID = Field(default_factory=uuid4)
    target: ReviewTarget
    reviewer: _NonBlank
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rationale: _NonBlank


class ManualAnnotation(_ReviewEvent):
    """Record a reviewer note without changing effective results."""

    kind: Literal["annotation"] = "annotation"


class ManualOverride(_ReviewEvent):
    """Record a reviewer correction to selected effective results."""

    kind: Literal["override"] = "override"
    changes: OverrideChanges


ReviewEvent = ManualAnnotation | ManualOverride
_EVENT_ADAPTER = TypeAdapter(Annotated[ReviewEvent, Field(discriminator="kind")])


@dataclass(frozen=True, slots=True)
class ReviewOverlay:
    """An inspectable copy of the automated result and its reviewed state."""

    original: dict[str, Any]
    events: tuple[ReviewEvent, ...]
    effective_ratings: dict[str, Any]
    effective_hard_failure_gates: tuple[dict[str, Any], ...]
    effective_quality_errors: tuple[str, ...]


def review_target(scoring: Mapping[str, Any], *, scored_run_id: str) -> ReviewTarget:
    """Bind review to the exact automated result and its scored run.

    Args:
        scoring: Metadata from the original native Inspect score.
        scored_run_id: Identity of the scored log containing the result.

    Returns:
        Source run and entry identity plus a digest of the automated metadata.

    Raises:
        ReviewEventError: If the metadata lacks a source identity or cannot
            be serialized as JSON.
    """
    source = scoring.get("source")
    if not isinstance(source, Mapping):
        raise ReviewEventError("The automated score is missing its source identity.")
    source_run_id = source.get("run_id")
    entry_id = source.get("entry_id")
    if not isinstance(source_run_id, str) or not isinstance(entry_id, str):
        raise ReviewEventError("The automated score is missing its source identity.")
    try:
        canonical = json.dumps(
            dict(scoring), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        return ReviewTarget(
            scored_run_id=scored_run_id,
            source_run_id=source_run_id,
            entry_id=entry_id,
            score_digest=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        )
    except (TypeError, ValueError) as error:
        raise ReviewEventError(
            "The automated score has invalid source identity or JSON metadata."
        ) from error


def _event_json(event: ReviewEvent) -> str:
    record = event.model_dump(mode="json")
    if isinstance(event, ManualOverride):
        # Preserve the difference between omitted fields and explicit nulls.
        record["changes"] = event.changes.model_dump(mode="json", exclude_unset=True)
    return json.dumps(record, separators=(",", ":"), sort_keys=True)


def _unique_events(events: Iterable[ReviewEvent]) -> Iterator[ReviewEvent]:
    seen: dict[UUID, str] = {}
    for event in events:
        serialized = _event_json(event)
        previous = seen.get(event.event_id)
        if previous is None:
            seen[event.event_id] = serialized
            yield event
        elif previous != serialized:
            raise ReviewEventError(f"Conflicting review event ID: {event.event_id}")


def append_review_event(directory: Path, event: ReviewEvent) -> Path:
    """Append one event to the annotation or override JSONL sidecar.

    Args:
        directory: Directory for the review sidecars, created if needed.
        event: Annotation or override to append.

    Returns:
        Path to the JSONL sidecar for the event kind.

    Raises:
        ReviewEventError: If the append writes only part of the event.
        OSError: If the directory or sidecar cannot be opened or written,
            or the write cannot be synced.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / _EVENT_FILES[event.kind]
    payload = (_event_json(event) + "\n").encode("utf-8")
    # A single append write keeps concurrent records from interleaving.
    with path.open("ab", buffering=0) as handle:
        if handle.write(payload) != len(payload):
            raise ReviewEventError(f"Incomplete review event write: {path}")
        os.fsync(handle.fileno())
    return path


def _read_events(path: Path, expected_kind: str) -> Iterator[ReviewEvent]:
    try:
        handle = path.open("rb")
    except FileNotFoundError:
        return
    with handle:
        for number, line in enumerate(handle, start=1):
            try:
                event = _EVENT_ADAPTER.validate_json(line)
            except ValidationError:
                raise ReviewEventError(
                    f"{path}:{number}: invalid review event"
                ) from None
            if (
                not line.endswith(b"\n")
                or event.kind != expected_kind
                or not _PERSISTED_EVENT_FIELDS <= event.model_fields_set
            ):
                raise ReviewEventError(f"{path}:{number}: invalid review event")
            yield event


def load_review_events(directory: Path) -> tuple[ReviewEvent, ...]:
    """Load annotations and then overrides, preserving each file's append order.

    Missing sidecars are empty. Identical retried events apply once. A malformed
    row or conflicting reuse of an event identifier raises ReviewEventError.
    """
    return tuple(
        _unique_events(
            event
            for kind, filename in _EVENT_FILES.items()
            for event in _read_events(directory / filename, kind)
        )
    )


def _overlay_gates(
    event: ManualOverride, automated_gates: tuple[dict[str, Any], ...]
) -> tuple[dict[str, Any], ...]:
    automated_names = {gate["gate"] for gate in automated_gates}
    return tuple(
        {
            "gate": name,
            "source": "manual_override",
            "evidence": f"Manual review event {event.event_id}.",
        }
        for name in event.changes.hard_failure_gates
        if name not in automated_names
    )


def apply_review_events(
    scoring: Mapping[str, Any],
    events: Iterable[ReviewEvent],
    *,
    scored_run_id: str,
) -> ReviewOverlay:
    """Return the effective review overlay for the exact automated score.

    Overrides are applied in input order. They can replace selected ratings
    and quality errors and change manually added gates. Automated gates always
    remain effective and force unusable status.
    """
    target = review_target(scoring, scored_run_id=scored_run_id)
    matching = tuple(
        event for event in _unique_events(events) if event.target == target
    )
    original = deepcopy(dict(scoring))
    ratings = dict(original["effective_ratings"])
    automated_gates = tuple(deepcopy(original["hard_failure_gates"]))
    effective_errors = tuple(original["quality_errors"])
    manual_gates: tuple[dict[str, Any], ...] = ()
    for event in matching:
        if not isinstance(event, ManualOverride):
            continue
        changes = event.changes
        changed = changes.model_fields_set
        ratings.update(
            {name: getattr(changes, name) for name in _RATING_FIELDS if name in changed}
        )
        if "quality_errors" in changed:
            effective_errors = changes.quality_errors
        if "hard_failure_gates" in changed:
            manual_gates = _overlay_gates(event, automated_gates)
        ratings["derived_from"] = "manual_override"

    gates = (*automated_gates, *manual_gates)
    if gates or ratings.get("hard_failed") is True:
        ratings.update(hard_failed=True, usability="unusable")
    return ReviewOverlay(original, matching, ratings, gates, effective_errors)
