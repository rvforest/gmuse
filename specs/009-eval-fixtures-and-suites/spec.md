# Feature Specification: Eval Fixtures And Suites

**Feature Branch**: `009-eval-fixtures-and-suites`

**Created**: 2026-06-11

**Status**: Implemented

**Implementation Note**: This specification describes maintainer-only eval
tooling. It does not change the public `gmuse` command workflow.

**Input**: User description: "Create maintainer-only eval fixture and suite foundation for gmuse, split from the broader eval planning notes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate A Smoke Suite Offline (Priority: P1)

As a gmuse maintainer, I want to validate a tiny checked-in smoke suite without
model credentials so that I can prove eval fixture structure and reconstruction
work before any live eval runs exist.

**Why this priority**: All later eval runner, judge, and baseline work depends on
trustworthy fixture and suite data.

**Independent Test**: Run the manual validation command against the smoke suite
and confirm it validates schemas, reconstructs temporary repositories, stages
patches, verifies diff digests, and reports coverage without making provider
calls.

**Acceptance Scenarios**:

1. **Given** a valid smoke suite with a synthetic fixture, **When** the maintainer validates it, **Then** validation succeeds without model credentials and reports fixture, case, format, and safety coverage.
2. **Given** a fixture whose reconstructed staged diff does not match its expected digest, **When** the maintainer validates the suite, **Then** validation fails and identifies the affected fixture and expected versus observed digest.
3. **Given** a real OSS fixture missing required attribution metadata, **When** the maintainer validates the suite, **Then** validation fails before the fixture can be used in eval runs.

---

### User Story 2 - Author Reviewable Fixtures And Rubrics (Priority: P2)

As a gmuse maintainer, I want fixtures and rubrics to be explicit, versioned, and
reviewable so that future eval results can be traced back to stable source
cases and scoring expectations.

**Why this priority**: Real commits, adapted fixtures, and synthetic safety
cases need different provenance and review expectations, but all must be
auditable.

**Independent Test**: Validate representative synthetic, adapted, and real
fixture definitions and confirm each fixture type is accepted only when its
required provenance fields are present.

**Acceptance Scenarios**:

1. **Given** a synthetic fixture with no external source commit, **When** it is validated, **Then** it must be marked synthetic and must not require source repository metadata.
2. **Given** an adapted fixture, **When** it is validated, **Then** it must include adaptation notes that explain what changed from the original source.
3. **Given** a real OSS fixture, **When** it is validated, **Then** it must include repository URL, owner/repo, commit SHA, commit URL, source license expression or license reference, full original commit message, import timestamp, and selection rationale.

---

### User Story 3 - Organize Curated Suites By Intent (Priority: P3)

As a gmuse maintainer, I want suites to identify smoke, core, and safety cases so
that later eval commands can run focused subsets without duplicating fixtures.

**Why this priority**: Suite organization controls later runner behavior and
prevents smoke cases from becoming a separate, inconsistent fixture set.

**Independent Test**: Validate a suite definition where `smoke` is a subset of
`core`, safety-tagged cases are discoverable, and coverage warnings are reported
without failing non-required balance guidelines.

**Acceptance Scenarios**:

1. **Given** a smoke suite that references only core cases, **When** validation runs, **Then** the suite passes the smoke/core relationship check.
2. **Given** a smoke suite that references a case outside core, **When** validation runs, **Then** validation fails with a clear suite membership error.
3. **Given** an imbalanced core suite where balance is advisory, **When** validation runs, **Then** validation emits warnings rather than failing.

### Edge Cases

- Fixture patch data cannot be applied to the temporary repository.
- A fixture applies cleanly but produces a staged diff with different path order,
  line endings, or metadata than expected.
- A case declares a conventional commit type that gmuse does not currently
  validate.
- A suite references a missing case, fixture, rubric, or unsupported format.
- A real OSS fixture includes a short SHA rather than a full commit SHA.
- A safety case includes realistic fake secrets that must be marked as
  nonfunctional test data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The eval foundation MUST define versioned fixture, case, suite, and rubric schemas.
