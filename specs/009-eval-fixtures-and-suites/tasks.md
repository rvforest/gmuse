# Tasks: Eval Fixtures And Suites

**Input**: Design documents from `/specs/009-eval-fixtures-and-suites/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/fixture-schema.md`, `contracts/suite-schema.md`, `contracts/validation-cli.md`, `quickstart.md`

**Tests**: Required. The feature plan, specification, and constitution require unit tests for structural/domain validation, integration tests for temporary Git reconstruction and CLI behavior, validation of checked-in smoke assets, and test-first coverage for critical Git and validation paths.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently once the shared foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it targets different files and has no dependency on an incomplete task
- **[Story]**: User story label (`[US1]`, `[US2]`, or `[US3]`)
- Every task includes exact repository file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add maintainer-only dependencies and establish the eval tool package without changing the public `gmuse` CLI.

- [X] T001 Add explicit Pydantic v2 and `license-expression` development dependencies, include `tools` in static type checking, and regenerate the lockfile in pyproject.toml and uv.lock
- [X] T002 [P] Create the maintainer module entrypoint and package scaffolding in tools/__init__.py, tools/evals/__init__.py, tools/evals/gmuse_evals/__init__.py, and tools/evals/gmuse_evals/__main__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define the versioned data model, TOML loading boundary, and structured validation result types shared by all stories.

**⚠️ CRITICAL**: No user story implementation should begin until this phase is complete.

> **NOTE**: Write T003 and T004 first and confirm they fail before implementing T005-T007.

- [X] T003 [P] Add failing unit tests for fixture, provenance, rubric, case, suite, coverage-policy, and validation-report structural constraints in tests/unit/test_eval_foundation_models.py
- [X] T004 [P] Add failing unit tests for TOML parsing, deterministic asset discovery, duplicate IDs, malformed documents, and missing asset paths in tests/unit/test_eval_foundation_load.py
- [X] T005 Implement fully typed Pydantic models, schema versions, origin-specific optional fields, path-safe FixtureFile records, and structured issue/report types in tools/evals/gmuse_evals/models.py
- [X] T006 Implement deterministic TOML discovery, parsing, model construction, ID indexing, and actionable load errors in tools/evals/gmuse_evals/load.py
- [X] T007 Implement the shared validated-suite result container, error/warning aggregation, and validator orchestration boundary in tools/evals/gmuse_evals/validate.py and export reusable helpers from tools/evals/gmuse_evals/__init__.py

**Checkpoint**: Versioned models and structured loading/reporting helpers are ready for story-specific behavior.

---

## Phase 3: User Story 1 - Validate A Smoke Suite Offline (Priority: P1) 🎯 MVP

**Goal**: Let a maintainer validate a tiny checked-in smoke suite offline by reconstructing temporary repositories, staging changes, verifying exact diff digests and paths, and receiving actionable human-readable results.

**Independent Test**: Run `uv run python -m tools.evals.gmuse_evals validate --suite smoke` without provider credentials and confirm schema loading, repository reconstruction, staged diff verification, coverage reporting, and the under-30-second target all succeed.

### Tests for User Story 1 ⚠️

> **NOTE**: Write these tests first and confirm they fail before implementation.

- [X] T008 [P] [US1] Add integration tests for deterministic repository initialization, base files, executable modes, synthetic history commits, branch checkout, repository instructions, patch failures, staged paths, and SHA-256 digests in tests/integration/test_eval_foundation_reconstruction.py
- [X] T009 [P] [US1] Add unit tests for successful validation, aggregated schema/reference errors, patch failures, changed-path mismatches, and expected-versus-observed digest diagnostics in tests/unit/test_eval_foundation_validation.py
- [X] T010 [P] [US1] Add CLI contract tests for default options, `--suite`, `--evals-dir`, success output, aggregated failure output, exit codes, and absence of model/network calls in tests/integration/test_eval_foundation_cli.py
- [X] T011 [P] [US1] Add a failing checked-in smoke-suite test for offline execution, provider-credential independence, complete validation stages, and the under-30-second target in tests/integration/test_eval_foundation_smoke.py

### Implementation for User Story 1

