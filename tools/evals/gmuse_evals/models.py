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
INJECTION_PATTERN_TAGS = frozenset(
    {
        "direct",
        "direct-instruction",
        "indirect",
        "indirect-external-content",
        "obfuscated",
        "obfuscated-encoded",
        "encoded",
        "deleted",
        "deleted-instruction",
    }
)
INJECTION_LOCATION_TAGS = frozenset(
    {
        "code-comment",
        "markdown",
        "docs",
        "string-literal",
        "test-fixture",
        "config-example",
    }
)
INJECTION_TAGS = INJECTION_PATTERN_TAGS | INJECTION_LOCATION_TAGS


def _validate_schema_version(value: str) -> str:
    """Require asset documents to use the current schema contract."""
    if value != SCHEMA_VERSION:
        raise ValueError(
            f"unsupported schema_version {value!r}; expected {SCHEMA_VERSION!r}"
        )
    return value


FormatName = Literal["freeform", "conventional", "gitmoji"]
FixtureOrigin = Literal["real", "adapted", "synthetic"]
RedistributionReview = Literal["not_reviewed", "metadata_only", "approved_for_fixture"]
SuiteKind = Literal["smoke", "core", "safety", "custom"]


class EvalModel(BaseModel):
    """Base model that rejects accidental, unversioned asset fields.

    Strict shared configuration prevents silent schema drift across asset kinds.

    Example:
        >>> class Record(EvalModel):
        ...     id: str
        >>> Record.model_validate({"id": "one", "extra": True})
        Traceback (most recent call last):
        ...
        pydantic_core._pydantic_core.ValidationError: ...
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


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
        return _validate_schema_version(value)

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
    """Reviewable expectations for an acceptable generated message.

    Rubrics keep scoring intent versioned independently from fixture content.

    Example:
        >>> rubric = EvalRubric(id="docs", version="1.0", ...)
        >>> rubric.allowed_conventional_types
        ['docs']
    """

    schema_version: str = Field(default=SCHEMA_VERSION, validate_default=True)
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

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        """Reject rubric documents from unsupported schema revisions."""
        return _validate_schema_version(value)


class EvalCase(EvalModel):
    """Bind a fixture and rubric to generation context options.

    Cases avoid duplicating fixture content across formats and context settings.

    Example:
        >>> case = EvalCase(id="docs", fixture_id="fixture", rubric_id="rubric", ...)
        >>> case.formats
        ['freeform']
    """

    schema_version: str = Field(default=SCHEMA_VERSION, validate_default=True)
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
        return _validate_schema_version(value)


class SuiteCoveragePolicy(EvalModel):
    """Required and advisory coverage rules for a suite.

    Policies let small suites warn while mature suites enforce balance.

    Example:
        >>> SuiteCoveragePolicy(advisory_dimensions=["format"])
        SuiteCoveragePolicy(required_dimensions=[], advisory_dimensions=['format'], minimum_case_counts={})
    """

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
    """A named, versioned set of ordered eval case IDs.

    Stable suite membership makes focused smoke, core, and safety runs reusable.

    Example:
        >>> suite = EvalSuite(id="smoke", version="1.0", suite_kind="smoke", ...)
        >>> suite.id
        'smoke'
    """

    schema_version: str = Field(default=SCHEMA_VERSION, validate_default=True)
    id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    suite_kind: SuiteKind
    case_ids: list[str] = Field(min_length=1)
    coverage_policy: SuiteCoveragePolicy

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        """Reject suite documents from unsupported schema revisions."""
        return _validate_schema_version(value)

    @field_validator("case_ids")
    @classmethod
    def validate_unique_case_ids(cls, value: list[str]) -> list[str]:
        """Keep suite membership unambiguous."""
        if len(value) != len(set(value)):
            raise ValueError("suite case IDs must be unique")
        return value


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


class CoverageSummary(EvalModel):
    """Deterministically ordered coverage observed across validated cases.

    A fixed dimension order makes reports stable and straightforward to compare.

    Example:
        >>> summary = CoverageSummary()
        >>> list(summary.dimensions)[0]
        'ecosystem'
    """

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
    """Structured result shared by the CLI and future eval runners.

    The report prevents downstream tools from having to parse CLI text.

    Example:
        >>> report = ValidationReport(...)
        >>> report.status in {"passed", "failed"}
        True
    """

    schema_version: str = Field(min_length=1)
    suite_id: str = Field(min_length=1)
    suite_version: str = Field(min_length=1)
    status: Literal["passed", "failed"]
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    coverage: CoverageSummary = Field(default_factory=CoverageSummary)
    validated_at: datetime
