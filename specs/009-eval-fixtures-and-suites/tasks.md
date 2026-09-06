# Tasks: Eval Fixtures And Suites

**Input**: Design documents in `specs/009-eval-fixtures-and-suites/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and
`contracts/`

**Tests**: Tests are included because the specification and project constitution
require unit and integration coverage for this maintainer CLI foundation.

**Organization**: Tasks are grouped by user story. Each story has a usable,
independently testable increment after the shared foundation is complete.

## Phase 1: Setup

**Purpose**: Establish the final asset layout and reusable test support.

- [X] T001 [P] Add the `evals/scoring_profiles/` catalog directory and extend shared temporary-asset helpers for all five asset catalogs in `tests/conftest.py`.
- [X] T002 [P] Add representative final-schema TOML fixtures for profiles, rubrics, cases, and suites to `tests/unit/test_eval_foundation_load.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define schema-versioned, revision-tracked models and the selected-graph loader that every
report, rubric, and composition goal uses.

**⚠️ CRITICAL**: Complete this phase before implementing user stories.

- [X] T003 Add failing model tests for scoring profiles, four anchored ratings, usability labels, case rubrics, deterministic gates, annotated examples, and composition goals in `tests/unit/test_eval_foundation_models.py`.
- [X] T004 Add failing catalog and reference-validation tests for profile, rubric, case, and suite loading in `tests/unit/test_eval_foundation_load.py` and `tests/unit/test_eval_foundation_rubrics.py`.
- [X] T005 Define final schema-1.0 Pydantic models for scoring profiles, rubric criteria, failure conditions, deterministic gates, examples, composition goals, composition entries, and validation reports in `tools/evals/gmuse_evals/*_models.py`, with `models.py` as the canonical import surface.
- [X] T006 Update catalog discovery, selected-graph loading, duplicate-ID diagnostics, and profile/rubric reference resolution in `tools/evals/gmuse_evals/load.py`.
- [X] T007 Export the final public evaluator model types from `tools/evals/gmuse_evals/__init__.py`.
- [X] T008 Confirm the original fixture reconstruction, staged-change identity, changed-path, and provenance tests still exercise the final asset graph in `tests/unit/test_eval_foundation_provenance.py`, `tests/unit/test_eval_foundation_validation.py`, `tests/integration/test_eval_foundation_provenance.py`, and `tests/integration/test_eval_foundation_reconstruction.py`.

**Checkpoint**: Final-schema assets load deterministically, and all later work
can rely on typed profiles, rubrics, and composition goals.

---

## Phase 3: User Story 1 - Understand a validated suite at a glance (Priority: P1) 🎯 MVP

**Goal**: Render a plain-language, counted suite-composition report that is
separate from validation status and errors.

**Independent Test**: Validate the checked-in smoke suite and confirm the
output shows counted Changes, Output formats, Context variations, Safety
scenarios, and Fixture sources without relying on raw comma-separated values.

### Tests for User Story 1

- [X] T009 [P] [US1] Add unit tests for stable, counted composition groups, multi-format cases, ordinary versus injection cases, and no fabricated entries for unresolved cases in `tests/unit/test_eval_foundation_composition.py`.
- [X] T010 [P] [US1] Add CLI rendering tests that distinguish status/errors from `Suite composition` and use human-readable counted labels in `tests/integration/test_eval_foundation_cli.py`.
- [X] T011 [P] [US1] Add checked-in smoke-suite integration assertions for all report groups in `tests/integration/test_eval_foundation_smoke.py`.

### Implementation for User Story 1

- [X] T012 [US1] Replace generic coverage collection with resolved-case `SuiteComposition` collection, including stable groups and human labels, in `tools/evals/gmuse_evals/composition.py`.
- [X] T013 [US1] Render the grouped `Suite composition` report with case counts while preserving actionable validation errors in `tools/evals/gmuse_evals/cli.py`.
- [X] T014 [US1] Update the checked-in fixture, case, and smoke-suite assets used by the report in `evals/fixtures/`, `evals/cases/`, and `evals/suites/smoke.toml`.