- [X] T012 [US1] Implement deterministic temporary Git reconstruction, safe base-file materialization, synthetic history commits, branch/instruction setup, patch application, staging, and production-fidelity `gmuse.git.get_staged_diff` extraction in tools/evals/gmuse_evals/git_reconstruct.py
- [X] T013 [US1] Implement fixture/case/rubric reference resolution plus reconstructability, changed-path, and staged-diff digest validation with expected/observed diagnostics in tools/evals/gmuse_evals/validate.py
- [X] T014 [US1] Implement coverage collection for ecosystem, source repository, origin, license evidence, change type, format, safety/injection tags, history, branch, hint, and `max_chars` usage in tools/evals/gmuse_evals/validate.py
- [X] T015 [P] [US1] Author the ordinary synthetic history fixture with deterministic base files, patch, expected paths, and staged-diff digest in evals/fixtures/synthetic-docs-history.toml
- [X] T016 [P] [US1] Author the synthetic injection fixture with nonfunctional safety content, injection sub-tags, deterministic patch, expected paths, and staged-diff digest in evals/fixtures/synthetic-injection-comment.toml
- [X] T017 [P] [US1] Author reviewable quality and injection-safety expectations for the smoke fixtures in evals/rubrics/docs-history.toml and evals/rubrics/injection-safety.toml
- [X] T018 [US1] Bind the two smoke fixtures to formats, rubrics, history, branch, hint, and `max_chars` options in evals/cases/docs-history.toml and evals/cases/injection-comment.toml
- [X] T019 [P] [US1] Implement the Typer `validate` command as a thin presentation layer with success/failure rendering and no public `gmuse` registration in tools/evals/gmuse_evals/cli.py and tools/evals/gmuse_evals/__main__.py
- [X] T020 [US1] Define the initial two-case smoke suite and make the checked-in smoke test pass in evals/suites/smoke.toml and tests/integration/test_eval_foundation_smoke.py

**Checkpoint**: The smoke suite validates end-to-end without credentials, network access, model calls, or judge calls.

---

## Phase 4: User Story 2 - Author Reviewable Fixtures And Rubrics (Priority: P2)

**Goal**: Enforce explicit, versioned fixture provenance and rubric expectations for synthetic, adapted, and real OSS source material.

**Independent Test**: Validate representative temporary synthetic, adapted, and real fixture documents and confirm each origin is accepted only with its required provenance, license evidence, redistribution-review status, and safety metadata.

### Tests for User Story 2 ⚠️

> **NOTE**: Write these tests first and confirm they fail before implementation.

- [X] T021 [P] [US2] Add table-driven provenance tests for synthetic, adapted, and real origins, full SHA requirements, source URLs, license expressions/references, redistribution review, timestamps, original messages, adaptation notes, and synthetic notes in tests/unit/test_eval_foundation_provenance.py
- [X] T022 [P] [US2] Add rubric and safety tests for required/forbidden concepts, gmuse-compatible conventional types, optional scopes, examples, quality notes, fake-secret marking, and injection location/sub-tags in tests/unit/test_eval_foundation_rubrics.py
- [X] T023 [P] [US2] Add representative temporary TOML integration tests proving valid and invalid synthetic, adapted, and real documents flow through the loader and validator in tests/integration/test_eval_foundation_provenance.py

### Implementation for User Story 2

- [X] T024 [US2] Implement origin-specific provenance, full-SHA, timestamp, source-license evidence, SPDX/LicenseRef parsing, redistribution-review, adaptation-note, and synthetic-note validation in tools/evals/gmuse_evals/validate.py
- [X] T025 [US2] Implement fixture path containment, expected-path preservation, injection-tag completeness, and nonfunctional secret-like test-data validation in tools/evals/gmuse_evals/validate.py
- [X] T026 [US2] Implement rubric semantic validation and compatibility checks against the conventional commit types accepted by `gmuse.prompts.validate_message` in tools/evals/gmuse_evals/validate.py

**Checkpoint**: Fixture and rubric reviews are auditable, origin-aware, safety-aware, and explicit that metadata validation is not legal approval.

---

## Phase 5: User Story 3 - Organize Curated Suites By Intent (Priority: P3)

**Goal**: Support smoke, core, safety, and custom suite intent with reference validation, smoke-as-core-subset enforcement, complete coverage summaries, and advisory-versus-required balance policy.

**Independent Test**: Validate temporary suite definitions where smoke is a subset of core, an out-of-core smoke case fails clearly, missing/duplicate references fail, safety cases are discoverable, advisory gaps warn, and strict or required balance gaps fail.

### Tests for User Story 3 ⚠️

