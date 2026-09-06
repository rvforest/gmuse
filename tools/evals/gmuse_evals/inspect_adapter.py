"""Framework-neutral descriptors suitable for later Inspect integration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from pydantic import BaseModel

from .results import ResolvedCase


@dataclass(frozen=True, slots=True)
class EvalCaseDescriptor:
    """Stable case metadata consumed by future runner adapters.

    A framework-neutral descriptor prevents the fixture foundation from taking
    a runtime dependency on Inspect AI.

    Attributes:
        case_id: Stable case ID.
        case_revision: Monotonic case revision.
        fixture_id: Stable fixture ID.
        fixture_revision: Monotonic fixture revision.
        rubric_id: Stable rubric ID.
        rubric_revision: Monotonic rubric revision.
        rubric_digest: Digest of the canonical rubric asset.
        scoring_profile_id: Stable scoring-profile ID, when present.
        scoring_profile_revision: Monotonic scoring-profile revision.
        scoring_profile_digest: Digest of the canonical profile asset.
        expected_staged_diff_sha256: Validated staged-diff digest.
        formats: Supported generation formats.
        history_depth: Requested history depth or the product default marker.
        include_branch: Whether branch context is enabled.
        user_hint: Optional user hint.
        max_chars: Optional message length limit.
        tags: Case classification tags.

    Example:
        >>> descriptor = resolved_case_to_descriptor(resolved_case)
        >>> descriptor.to_metadata()["case_id"] == descriptor.case_id
        True
    """

    case_id: str
    case_revision: int
    fixture_id: str
    fixture_revision: int
    rubric_id: str
    rubric_revision: int
    expected_staged_diff_sha256: str
    formats: tuple[str, ...]
    history_depth: int | None
    include_branch: bool
    user_hint: str | None
    max_chars: int | None
    tags: tuple[str, ...]
    rubric_digest: str
    scoring_profile_id: str
    scoring_profile_revision: int
    scoring_profile_digest: str

    def to_metadata(self) -> dict[str, Any]:
        """Return JSON-compatible stable metadata for an eval sample.

        Returns:
            A new dictionary with tuple fields converted to lists.

        Example:
            >>> descriptor.to_metadata()["formats"]
            ['freeform']
        """
        data = asdict(self)
        data["formats"] = list(self.formats)
        data["tags"] = list(self.tags)
        return data


def resolved_case_to_descriptor(item: ResolvedCase) -> EvalCaseDescriptor:
    """Convert a resolved case without importing an Inspect runtime.

    Args:
        item: A case whose source-asset references were resolved.

    Returns:
        Stable framework-neutral case metadata.

    Example:
        >>> resolved_case_to_descriptor(item).case_id == item.case.id
        True
    """
    profile = item.scoring_profile
    return EvalCaseDescriptor(
        case_id=item.case.id,
        case_revision=item.case.revision,
        fixture_id=item.fixture.id,
        fixture_revision=item.fixture.revision,
        rubric_id=item.rubric.id,
        rubric_revision=item.rubric.revision,
        expected_staged_diff_sha256=item.fixture.expected_staged_diff_sha256,
        formats=tuple(item.case.formats),
        history_depth=item.case.history_depth,
        include_branch=item.case.include_branch,
        user_hint=item.case.user_hint,
        max_chars=item.case.max_chars,
        tags=tuple(item.case.tags),
        rubric_digest=stable_asset_digest(item.rubric),
        scoring_profile_id=profile.id,
        scoring_profile_revision=profile.revision,
        scoring_profile_digest=stable_asset_digest(profile),
    )


def stable_asset_digest(asset: BaseModel) -> str:
    """Hash a model's canonical JSON representation.

    Args:
        asset: A validated profile or rubric model.

    Returns:
        Lowercase SHA-256 digest of sorted, compact JSON.

    Example:
        >>> class Asset(BaseModel):
        ...     value: str
        >>> len(stable_asset_digest(Asset(value="one")))
        64
    """
    payload = json.dumps(
        asset.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def to_inspect_sample(item: ResolvedCase) -> dict[str, Any]:
    """Return plain sample-shaped data for a future Inspect adapter.

    Args:
        item: A case whose source-asset references were resolved.

    Returns:
        JSON-compatible sample-shaped input and metadata.

    Example:
        >>> to_inspect_sample(item)["id"] == item.case.id
        True
    """
    descriptor = resolved_case_to_descriptor(item)
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
    "EvalCaseDescriptor",
    "stable_asset_digest",
    "to_inspect_sample",
    "resolved_case_to_descriptor",
]