**Checkpoint**: A maintainer can understand what the smoke suite contains from
one offline validation report.

---

## Phase 4: User Story 2 - Author a rubric that explains future scoring (Priority: P1)

**Goal**: Provide a reusable scored-assessment profile and case-specific,
reviewable rubrics that clearly separate judgment from objective gates.

**Independent Test**: Read the ordinary and injection-safety rubrics and
classify representative messages using their anchors, gates, failure
conditions, and annotations without requiring an exact message match.

### Tests for User Story 2

- [X] T015 [P] [US2] Add validation tests for dimension references, anchor completeness, applicability, criterion and failure-condition structure, supported deterministic gates, and the two required annotated examples in `tests/unit/test_eval_foundation_rubrics.py`.
- [X] T016 [P] [US2] Add loader tests for missing or incompatible scoring-profile and rubric references in `tests/unit/test_eval_foundation_load.py`.
- [X] T017 [P] [US2] Add adapter tests proving that profile and rubric identity, revision, and digest are preserved as metadata without generating scoring prompts in `tests/unit/test_eval_foundation_inspect_adapter.py`.

### Implementation for User Story 2

- [X] T018 [US2] Validate scoring-profile anchors and usability illustrations, rubric dimensions and error categories, deterministic-gate evidence, and annotated examples in `tools/evals/gmuse_evals/validation_rules.py`.
- [X] T019 [US2] Add the `commit-message-v1` profile and author final-schema ordinary and injection-safety rubrics in `evals/scoring_profiles/commit-message-v1.toml` and `evals/rubrics/`.
- [X] T020 [US2] Bind each checked-in case to its rubric and preserve its generation context in `evals/cases/docs-history.toml` and `evals/cases/injection-comment.toml`.
- [X] T021 [US2] Extend Inspect descriptors with scoring-profile and rubric identity, revision, and digest in `tools/evals/gmuse_evals/inspect_adapter.py`.
- [X] T022 [US2] Add an end-to-end checked-in-asset test for rubric/profile validation and adapter metadata in `tests/integration/test_eval_foundation_suites.py`.

**Checkpoint**: Every checked-in case has a concise, reviewable explanation of
future assessment while offline validation remains deterministic.

---

## Phase 5: User Story 3 - Curate suites with meaningful composition goals (Priority: P2)

**Goal**: Let maintainers state which exact scenarios a suite needs, with clear
required or advisory outcomes.

**Independent Test**: Validate a temporary suite with selector/value/minimum
goals and verify the observed and required counts, default advisory warning,
and `--strict-composition` failure behavior.

### Tests for User Story 3

- [X] T023 [P] [US3] Add unit tests for supported selectors, value matching, matching-case counts, duplicate/conflicting goals, unknown values, and required/advisory shortfalls in `tests/unit/test_eval_foundation_composition.py` and `tests/unit/test_eval_foundation_suites.py`.
- [X] T024 [P] [US3] Add CLI tests for `--strict-composition`, advisory warnings, and required-goal failures in `tests/integration/test_eval_foundation_cli.py`.
- [X] T025 [P] [US3] Add integration tests showing smoke is a core subset and core reports its configured composition goals in `tests/integration/test_eval_foundation_suites.py`.

### Implementation for User Story 3

- [X] T026 [US3] Implement selector/value/minimum-case composition-goal evaluation and required/advisory diagnostics in `tools/evals/gmuse_evals/composition.py`.
- [X] T027 [US3] Replace the evaluator CLI option with `--strict-composition`, including help text and exit-status behavior, in `tools/evals/gmuse_evals/cli.py` and `tools/evals/gmuse_evals/__main__.py`.
- [X] T028 [US3] Define minimal smoke goals and initial core composition goals using final-schema suite assets in `evals/suites/smoke.toml` and `evals/suites/core.toml`.

