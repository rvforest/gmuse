# Data Model: Eval Fixtures And Suites

## Entity: `EvalFixture`

Represents offline data needed to reconstruct a temporary git repository and
stage the evaluated change.

**Fields**:

- `id: str`
  - Stable fixture identifier.
- `schema_version: str`
  - Fixture schema version.
- `revision: int`
  - Monotonic fixture revision when fixture content changes.
- `origin: Literal["real", "adapted", "synthetic"]`
  - Fixture source category.
- `provenance: FixtureProvenance`
  - Source and attribution metadata.
- `ecosystem: str`
  - Primary ecosystem or language represented by the fixture.
- `change_type: str`
  - Maintainer-assigned category such as `fix`, `feat`, `docs`, `test`,
    `refactor`, or `chore`.
- `safety_tags: list[str]`
  - Optional tags such as `privacy` or `injection`.
- `injection_tags: list[str]`
  - Optional injection pattern tags for injection safety fixtures.
- `base_files: list[FixtureFile]`
  - Minimal file contents needed before applying the evaluated change.
- `patch: str`
  - Patch data applied to stage the evaluated change.
- `expected_staged_diff_sha256: str`
  - Digest of the staged diff produced by reconstruction.
- `expected_files_changed: list[str]`
  - Original changed file paths expected in the staged diff.
- `history: list[FixtureHistoryCommit]`
  - Optional recent commit subjects used to reconstruct style context.
- `branch_name: str | None`
  - Optional branch name for branch-context cases.
- `repository_instructions: str | None`
  - Optional fixture-level `.gmuse` content.
- `selection_rationale: str`
  - Maintainer explanation for why the fixture belongs in the suite.

**Validation Rules**:

- `id` must be unique across checked-in fixtures.
- `schema_version` must be compatible with the validator.
- `revision` must be positive.
- `patch` must apply to `base_files` in a temporary git repository.
- Reconstructed staged diff digest must equal `expected_staged_diff_sha256`.
- `expected_files_changed` must match the reconstructed staged diff paths.
- Fixtures must not store a pre-truncated diff.
- Safety fixtures containing secret-like values must mark them as fake or
  nonfunctional in safety notes or provenance.
- `injection_tags` must be non-empty when `safety_tags` includes `injection`.

## Entity: `FixtureFile`

Represents a file present before the evaluated patch is applied.

**Fields**:

- `path: str`
- `content: str`
- `executable: bool`

**Validation Rules**:

- Paths must be relative repository paths.
- Paths must not escape the temporary repository root.

## Entity: `FixtureHistoryCommit`

Represents a synthetic history commit used to recreate style context.

**Fields**:

- `subject: str`
- `body: str | None`
- `source_commit_sha: str | None`

**Rules**:

- History must not include the evaluated commit itself.
- History may use synthetic placeholder commits as long as original prior commit
  messages are preserved when derived from a real source.

## Entity: `FixtureProvenance`

Represents source attribution and origin metadata.

**Fields**:

- `origin: Literal["real", "adapted", "synthetic"]`
- `source_repository_url: str | None`
- `source_owner_repo: str | None`
- `source_commit_sha: str | None`
- `source_commit_url: str | None`
- `source_license: str | None`
  - Optional human-readable source license label when available.
- `source_license_expression: str | None`
  - SPDX license expression or `LicenseRef-*` reference when available.
- `source_license_url: str | None`
  - URL or repository path for license evidence when available.
- `redistribution_review: Literal["not_reviewed", "metadata_only", "approved_for_fixture"]`
  - Maintainer review status for checking fixture content into gmuse.
- `original_commit_message: str | None`
- `imported_at: str | None`
- `adaptation_notes: str | None`
- `synthetic_notes: str | None`

**Validation Rules**:

- Real fixtures require repository URL, owner/repo, full commit SHA, commit URL,
  source license evidence, full original commit message, and import timestamp.
- Real fixtures require either `source_license_expression` or
  `source_license_url`; both should be present when practical.
- `redistribution_review` must be present for real and adapted fixtures, and
  validation must not treat metadata presence alone as legal approval.
- Adapted fixtures require all real fixture metadata when derived from a real
  commit plus non-empty adaptation notes.
- Synthetic fixtures require non-empty synthetic notes and must not pretend to
  have a real source commit.

## Entity: `EvalRubric`

Represents reviewable expectations for a case.

**Fields**:

- `id: str`
- `version: str`
- `required_concepts: list[str]`
- `forbidden_concepts: list[str]`
- `allowed_conventional_types: list[str]`
- `allowed_scopes: list[str]`
- `example_good: list[str]`
- `example_bad: list[str]`
- `quality_notes: str | None`
- `safety_notes: str | None`

**Validation Rules**:

- Allowed conventional types must be compatible with gmuse's current supported
  conventional type validation.
- Rubrics must not require exact match to an original source commit message.
- Safety notes are required for privacy or injection-tagged cases.
- Injection safety notes should identify the injection location and pattern,
  such as direct instruction text, indirect external-content text, obfuscated or
  encoded instruction text, deleted instruction text, code comments, Markdown,
  test fixtures, string literals, or config examples.

## Entity: `EvalCase`

Represents a runnable eval case binding fixture data to rubric and context
options.

**Fields**:

- `id: str`
- `revision: int`
- `fixture_id: str`
- `rubric_id: str`
- `formats: list[Literal["freeform", "conventional", "gitmoji"]]`
- `history_depth: int | None`
- `include_branch: bool`
- `user_hint: str | None`
- `max_chars: int | None`
- `tags: list[str]`

**Validation Rules**:

- `fixture_id` and `rubric_id` must resolve.
- `formats` must include only gmuse-supported formats.
- `history_depth`, branch, hint, and `max_chars` settings must be represented in
  validation coverage.

## Entity: `EvalSuite`

Represents a named, versioned set of eval cases.

**Fields**:

- `id: Literal["smoke", "core", "safety"] | str`
- `version: str`
- `case_ids: list[str]`
- `suite_kind: Literal["smoke", "core", "safety", "custom"]`
- `coverage_policy: SuiteCoveragePolicy`

**Validation Rules**:

- `smoke` cases must be a subset of `core`.
- `safety` may include safety-tagged core cases and additional safety cases.
- Missing case references fail validation.
- Balance gaps warn by default unless required by `coverage_policy`.

## Entity: `SuiteCoveragePolicy`

Represents optional required coverage rules for a suite.

**Fields**:

- `required_dimensions: list[str]`
- `advisory_dimensions: list[str]`
- `minimum_case_counts: dict[str, int]`

## Entity: `ValidationReport`

Represents the result of validating fixtures and suites.

**Fields**:

- `schema_version: str`
- `suite_id: str`
- `suite_version: str`
- `status: Literal["passed", "failed"]`
- `errors: list[ValidationIssue]`
- `warnings: list[ValidationIssue]`
- `coverage: CoverageSummary`
- `validated_at: str`

**Rules**:

- Any schema, provenance, reference, reconstructability, or digest error fails
  validation.
- Advisory balance issues are warnings unless the suite policy marks them
  required.

## Relationships

- An `EvalSuite` contains many `EvalCase` records.
- An `EvalCase` references exactly one `EvalFixture` and one `EvalRubric`.
- An `EvalFixture` owns one `FixtureProvenance` record and zero or more history
  commits.
- A `ValidationReport` is produced for a suite validation attempt and includes
  issues from fixtures, rubrics, cases, and suite policies.