> **NOTE**: Write these tests first and confirm they fail before implementation.

- [X] T027 [P] [US3] Add suite tests for missing and duplicate case IDs, unsupported formats, suite kinds, smoke/core subset success and failure, and safety-case discovery in tests/unit/test_eval_foundation_suites.py
- [X] T028 [P] [US3] Add coverage-policy tests for every required dimension, advisory warnings, required minimum failures, and deterministic coverage ordering in tests/unit/test_eval_foundation_coverage.py
- [X] T029 [P] [US3] Add CLI integration tests for default advisory behavior and `--strict-balance` promotion of warnings to failures in tests/integration/test_eval_foundation_cli.py

### Implementation for User Story 3

- [X] T030 [US3] Implement suite/case/fixture/rubric reference checks, duplicate detection, supported-format validation, safety discovery, and smoke/core subset enforcement in tools/evals/gmuse_evals/validate.py
- [X] T031 [US3] Implement required/advisory coverage-policy evaluation, minimum counts, deterministic warnings, and strict-balance promotion in tools/evals/gmuse_evals/validate.py
- [X] T032 [US3] Wire `--strict-balance` through the Typer contract and render actionable policy warnings/errors in tools/evals/gmuse_evals/cli.py
- [X] T033 [US3] Define the curated core suite as a superset of the checked-in smoke cases with explicit coverage policy in evals/suites/core.toml and finalize subset policy in evals/suites/smoke.toml
- [X] T034 [US3] Add checked-in smoke/core membership, reference, coverage, and strict-balance integration coverage in tests/integration/test_eval_foundation_suites.py

**Checkpoint**: Maintainers can select suites by intent without duplicating fixture content, and coverage gaps have predictable warning/failure semantics.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Preserve downstream reuse, align maintainer documentation, and run all repository quality gates.

- [X] T035 [P] Add compatibility tests for stable IDs, revisions, digests, rubric metadata, and framework-neutral validated-case descriptors in tests/unit/test_eval_foundation_inspect_adapter.py
- [X] T036 Implement the structured validated-case adapter for downstream Inspect-based runner work without adding an Inspect runtime dependency in tools/evals/gmuse_evals/inspect_adapter.py
- [X] T037 [P] Update the maintainer validation walkthrough, failure examples, and offline/non-goal boundaries in specs/009-eval-fixtures-and-suites/quickstart.md and docs/source/development/contributing.md
- [X] T038 Run and verify every smoke, provenance-failure, and digest-failure scenario in specs/009-eval-fixtures-and-suites/quickstart.md against evals/suites/smoke.toml
- [X] T039 Run `uv run nox -s test`, `uv run nox -s lint`, `uv run nox -s format`, and `uv run nox -s types` using noxfile.py and pyproject.toml, and confirm .github/workflows/run-checks.yaml adds no provider credentials or live eval execution

---

## Phase 7: User Story 1 Review Remediation - Deterministic, Observable Offline Validation (Priority: P1) 🎯 MVP

**Goal**: Close review gaps in the smoke-validation path so its CLI visibly
reports every required coverage dimension, reconstruction is independent of
maintainer Git configuration, and reconstructed history contains only history
declared by the fixture.

**Independent Test**: Run the smoke command with a temporary global Git config
that enables `diff.noprefix`, mnemonic prefixes, forced color, and a non-default
diff context; confirm the command still passes with the checked-in digests,
prints all twelve coverage dimensions in deterministic order, and exposes no
internal bootstrap commit through production history extraction.

### Tests for User Story 1 Review Remediation ⚠️

> **NOTE**: Write these tests first and confirm they fail before implementation.

- [X] T040 [P] [US1] Add CLI success-output assertions for a `Coverage:` section containing every key in `COVERAGE_DIMENSIONS`, deterministic sorted values, and the existing case/fixture/warning counts in tests/integration/test_eval_foundation_cli.py
- [X] T041 [P] [US1] Add a reconstruction regression test that points `GIT_CONFIG_GLOBAL` at a temporary config enabling `diff.noprefix`, `diff.mnemonicPrefix`, forced diff color, non-default diff context/algorithm, and `core.quotePath`; use multiline ambiguous content plus a non-ASCII path so the uncontrolled settings would alter output, then assert raw diff text, changed paths, and SHA-256 match an uncontaminated reconstruction in tests/integration/test_eval_foundation_reconstruction.py
- [X] T042 [P] [US1] Add production-history fidelity tests asserting `gmuse.git.get_commit_history(path=...)` returns fixture-declared subjects in declared newest-first order and never returns `fixture: establish base` within any validated case depth in tests/integration/test_eval_foundation_reconstruction.py
- [X] T043 [P] [US1] Add case/fixture compatibility and coverage tests proving `history_depth = 0` reports `not-used`, positive depth reports `used`, `null` resolves gmuse's current default depth, and a resolved depth larger than declared fixture history fails validation before reconstruction in tests/unit/test_eval_foundation_coverage.py and tests/unit/test_eval_foundation_validation.py