**Checkpoint**: A maintainer can see exactly which missing scenario matters and
choose whether advisory curation gaps should block validation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Complete documentation, downstream design alignment, and quality
verification for the complete final design.

- [X] T029 [P] Update maintainer validation guidance, command examples, report terminology, rubric-reading guidance, and deterministic-gate limits in `docs/source/development/contributing.md` and `specs/009-eval-fixtures-and-suites/quickstart.md`.
- [X] T030 [P] Align future runner and resume design with profile/rubric identities and a privacy-reviewed immutable assessment-evidence reference in `specs/draft/010-eval-runner/` and `specs/draft/011-eval-live-budgeting-resume/`.
- [X] T031 [P] Align future scoring and comparison design with named 1–4 profile ratings, categorical usability, deterministic versus judge-sourced gates, and no aggregate score in `specs/draft/012-eval-judge-scoring/` and `specs/draft/013-eval-baselines-comparison/`.
- [X] T032 Run the documented offline smoke and core validation walkthroughs in `specs/009-eval-fixtures-and-suites/quickstart.md` and confirm no provider call, normal `gmuse` CLI behavior, or ordinary report exposes raw generation prompts.
- [X] T033 Run evaluator-focused tests in `tests/unit/test_eval_foundation_*.py` and `tests/integration/test_eval_foundation_*.py`.
- [X] T034 Run the project quality gates `uv run nox -s format`, `uv run nox -s lint`, `uv run nox -s types`, `uv run nox -s test`, and `uv run nox -s docs`.

## Phase 7: Review Hardening And Simplification

**Purpose**: Apply pre-merge review findings while the evaluator API remains
unreleased and can be simplified without compatibility constraints.

- [X] T035 Add regression tests for strict schema-1.0 rubrics, unique case formats, hard-gate usability, Git-environment isolation, long fixture histories, and composition-only CLI output.
- [X] T036 Remove legacy rubric, coverage-policy, alias, and deprecated-flag APIs; use one canonical evaluator vocabulary and split models, composition, domain rules, and validation orchestration by responsibility.
- [X] T037 Update evaluator documentation and downstream drafts for the simplified API and report shape.
- [X] T038 Run focused evaluator tests, Git tests, smoke/core validation, formatting, linting, types, documentation, and the full test suite.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can begin immediately.
- **Foundational (Phase 2)**: Depends on T001–T002 and blocks all user-story
  implementation.
- **US1, US2, and US3 (Phases 3–5)**: Can begin after Phase 2. US1 and US2
  are both P1; US3 relies on the shared composition model but not on either
  story's report rendering.
- **Polish (Phase 6)**: Follows the desired story phases; T032–T034 follow all
  implementation and documentation tasks.

### User Story Dependencies

- **US1 (P1)**: Depends only on the final models and loader from Phase 2.
- **US2 (P1)**: Depends only on the final models and loader from Phase 2.
- **US3 (P2)**: Depends on Phase 2; its report assertions use the US1
  composition result, so complete T012 before accepting T025.

### Parallel Opportunities

- T001–T002 may run in parallel.
- T003–T004 may run in parallel before T005–T007; T008 may proceed after T006.
- Within each user story, its `[P]` tests can be written concurrently before
  their implementation tasks.
- After Phase 2, US1 and US2 can be developed in parallel; US3's selector
  validation may proceed in parallel with them, with its integration work after
  T012.
- T029–T031 can run in parallel after behavior is settled.

## Implementation Strategy

### MVP First

1. Complete Phases 1 and 2.
2. Complete US1 (T009–T014).
3. Run the US1 independent test against the smoke suite.
4. Demonstrate the plain-language suite-composition report to maintainers.

### Incremental Delivery

1. Deliver US1 for understandable validation output.
2. Deliver US2 for reviewable future assessment guidance.
3. Deliver US3 for explicit suite curation goals.
4. Complete cross-cutting documentation and full quality checks.
