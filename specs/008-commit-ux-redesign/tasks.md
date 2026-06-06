# Tasks: Breaking CLI UX Redesign for Commit Message Generation

**Input**: Design documents from `/specs/008-commit-ux-redesign/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli-commands.md`, `contracts/completion-runtime.md`, `quickstart.md`

**Tests**: This feature requires unit, integration, lint, type, and docs validation using the existing pytest/nox workflow.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently once Phase 2 is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete-task dependency)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`, `[US4]`)
- Every task includes concrete repository file paths

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new module/test/doc touchpoints needed for the redesign without changing behavior yet.

- [ ] T001 Create commit workflow scaffolding in src/gmuse/cli/commit_session.py, tests/unit/test_cli_commit_session.py, and tests/integration/test_cli_generate_commit.py
- [ ] T002 [P] Add command-surface baseline assertions for renamed CLI help in tests/unit/test_cli_main.py and tests/unit/test_cli_main_additional.py
- [ ] T003 [P] Add reusable git/editor test helpers for commit-flow integration coverage in tests/integration/test_cli.py and tests/integration/test_cli_generate_commit.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared raw-generation and commit-execution boundaries that every story depends on.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [ ] T004 Extract a shared raw-generation request/result helper from src/gmuse/cli/main.py into src/gmuse/commit.py and src/gmuse/cli/config_resolution.py so commit, generate, msg, and completions share one generation path
- [ ] T005 [P] Add commit-session, migration, and non-interactive CLI error types in src/gmuse/exceptions.py and map them in src/gmuse/cli/main.py
- [ ] T006 [P] Add direct commit, editor handoff, and HEAD-change git wrappers in src/gmuse/git.py for accept/edit/--yes outcomes
- [ ] T007 [P] Deprecate clipboard compatibility inputs in src/gmuse/config.py and src/gmuse/cli/config_resolution.py so GMUSE_COPY and copy_to_clipboard stay inert on raw/completion success paths
- [ ] T008 Preserve the raw completion boundary in src/gmuse/cli/completions.py by reusing the shared generation helper without importing src/gmuse/cli/commit_session.py

**Checkpoint**: Shared generation, git commit wrappers, and compatibility/error plumbing are ready for story work.

---

## Phase 3: User Story 1 - Review and finalize an AI-generated commit interactively (Priority: P1) 🎯 MVP

**Goal**: Make `gmuse commit` the primary interactive workflow with accept, edit, regenerate, and abort actions before any commit is finalized.

**Independent Test**: In a repo with staged changes, run `gmuse commit` in an interactive terminal and verify accept, edit, regenerate, and abort all behave correctly without manual copy/paste.

### Tests for User Story 1 ⚠️

> **NOTE**: Write these tests first and confirm they fail before implementation.

- [ ] T009 [P] [US1] Add unit tests for accept/edit/regenerate/abort review-loop branches in tests/unit/test_cli_commit_session.py
- [ ] T010 [P] [US1] Add integration tests for interactive accept/edit/regenerate/abort flows in tests/integration/test_cli_generate_commit.py

### Implementation for User Story 1

- [ ] T011 [US1] Implement CommitSession, GeneratedDraft tracking, and review-action orchestration in src/gmuse/cli/commit_session.py
- [ ] T012 [US1] Add the interactive gmuse commit command, draft rendering, and action prompt wiring in src/gmuse/cli/main.py
- [ ] T013 [US1] Surface accept/edit success and failure outcomes consistently in src/gmuse/cli/commit_session.py and src/gmuse/git.py

**Checkpoint**: `gmuse commit` interactive review works end-to-end and is independently testable.

---

## Phase 4: User Story 2 - Commit immediately when I trust the generated draft (Priority: P1)

**Goal**: Support `gmuse commit --yes` as the explicit fast path and fail fast when interactive review would hang in non-interactive environments.

**Independent Test**: Run `gmuse commit --yes` with staged changes and verify it commits immediately; run `gmuse commit` without TTYs and verify it exits with guidance instead of prompting.

### Tests for User Story 2 ⚠️

- [ ] T014 [P] [US2] Add unit tests for `gmuse commit --yes`, `gmuse commit --dry-run` rejection, and the non-interactive guard in tests/unit/test_cli_main.py and tests/unit/test_cli_commit_session.py
- [ ] T015 [P] [US2] Add integration tests for `gmuse commit --yes` success and non-interactive `gmuse commit` failure guidance in tests/integration/test_cli_generate_commit.py

### Implementation for User Story 2

- [ ] T016 [US2] Implement the `--yes` fast path and reject raw-only options on commit in src/gmuse/cli/main.py and src/gmuse/cli/commit_session.py
- [ ] T017 [US2] Enforce non-interactive guard messaging and exit behavior in src/gmuse/cli/main.py and src/gmuse/exceptions.py

**Checkpoint**: The fast path works without prompts, and non-interactive `gmuse commit` no longer risks hanging.

---

## Phase 5: User Story 3 - Use raw generation for scripts and shell completion plumbing (Priority: P1)

**Goal**: Expose `gmuse generate` as the stdout-only primitive while keeping `gmuse git-completions-run` on the same raw generation path.

**Independent Test**: Run `gmuse generate` and verify stdout contains only the commit message; run `gmuse git-completions-run` and verify stdout remains JSON-only without any interactive commit behavior.

### Tests for User Story 3 ⚠️

- [ ] T018 [P] [US3] Add unit tests for shared raw-generation option plumbing and completion invariants in tests/unit/test_cli_main.py, tests/unit/test_commit.py, and tests/unit/test_cli_completions.py
- [ ] T019 [P] [US3] Add integration tests for stdout-only `gmuse generate` and JSON-only `gmuse git-completions-run` behavior in tests/integration/test_cli_generate_commit.py and tests/integration/test_completions_run.py

### Implementation for User Story 3

- [ ] T020 [US3] Add the `gmuse generate` command and shared stdout-only execution helper in src/gmuse/cli/main.py and src/gmuse/commit.py
- [ ] T021 [US3] Route completion runtime through the shared raw-generation helper while preserving timeout/status mapping in src/gmuse/cli/completions.py
- [ ] T022 [US3] Update command ordering and raw-generation help text in src/gmuse/cli/main.py and docs/source/development/shell-completions.md

**Checkpoint**: Scripts and completions use the raw path only, with no commit/editor/clipboard side effects.

---

## Phase 6: User Story 4 - Understand and migrate from the old command surface (Priority: P2)

**Goal**: Provide a clear migration path from `gmuse msg` and retired clipboard behavior to `gmuse generate` and `gmuse commit`.

**Independent Test**: Verify `gmuse --help`, `gmuse msg`, and `gmuse msg --copy` clearly describe the new command split, deprecation window, and retired clipboard workflow.

### Tests for User Story 4 ⚠️

- [ ] T023 [P] [US4] Add unit tests for deprecated `gmuse msg`, `gmuse msg --copy`, and passive clipboard compatibility handling in tests/unit/test_cli_main.py and tests/unit/test_config.py
- [ ] T024 [P] [US4] Add integration tests for `gmuse msg` deprecation stderr, `gmuse msg --copy` migration errors, and ignored clipboard compatibility inputs in tests/integration/test_cli_generate_commit.py and tests/integration/test_completions_run.py

### Implementation for User Story 4

- [ ] T025 [US4] Convert `gmuse msg` into a deprecated alias for `gmuse generate` and remove `--copy` from primary command surfaces in src/gmuse/cli/main.py
- [ ] T026 [US4] Implement retired clipboard migration behavior for GMUSE_COPY and copy_to_clipboard in src/gmuse/config.py, src/gmuse/cli/config_resolution.py, and src/gmuse/exceptions.py
- [ ] T027 [US4] Update migration guidance in README.md, docs/source/reference/cli.md, docs/source/reference/configuration.md, docs/source/tutorials/quickstart.md, docs/source/how_to/completions.md, docs/source/how_to/troubleshooting.md, and docs/source/explanation/how_it_works.md

**Checkpoint**: Legacy entry points are still understandable, but users are guided firmly to the new workflow.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final docs alignment, scenario validation, and repository quality checks across all stories.

- [ ] T028 [P] Refresh primary workflow and migration examples in docs/source/reference/cli.md, docs/source/how_to/configuration.md, docs/source/how_to/completions.md, docs/source/tutorials/quickstart.md, and README.md
- [ ] T029 Validate the feature walkthrough against specs/008-commit-ux-redesign/quickstart.md and keep end-to-end examples aligned in tests/integration/test_cli_generate_commit.py
- [ ] T030 Run `uv run nox -s test`, `uv run nox -s lint`, `uv run nox -s types`, and `uv run nox -s docs` for the changes governed by noxfile.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** — no dependencies
- **Phase 2: Foundational** — depends on Phase 1 and blocks all user stories
- **Phase 3: US1** — depends on Phase 2
- **Phase 4: US2** — depends on Phase 2 and benefits from US1 command wiring
- **Phase 5: US3** — depends on Phase 2 and must preserve the raw-generation boundary introduced there
- **Phase 6: US4** — depends on Phases 3-5 because aliasing and migration text must reflect the finished command surfaces
- **Phase 7: Polish** — depends on all selected user stories being complete

### User Story Dependencies

- **US1**: Starts after Foundational and delivers the MVP interactive commit flow
- **US2**: Starts after Foundational; shares `gmuse commit` plumbing with US1 but remains independently testable through `--yes` and non-interactive failure behavior
- **US3**: Starts after Foundational; depends on the shared raw helper, not on interactive commit orchestration
- **US4**: Starts after the command surfaces from US1-US3 are stable enough to document and deprecate

### Within Each User Story

- Tests first, and they must fail before implementation
- Shared command/helper plumbing before story-specific help/docs updates
- Git/editor outcome handling before success messaging
- Complete one story end-to-end before counting it as done

---

## Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel after T001 creates the new file touchpoints
- **Phase 2**: T005, T006, T007, and T008 can run in parallel after T004 defines the shared raw-generation seam
- **US1**: T009 and T010 can run together; T011 and T013 can overlap once the session structure exists
- **US2**: T014 and T015 can run together before T016 and T017
- **US3**: T018 and T019 can run together; T021 and T022 can proceed after T020 establishes `gmuse generate`
- **US4**: T023 and T024 can run together; T027 can start once T025 defines the final alias/help behavior
- **Polish**: T028 and T029 can run in parallel before T030 executes the full nox validation suite

---

## Parallel Example: User Story 1

```bash
# Write failing coverage for the review loop in parallel:
Task: "T009 Add unit tests for accept/edit/regenerate/abort review-loop branches in tests/unit/test_cli_commit_session.py"
Task: "T010 Add integration tests for interactive accept/edit/regenerate/abort flows in tests/integration/test_cli_generate_commit.py"