### Implementation for User Story 1 Review Remediation

- [X] T044 [US1] Make temporary repositories override all digest-affecting user/global Git settings exercised by T041 while retaining `gmuse.git.get_staged_diff(path=...)` as the extraction path in tools/evals/gmuse_evals/git_reconstruct.py (depends on T041)
- [X] T045 [US1] Reconstruct declared history so every commit visible to production history extraction corresponds to a fixture history record, resolve `history_depth = null` through gmuse's default, reject cases that request more history than the fixture declares, and report resolved usage accurately in tools/evals/gmuse_evals/git_reconstruct.py and tools/evals/gmuse_evals/validate.py (depends on T042, T043)
- [X] T046 [US1] Render `ValidationReport.coverage.dimensions` in `COVERAGE_DIMENSIONS` order with sorted values and stable human-readable labels in tools/evals/gmuse_evals/cli.py (depends on T040)

**Checkpoint**: The smoke command has deterministic output and digests under
supported Git environments, and its visible coverage/history claims match the
repository state later runner work will consume.

---

## Phase 8: User Story 2 Review Remediation - Strict Schemas, Provenance, And Safety Metadata (Priority: P2)

**Goal**: Prevent schema/provenance false positives and false negatives by
rejecting unsupported schema versions, accepting the complete SPDX catalog,
validating source URLs, and requiring both an injection pattern and location.

**Independent Test**: Validate temporary real and injection fixtures showing
that supported schema `1.0`, valid SPDX identifiers/expressions/exceptions, and
well-formed source URLs pass; unknown schema versions, malformed URLs, invalid
license expressions, or injection tags missing either category fail with
field-specific issues.

### Tests for User Story 2 Review Remediation ⚠️

> **NOTE**: Write these tests first and confirm they fail before implementation.

- [X] T047 [P] [US2] Add table-driven model/loader tests proving fixture, rubric, case, and suite documents accept only `SCHEMA_VERSION`, reject future/unknown declared versions such as `999.0`, and preserve current contract defaults where the schema contract permits omission in tests/unit/test_eval_foundation_models.py and tests/unit/test_eval_foundation_load.py
- [X] T048 [P] [US2] Add provenance tests accepting valid SPDX examples outside the current allowlist (`0BSD`, `Python-2.0`, and an expression using `WITH Classpath-exception-2.0`), retaining `LicenseRef-*` support, rejecting malformed expressions, and rejecting non-absolute or non-HTTP(S) repository/commit URLs in tests/unit/test_eval_foundation_provenance.py and tests/integration/test_eval_foundation_provenance.py
- [X] T049 [P] [US2] Add injection taxonomy tests showing a pattern-only tag list and a location-only tag list each fail, while every supported pattern family paired with a supported code/docs/string/test/config location passes in tests/unit/test_eval_foundation_rubrics.py

### Implementation for User Story 2 Review Remediation

- [X] T050 [US2] Constrain every declared `schema_version` to the validator's `SCHEMA_VERSION` without conflating document schema versions with fixture revisions or rubric/suite versions in tools/evals/gmuse_evals/models.py (depends on T047)
- [X] T051 [US2] Replace the hand-maintained SPDX symbol allowlist with `license-expression`'s complete SPDX licensing data, preserve valid `LicenseRef-*` expressions, and validate `source_repository_url` plus `source_commit_url` as absolute HTTP(S) URLs while retaining the documented repository-path option for `source_license_url` in tools/evals/gmuse_evals/models.py and tools/evals/gmuse_evals/validate.py (depends on T048)
- [X] T052 [US2] Define non-overlapping injection-pattern and injection-location tag sets once in tools/evals/gmuse_evals/models.py and require at least one recognized tag from each set for every injection fixture in tools/evals/gmuse_evals/validate.py (depends on T049)

