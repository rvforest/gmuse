"""Framework-neutral descriptors suitable for later Inspect integration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .validate import ValidatedCase


@dataclass(frozen=True, slots=True)
class ValidatedCaseDescriptor:
    """Stable case metadata consumed by future runner adapters."""

    case_id: str
    case_revision: int
    fixture_id: str
    fixture_revision: int
    rubric_id: str
    rubric_version: str
    expected_staged_diff_sha256: str
    formats: tuple[str, ...]
    history_depth: int | None
    include_branch: bool
    user_hint: str | None
    max_chars: int | None
    tags: tuple[str, ...]

    def to_metadata(self) -> dict[str, Any]:
        """Return JSON-compatible stable metadata for an eval sample."""
        data = asdict(self)
        data["formats"] = list(self.formats)
        data["tags"] = list(self.tags)
        return data


def validated_case_to_descriptor(item: ValidatedCase) -> ValidatedCaseDescriptor:
    """Convert a validated case without importing an Inspect runtime."""
    return ValidatedCaseDescriptor(
        case_id=item.case.id,
        case_revision=item.case.revision,
        fixture_id=item.fixture.id,
        fixture_revision=item.fixture.revision,
        rubric_id=item.rubric.id,
        rubric_version=item.rubric.version,
        expected_staged_diff_sha256=item.fixture.expected_staged_diff_sha256,
        formats=tuple(item.case.formats),
        history_depth=item.case.history_depth,
        include_branch=item.case.include_branch,
        user_hint=item.case.user_hint,
        max_chars=item.case.max_chars,
        tags=tuple(item.case.tags),
    )


def to_inspect_sample(item: ValidatedCase) -> dict[str, Any]:
    """Return plain sample-shaped data for a future Inspect adapter."""
    descriptor = validated_case_to_descriptor(item)
    return {
        "id": descriptor.case_id,
        "input": {
            "fixture_id": descriptor.fixture_id,
            "formats": list(descriptor.formats),
            "history_depth": descriptor.history_depth,
            "include_branch": descriptor.include_branch,
            "user_hint": descriptor.user_hint,
            "max_chars": descriptor.max_chars,
        },
        "metadata": descriptor.to_metadata(),
    }


__all__ = [
    "ValidatedCaseDescriptor",
    "to_inspect_sample",
    "validated_case_to_descriptor",
]