# After the session model exists, implementation can split cleanly:
Task: "T011 Implement CommitSession, GeneratedDraft tracking, and review-action orchestration in src/gmuse/cli/commit_session.py"
Task: "T013 Surface accept/edit success and failure outcomes consistently in src/gmuse/cli/commit_session.py and src/gmuse/git.py"
```

## Parallel Example: User Story 3

```bash
# Protect the raw path before changing command wiring:
Task: "T018 Add unit tests for shared raw-generation option plumbing and completion invariants in tests/unit/test_cli_main.py, tests/unit/test_commit.py, and tests/unit/test_cli_completions.py"
Task: "T019 Add integration tests for stdout-only gmuse generate and JSON-only gmuse git-completions-run behavior in tests/integration/test_cli_generate_commit.py and tests/integration/test_completions_run.py"

# Once generate exists, completion and docs can move independently:
Task: "T021 Route completion runtime through the shared raw-generation helper while preserving timeout/status mapping in src/gmuse/cli/completions.py"
Task: "T022 Update command ordering and raw-generation help text in src/gmuse/cli/main.py and docs/source/development/shell-completions.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Deliver Phase 3 (`gmuse commit` interactive review flow)
3. Validate accept/edit/regenerate/abort independently
4. Stop and demo before expanding to `--yes`, `generate`, and migration work

### Incremental Delivery

1. Setup + Foundational establish the shared raw path and commit wrappers
2. Add US1 for the new primary workflow
3. Add US2 for trusted fast-path and non-interactive safety
4. Add US3 for scripting/completion preservation
5. Add US4 for migration, aliasing, and clipboard retirement
6. Finish with docs and nox validation

### Suggested Team Split

1. One developer owns Phase 2 shared helpers (`src/gmuse/commit.py`, `src/gmuse/git.py`, `src/gmuse/exceptions.py`)
2. One developer owns `gmuse commit` session UX (`src/gmuse/cli/main.py`, `src/gmuse/cli/commit_session.py`, US1-US2 tests)
3. One developer owns raw path + migration docs (`src/gmuse/cli/completions.py`, README.md, docs/source/, US3-US4 tests)

---

## Notes

- `gmuse commit` and `gmuse generate` must remain separate orchestration layers even when they reuse the same raw-generation helper
- `gmuse git-completions-run` must stay JSON-only and must never import or execute interactive commit-session logic
- `gmuse msg` is temporary compatibility only; migration guidance belongs on stderr, not stdout
- Passive clipboard compatibility inputs must never violate the stdout-only success contract of `gmuse generate`