**Checkpoint**: Reviewable assets cannot silently opt into an unknown schema,
valid SPDX evidence is not rejected by a local subset, and injection coverage
always records both attack pattern and content location.

---

## Phase 9: User Story 3 Review Remediation - Suite-Scoped Asset Loading (Priority: P3)

**Goal**: Preserve global asset discovery and duplicate-ID diagnostics while
ensuring validation of one suite model-validates only that suite's transitive
case, fixture, rubric, and smoke/core relationship records.

**Independent Test**: Place a parseable, ID-bearing but schema-invalid asset
outside the selected suite graph and confirm smoke validation passes; reference
that same asset and confirm validation fails with its path and ID. Duplicate IDs,
malformed requested documents, missing references, and smoke/core violations
must remain failures.

### Tests for User Story 3 Review Remediation ⚠️

- [X] T053 [P] [US3] Add loader unit tests for a two-stage raw-ID index plus requested-graph model validation, covering an unreferenced parseable ID-bearing schema-invalid document, the same document when referenced, duplicate IDs, and a parseable ID-bearing selected document missing required structural fields in tests/unit/test_eval_foundation_load.py
- [X] T054 [P] [US3] Add CLI integration coverage proving `--suite smoke` ignores schema-invalid assets outside its transitive graph but still validates the `core` membership record and fails when the invalid asset becomes referenced in tests/integration/test_eval_foundation_cli.py

### Implementation for User Story 3 Review Remediation

- [X] T055 [US3] Refactor suite loading into deterministic raw TOML discovery/ID indexing followed by Pydantic construction of the requested suite graph, retain `load_assets()` as the explicit full-catalog validation API, and make `load_suite_assets()` include the core suite data needed for smoke-subset checks in tools/evals/gmuse_evals/load.py and tools/evals/gmuse_evals/validate.py (depends on T053, T054)

**Checkpoint**: A focused suite remains independently runnable without hiding
errors in assets it actually references or weakening global catalog validation.

---

## Phase 10: Review Remediation Polish & Merge Gates

**Purpose**: Align maintainer documentation with the corrected contracts,
restore repository formatting, and prove all remediation through the required
quality gates.

- [X] T056 [P] Update the coverage-output example, deterministic Git-environment behavior, schema-version rejection, complete SPDX validation, injection pattern/location rule, and suite-scoped loading semantics in specs/009-eval-fixtures-and-suites/contracts/validation-cli.md, specs/009-eval-fixtures-and-suites/contracts/fixture-schema.md, specs/009-eval-fixtures-and-suites/quickstart.md, and docs/source/development/contributing.md
- [X] T057 Run `uv run nox -s format`, review and retain Ruff formatting for all touched Python files, and specifically resolve the pre-existing review failures in tests/integration/test_eval_foundation_cli.py, tests/integration/test_eval_foundation_provenance.py, tests/integration/test_eval_foundation_reconstruction.py, tests/unit/test_eval_foundation_coverage.py, tests/unit/test_eval_foundation_load.py, tests/unit/test_eval_foundation_rubrics.py, and tests/unit/test_eval_foundation_validation.py
- [X] T058 Run `uv run nox -s test`, `uv run nox -s lint`, `uv run nox -s format`, and `uv run nox -s types`; then run the checked-in smoke/core CLI commands normally and with the adversarial temporary global Git config from T041, confirming under-30-second offline execution, identical digests, visible complete coverage, zero provider credentials, and no live/network calls

**Checkpoint**: All review findings are covered by regression tests, documented,
formatted, and verified through the repository's merge gates.

---

## Phase 11: Holistic Review Remediation

**Purpose**: Close the remaining security, validation-integrity, structured-error,
documentation, and specification-metadata findings from the holistic branch review.

- [X] T059 [P] Add failing regressions for complete Git environment isolation,
  license-reference validation, orphan injection tags, aggregated selected-graph
  errors, and non-duplicated advisory policy issues in
  tests/integration/test_eval_foundation_reconstruction.py,
  tests/unit/test_eval_foundation_provenance.py,
  tests/unit/test_eval_foundation_rubrics.py,
  tests/unit/test_eval_foundation_load.py, and
  tests/unit/test_eval_foundation_coverage.py
- [X] T060 [US1] Isolate reconstruction from inherited Git configuration and
  Git-specific environment variables, add subprocess timeouts, and pass the
  sanitized environment through production staged-diff extraction in
  src/gmuse/git.py and tools/evals/gmuse_evals/git_reconstruct.py
