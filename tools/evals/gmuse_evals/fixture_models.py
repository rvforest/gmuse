"""Models for reconstructable offline evaluation fixtures."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import PurePosixPath

from pydantic import Field, field_validator, model_validator

from .schema import (
    EvalModel,
    FixtureOrigin,
    RedistributionReview,
    validate_schema_version as validate_current_schema,
)


class FixtureFile(EvalModel):
    """A safe file to materialize before applying a fixture patch.

    Relative POSIX paths keep fixture reconstruction portable and contained.

    Example:
        >>> FixtureFile(path="README.md", content="# Example\n")
        FixtureFile(path='README.md', content='# Example\\n', executable=False)
    """

    path: str = Field(min_length=1)
    content: str
    executable: bool = False

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        """Reject absolute paths and paths that escape the repository root."""
        if "\\" in value:
            raise ValueError("fixture paths must use POSIX separators")
        path = PurePosixPath(value)
        if path.is_absolute() or value in {".", ".."} or ".." in path.parts:
            raise ValueError("fixture path must remain inside the repository")
        if any(part == "" for part in path.parts):
            raise ValueError("fixture path must not contain empty components")
        return value


class FixtureHistoryCommit(EvalModel):
    """A prior commit message used to reconstruct style context.

    Explicit history records keep later eval runs reproducible.

    Example:
        >>> FixtureHistoryCommit(subject="docs: explain validation")
        FixtureHistoryCommit(subject='docs: explain validation', body=None, source_commit_sha=None)
    """

    subject: str = Field(min_length=1)
    body: str | None = None
    source_commit_sha: str | None = None


class FixtureProvenance(EvalModel):
    """Origin and attribution metadata for a fixture.

    The record separates source evidence from redistribution review status.

    Example:
        >>> FixtureProvenance(origin="synthetic", synthetic_notes="Fictional data")
        FixtureProvenance(origin='synthetic', ...)
    """

    origin: FixtureOrigin
    source_repository_url: str | None = None
    source_owner_repo: str | None = None
    source_commit_sha: str | None = None
    source_commit_url: str | None = None
    source_license: str | None = None
    source_license_expression: str | None = None
    source_license_url: str | None = None
    redistribution_review: RedistributionReview | None = None
    original_commit_message: str | None = None
    imported_at: datetime | None = None
    adaptation_notes: str | None = None
    synthetic_notes: str | None = None


class EvalFixture(EvalModel):
    """Offline data needed to reconstruct one evaluated change.

    A fixture preserves exact Git evidence so candidate runs remain auditable.

    Example:
        >>> data = {"schema_version": "1.0", "id": "example", ...}
        >>> fixture = EvalFixture.model_validate(data)
    """

    schema_version: str = Field(min_length=1)
    id: str = Field(min_length=1)
    revision: int = Field(gt=0)
    origin: FixtureOrigin
    provenance: FixtureProvenance
    ecosystem: str = Field(min_length=1)
    change_type: str = Field(min_length=1)
    safety_tags: list[str]
    injection_tags: list[str]
    base_files: list[FixtureFile]
    patch: str
    expected_staged_diff_sha256: str
    expected_files_changed: list[str]
    history: list[FixtureHistoryCommit]
    branch_name: str | None = None
    repository_instructions: str | None = None
    selection_rationale: str = Field(min_length=1)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        """Reject fixture documents from unsupported schema revisions."""
        return validate_current_schema(value)

    @field_validator("expected_staged_diff_sha256")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        """Require the canonical SHA-256 representation."""
        if re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
            raise ValueError(
                "expected staged diff digest must be a 64-character SHA-256"
            )
        return value.lower()

    @field_validator("expected_files_changed")
    @classmethod
    def validate_changed_paths(cls, value: list[str]) -> list[str]:
        """Require relative changed paths in deterministic order."""
        for path in value:
            FixtureFile(path=path, content="")
        if value != sorted(value):
            raise ValueError("expected changed paths must be sorted")
        if len(value) != len(set(value)):
            raise ValueError("expected changed paths must be unique")
        return value

    @model_validator(mode="after")
    def validate_provenance_origin(self) -> EvalFixture:
        """Keep the denormalized origin fields consistent."""
        if self.origin != self.provenance.origin:
            raise ValueError("fixture origin must match provenance.origin")
        return self


__all__ = [
    "EvalFixture",
    "FixtureFile",
    "FixtureHistoryCommit",
    "FixtureProvenance",
]