- **FR-002**: Fixtures MUST be offline and self-contained after they are checked in.
- **FR-003**: Fixture validation MUST reconstruct a temporary git repository, stage the evaluated changes, and verify that the staged diff digest matches fixture metadata.
- **FR-004**: Fixtures MUST preserve original changed file paths and MUST NOT pre-truncate diffs.
- **FR-005**: Real OSS fixtures MUST include source repository URL, owner/repo, full commit SHA, commit URL, source license expression or license reference, full original commit message, import timestamp, fixture origin kind, and maintainer selection rationale.
- **FR-006**: Synthetic fixtures MUST be explicitly marked synthetic and MUST NOT require external source commit metadata.
- **FR-007**: Adapted fixtures MUST be explicitly marked adapted and MUST include adaptation notes.
- **FR-008**: Rubrics MUST support required concepts, forbidden concepts, allowed conventional types, optional allowed scopes, example good messages, example bad messages, quality notes, and safety notes.
- **FR-009**: Suite definitions MUST support `smoke`, `core`, and `safety` membership without duplicating fixture content.
- **FR-010**: The smoke suite MUST be validated as a subset of the core suite.
- **FR-011**: Validation MUST check fixture schema validity, rubric schema validity, required provenance metadata, reconstructability, staged diff digest, suite references, supported formats, and compatibility between declared conventional types and gmuse's current validator.
- **FR-012**: Validation MUST report coverage by ecosystem, source repo, origin kind, source license evidence status, change type, format, safety tag, injection sub-tag, history usage, branch usage, hint usage, and `max_chars` usage.
- **FR-013**: Balance issues SHOULD warn by default unless a suite policy marks the balance rule required.
- **FR-014**: Safety fixtures tagged for injection MUST support sub-tags that distinguish direct instructions, indirect/external-content instructions, obfuscated or encoded instructions, deleted instructions, and instruction-like content in code comments, docs, strings, tests, or config examples.
- **FR-015**: Fixture provenance MUST distinguish source licensing from fixture redistribution review status so validation can enforce metadata without claiming legal approval.
- **FR-016**: The foundation MUST NOT make live model calls, judge calls, baseline comparisons, fixture import network calls, or public benchmark recommendations.
- **FR-017**: Default CI MUST NOT require provider credentials or live eval execution for this foundation.

### Key Entities *(include if feature involves data)*

- **EvalFixture**: Offline source data needed to reconstruct a temporary git repository and stage the evaluated patch.
- **EvalCase**: A runnable evaluation case that binds a fixture to formats, context options, and a rubric.
- **EvalSuite**: A named, versioned set of case IDs grouped for smoke, core, or safety execution.
- **EvalRubric**: Reviewable expectations for acceptable messages and disallowed claims.
- **FixtureProvenance**: Attribution and origin metadata for real, adapted, or synthetic fixtures.
- **ValidationReport**: Machine-readable and human-readable validation results for fixtures and suites.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can validate the initial smoke suite in under 30 seconds on a typical development machine without provider credentials.
- **SC-002**: Validation detects 100% of fixtures with missing required real-OSS attribution fields.
- **SC-003**: Validation detects 100% of reconstructed staged diff digest mismatches in the checked-in fixture set.
- **SC-004**: The validation report lists coverage for every required coverage dimension for the checked-in suite.
- **SC-005**: Later eval runner specs can reference fixture, case, suite, and rubric entities without redefining their schemas.

## Assumptions

- Eval fixtures are maintainer-only assets and are not part of the normal `gmuse msg` or `gmuse commit` user workflow.
- The first checked-in smoke suite is intentionally small and may use only synthetic fixtures while real OSS source selection is still being curated.
- Fixture importer automation is deferred; manually authored fixtures are acceptable for proving the schema and validation foundation.
- Validation is manual for this feature and is not a default CI gate.
- Existing gmuse git behavior is the source of truth for staged diff extraction once a fixture is reconstructed.