- [X] T061 [US2] Validate source license URL-or-repository-path evidence and
  reject injection sub-tags without an explicit injection safety tag in
  tools/evals/gmuse_evals/validate.py
- [X] T062 [US3] Preserve structured, aggregated issues while loading a selected
  suite graph and remove duplicate advisory policy reporting in
  tools/evals/gmuse_evals/load.py and tools/evals/gmuse_evals/validate.py
- [X] T063 Add constitution-compliant Google-style documentation, rationale,
  and examples for exported eval foundation APIs in tools/evals/gmuse_evals/
- [X] T064 Align promoted feature status/path metadata and document the hardened
  validation contracts in specs/009-eval-fixtures-and-suites/ and
  docs/source/development/contributing.md
- [X] T065 Run focused regressions, the checked-in smoke/core commands, the full
  Python 3.10 suite, lint, format, types, pre-commit checks, and docs

**Checkpoint**: The reviewed branch is deterministic and offline under hostile
Git configuration, rejects misleading provenance/safety metadata, aggregates
selected-graph failures, and satisfies the project constitution.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** — no dependencies
- **Phase 2: Foundational** — depends on Phase 1 and blocks all user stories
- **Phase 3: US1** — depends on Phase 2 and delivers the MVP
- **Phase 4: US2** — depends on Phase 2; its temporary origin/rubric cases are independently testable
- **Phase 5: US3** — depends on Phase 2; T033-T034 additionally depend on US1's checked-in cases and smoke suite
- **Phase 6: Polish** — depends on all selected user stories
- **Phase 7: US1 review remediation** — starts from the completed foundation; T040-T043 can be written in parallel, then T044-T046 follow their named test dependencies
- **Phase 8: US2 review remediation** — starts from the completed foundation and can proceed alongside Phase 7 at the test level; T050-T052 follow T047-T049 respectively
- **Phase 9: US3 review remediation** — depends on T050's schema-version behavior so requested-graph loading can distinguish unsupported documents consistently; T053-T054 precede T055
- **Phase 10: Review remediation polish** — depends on T044-T046, T050-T052, and T055; documentation may start once the corrected behavior is settled, formatting precedes T058

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational with no dependency on another story and delivers offline smoke validation
- **US2 (P2)**: Starts after Foundational and can be completed with temporary fixtures independently of US1; the final checked-in injection fixture benefits from its safety validation
- **US3 (P3)**: Starts after Foundational for suite-policy logic; checked-in smoke/core integration depends on US1's fixture, rubric, and case assets
- **US1 review remediation**: Independently verified by the smoke CLI under adversarial global Git configuration, complete visible coverage, and exact production history extraction
- **US2 review remediation**: Independently verified with temporary schema, real-provenance, SPDX, URL, and injection-taxonomy documents without reconstruction or provider access
- **US3 review remediation**: Depends on supported-schema enforcement from T050, then independently verifies selected-suite graph loading with referenced and unreferenced invalid assets

### Within Each User Story

- Tests must be written first and confirmed failing before implementation
- Structural loading must precede domain validation
- Repository reconstruction must precede digest generation for checked-in fixtures
- Fixture and rubric assets must exist before cases; cases must exist before suites
- Core logic must return structured results before CLI rendering is finalized
- Review-remediation tests T040-T043, T047-T049, and T053-T054 must fail for the reviewed behavior before their paired implementation tasks begin
- Do not update checked-in staged-diff digests merely to accommodate inherited Git configuration; T044 must make reconstruction deterministic and existing digests may change only after an intentional raw-diff review
- T058 is the merge gate and cannot begin until implementation, documentation, and formatting remediation are complete

---

## Parallel Opportunities

- **Setup**: T002 can proceed independently while T001 updates dependency and type-check configuration
- **Foundational**: T003 and T004 can run in parallel before T005-T007
- **US1**: T008-T011 can run in parallel; T015-T017 can run in parallel after reconstruction is available; T019 can proceed alongside asset authoring after T013
- **US2**: T021-T023 can run in parallel before T024-T026
- **US3**: T027-T029 can run in parallel before T030-T032
- **Polish**: T035 and T037 can run in parallel before T036 and final validation
- **US1 review remediation**: T040-T043 target separate CLI, reconstruction, and coverage/validation test paths and can be authored in parallel; T044 and T046 edit separate implementation modules
- **US2 review remediation**: T047-T049 cover distinct schema, provenance, and safety concerns and can be authored in parallel before T050-T052
- **US3 review remediation**: T053 and T054 can be authored in parallel before the shared loader implementation in T055
- **Review remediation polish**: T056 can proceed while implementation tests stabilize; T057-T058 remain sequential merge-gate work

