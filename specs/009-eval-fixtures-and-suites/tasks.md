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

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** — no dependencies
- **Phase 2: Foundational** — depends on Phase 1 and blocks all user stories
- **Phase 3: US1** — depends on Phase 2 and delivers the MVP
- **Phase 4: US2** — depends on Phase 2; its temporary origin/rubric cases are independently testable
- **Phase 5: US3** — depends on Phase 2; T033-T034 additionally depend on US1's checked-in cases and smoke suite
- **Phase 6: Polish** — depends on all selected user stories

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational with no dependency on another story and delivers offline smoke validation
- **US2 (P2)**: Starts after Foundational and can be completed with temporary fixtures independently of US1; the final checked-in injection fixture benefits from its safety validation
- **US3 (P3)**: Starts after Foundational for suite-policy logic; checked-in smoke/core integration depends on US1's fixture, rubric, and case assets

### Within Each User Story

- Tests must be written first and confirmed failing before implementation
- Structural loading must precede domain validation
- Repository reconstruction must precede digest generation for checked-in fixtures
- Fixture and rubric assets must exist before cases; cases must exist before suites
- Core logic must return structured results before CLI rendering is finalized

---

## Parallel Opportunities

- **Setup**: T002 can proceed independently while T001 updates dependency and type-check configuration
- **Foundational**: T003 and T004 can run in parallel before T005-T007
- **US1**: T008-T011 can run in parallel; T015-T017 can run in parallel after reconstruction is available; T019 can proceed alongside asset authoring after T013
- **US2**: T021-T023 can run in parallel before T024-T026
- **US3**: T027-T029 can run in parallel before T030-T032
- **Polish**: T035 and T037 can run in parallel before T036 and final validation

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
