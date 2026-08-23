"""Versioned structural models for offline gmuse evaluation assets."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = "1.0"
SUPPORTED_FORMATS = ("freeform", "conventional", "gitmoji")
SUPPORTED_CONVENTIONAL_TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "test",
    "chore",
)
COVERAGE_DIMENSIONS = (
    "ecosystem",
    "source_repo",
    "origin",
    "source_license",
    "change_type",
    "format",
    "safety_tag",
    "injection_tag",
    "history",
    "branch",
    "hint",
    "max_chars",
)
INJECTION_TAGS = (
    "direct",
    "indirect",
    "obfuscated",
    "encoded",
    "deleted",
    "code-comment",
    "markdown",
    "docs",
    "string-literal",
    "test-fixture",
    "config-example",
)

FormatName = Literal["freeform", "conventional", "gitmoji"]
FixtureOrigin = Literal["real", "adapted", "synthetic"]
RedistributionReview = Literal["not_reviewed", "metadata_only", "approved_for_fixture"]
SuiteKind = Literal["smoke", "core", "safety", "custom"]


class EvalModel(BaseModel):
    """Base model that rejects accidental, unversioned asset fields."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class FixtureFile(EvalModel):
    """A safe, relative file to materialize before applying a fixture patch."""

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
    """A prior synthetic commit used to provide realistic history context."""

    subject: str = Field(min_length=1)
    body: str | None = None
    source_commit_sha: str | None = None


class FixtureProvenance(EvalModel):
    """Origin and attribution metadata for a fixture."""

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
    """Offline data needed to reconstruct and stage one evaluated change."""

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


class EvalRubric(EvalModel):
    """Reviewable expectations for an acceptable generated message."""

    schema_version: str = SCHEMA_VERSION
    id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    required_concepts: list[str]
    forbidden_concepts: list[str]
    allowed_conventional_types: list[str]
    allowed_scopes: list[str]
    example_good: list[str]
    example_bad: list[str]
    quality_notes: str | None = None
    safety_notes: str | None = None


class EvalCase(EvalModel):
    """Bind a fixture and rubric to generation context options."""

    schema_version: str = SCHEMA_VERSION
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


class SuiteCoveragePolicy(EvalModel):
    """Required and advisory coverage rules for a suite."""

    required_dimensions: list[str] = Field(default_factory=list)
    advisory_dimensions: list[str] = Field(default_factory=list)
    minimum_case_counts: dict[str, int] = Field(default_factory=dict)

    @field_validator("minimum_case_counts")
    @classmethod
    def validate_minimums(cls, value: dict[str, int]) -> dict[str, int]:
        """Reject negative policy counts."""
        if any(count < 0 for count in value.values()):
            raise ValueError("minimum case counts must be non-negative")
        return value


class EvalSuite(EvalModel):
    """A named, versioned set of ordered eval case IDs."""

    schema_version: str = SCHEMA_VERSION
    id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    suite_kind: SuiteKind
    case_ids: list[str] = Field(min_length=1)
    coverage_policy: SuiteCoveragePolicy

    @field_validator("case_ids")
    @classmethod
    def validate_unique_case_ids(cls, value: list[str]) -> list[str]:
        """Keep suite membership unambiguous."""
        if len(value) != len(set(value)):
            raise ValueError("suite case IDs must be unique")
        return value


class ValidationIssue(EvalModel):
    """One actionable validation error or warning."""

    code: str = "validation_error"
    message: str = Field(min_length=1)
    path: str | None = None
    asset_id: str | None = None

    def render(self) -> str:
        """Return a compact human-readable issue description."""
        prefix = self.asset_id or self.path
        return f"{prefix}: {self.message}" if prefix else self.message


class CoverageSummary(EvalModel):
    """Deterministically ordered values observed across validated cases."""

    dimensions: dict[str, list[str]] = Field(
        default_factory=lambda: {dimension: [] for dimension in COVERAGE_DIMENSIONS}
    )

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, value: dict[str, list[str]]) -> dict[str, list[str]]:
        """Reject unknown dimensions while preserving declared ordering."""
        unknown = set(value).difference(COVERAGE_DIMENSIONS)
        if unknown:
            raise ValueError(f"unknown coverage dimensions: {sorted(unknown)}")
        return {
            dimension: sorted(set(value.get(dimension, [])))
            for dimension in COVERAGE_DIMENSIONS
        }


class ValidationReport(EvalModel):
    """Structured result shared by the CLI and future eval runners."""

    schema_version: str = Field(min_length=1)
    suite_id: str = Field(min_length=1)
    suite_version: str = Field(min_length=1)
    status: Literal["passed", "failed"]
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    coverage: CoverageSummary = Field(default_factory=CoverageSummary)
    validated_at: datetime