## Parallel Example: User Story 1

```text
Task: "T008 Add reconstruction integration tests in tests/integration/test_eval_foundation_reconstruction.py"
Task: "T009 Add validation unit tests in tests/unit/test_eval_foundation_validation.py"
Task: "T010 Add CLI contract tests in tests/integration/test_eval_foundation_cli.py"
Task: "T011 Add the checked-in smoke test in tests/integration/test_eval_foundation_smoke.py"

After T012-T014:
Task: "T015 Author evals/fixtures/synthetic-docs-history.toml"
Task: "T016 Author evals/fixtures/synthetic-injection-comment.toml"
Task: "T017 Author evals/rubrics/docs-history.toml and evals/rubrics/injection-safety.toml"
```

## Parallel Example: User Story 2

```text
Task: "T021 Add provenance tests in tests/unit/test_eval_foundation_provenance.py"
Task: "T022 Add rubric and safety tests in tests/unit/test_eval_foundation_rubrics.py"
Task: "T023 Add provenance integration tests in tests/integration/test_eval_foundation_provenance.py"
```

## Parallel Example: User Story 3

```text
Task: "T027 Add suite membership tests in tests/unit/test_eval_foundation_suites.py"
Task: "T028 Add coverage policy tests in tests/unit/test_eval_foundation_coverage.py"
Task: "T029 Add strict-balance CLI tests in tests/integration/test_eval_foundation_cli.py"
```

## Parallel Example: Review Remediation

```text
Task: "T040 Add complete CLI coverage-rendering assertions in tests/integration/test_eval_foundation_cli.py"
Task: "T041 Add global Git configuration isolation coverage in tests/integration/test_eval_foundation_reconstruction.py"
Task: "T047 Add unknown schema-version rejection coverage in tests/unit/test_eval_foundation_models.py and tests/unit/test_eval_foundation_load.py"
Task: "T048 Add complete SPDX and provenance URL coverage in tests/unit/test_eval_foundation_provenance.py and tests/integration/test_eval_foundation_provenance.py"
Task: "T049 Add injection pattern/location completeness coverage in tests/unit/test_eval_foundation_rubrics.py"
Task: "T053 Add requested-suite graph loading coverage in tests/unit/test_eval_foundation_load.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Write the US1 tests in T008-T011 and confirm they fail
3. Implement reconstruction, validation, coverage, assets, and CLI in T012-T020
4. Stop and validate the smoke suite offline against the independent test

### Incremental Delivery

1. Setup + Foundational establish versioned models and structured helpers
2. Add US1 for a working offline smoke validator
3. Add US2 for complete provenance, licensing-evidence, rubric, and safety review rules
4. Add US3 for curated suite intent, subset policy, and balance handling
5. Finish downstream adapter compatibility, documentation, quickstart scenarios, and quality gates
6. Complete US1 review remediation first because deterministic fixture digests and visible coverage block trustworthy downstream evals
7. Complete US2 schema/provenance/safety remediation and US3 suite-scoped loading remediation
8. Finish review documentation, formatting, and T058 merge-gate verification

### Suggested Team Split

1. One developer owns models/loading and provenance/rubric validation in tools/evals/gmuse_evals/models.py, tools/evals/gmuse_evals/load.py, and US2 tests
2. One developer owns Git reconstruction, smoke assets, and CLI behavior in tools/evals/gmuse_evals/git_reconstruct.py, tools/evals/gmuse_evals/cli.py, evals/, and US1 tests
3. One developer owns suite policy, coverage reporting, downstream adapter compatibility, and US3/polish tests

---

## Notes

- The evaluator remains maintainer-only under tools/evals/ and must not register a public `gmuse` command
- Normal validation must not clone repositories, import fixtures from the network, or call candidate/judge models
- Fixture patches must remain complete; truncation belongs only to later generation paths
- Source license evidence and redistribution review are distinct, and validation must not claim legal approval
- Human-readable CLI output is in scope; a stable external `--json` contract is deferred
- Commit after each task or cohesive task group and stop at each checkpoint for independent validation
