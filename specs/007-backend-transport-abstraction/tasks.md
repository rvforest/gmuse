---
description: "Task list for implementing backend and transport abstraction"
---

# Tasks: Backend and Transport Abstraction

**Input**: Design documents from `/specs/007-backend-transport-abstraction/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included (explicitly requested in the feature spec's Constitution Check).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the existing backend/provider flow is green before refactoring it.

- [X] T001 Run baseline quality checks (`uv sync` and targeted `pytest`) using pyproject.toml, noxfile.py, tests/unit/test_llm.py, and tests/integration/test_cli.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the shared backend abstraction scaffolding required by all user stories.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [X] T002 Add `backend` to defaults, environment-variable mapping, allowed config keys, and validation in src/gmuse/config.py
- [X] T003 Extend global config view/set support for the `backend` key in src/gmuse/cli/config.py
- [X] T004 Create the typed direct-backend registry, selection state, and resolution-context scaffolding in src/gmuse/llm.py
- [X] T005 Update shared test environment cleanup for `GMUSE_BACKEND` and backend credential combinations in tests/conftest.py

**Checkpoint**: Backend selection can be represented consistently across config, CLI plumbing, and test fixtures.

---

## Phase 3: User Story 1 - Preserve Simple Direct Setup (Priority: P1)

**Goal**: Keep today's single direct-backend setup working while separating backend selection from model selection.

**Independent Test**: Configure exactly one supported direct backend, run `gmuse msg` without `--backend` or `--model`, and confirm generation succeeds with that backend's maintained default model; then supply a model with a clear native backend hint and confirm the matching configured backend is selected automatically.

### Tests for User Story 1

- [X] T006 [P] [US1] Add unit coverage for single configured backend resolution, native backend hint preference, and ambiguity failures in tests/unit/test_llm.py
- [X] T007 [P] [US1] Add generation-path regression coverage for resolved backend/model handoff in tests/unit/test_commit.py and tests/integration/test_cli.py

### Implementation for User Story 1

- [X] T008 [US1] Implement automatic backend resolution order and default-model fallback for built-in direct backends in src/gmuse/llm.py
- [X] T009 [US1] Thread the resolved backend/model context through message generation without changing the single-backend happy path in src/gmuse/commit.py
- [X] T010 [US1] Replace provider-only auto-detection errors with backend-aware recovery messages for unresolved or unmapped direct backends in src/gmuse/llm.py

**Checkpoint**: Single-backend users retain the current low-friction workflow, but the execution path now resolves a backend and model explicitly.

---

## Phase 4: User Story 2 - Choose Backend Independently Of Model (Priority: P2)

**Goal**: Let users select a backend explicitly via CLI, environment variable, or config file, independent of the model name.

**Independent Test**: Configure multiple compatible direct backends, set an explicit backend via `--backend`, `GMUSE_BACKEND`, or `backend = "..."`, and confirm that explicit choice wins; then verify incompatible backend/model pairs and missing credentials fail before request submission.

### Tests for User Story 2

- [X] T011 [P] [US2] Add precedence coverage for CLI, environment, and config-file backend selection in tests/unit/test_config.py and tests/unit/test_cli_load_config_llm_overrides.py
- [X] T012 [P] [US2] Add CLI and integration coverage for explicit `--backend`, backend/model mismatch, and missing-credential failures in tests/unit/test_cli_main.py and tests/integration/test_cli_config.py

### Implementation for User Story 2

- [X] T013 [US2] Add the `--backend` option to `gmuse msg` and pass the override through config loading in src/gmuse/cli/main.py
- [X] T014 [US2] Resolve and persist explicit backend selection across CLI, environment, and config-file flows in src/gmuse/config.py and src/gmuse/cli/config.py
- [X] T015 [US2] Enforce explicit-backend precedence, compatibility validation, and pre-request credential checks in src/gmuse/llm.py

**Checkpoint**: Users can choose the backend deliberately, and invalid backend/model combinations fail deterministically before any request is sent.

---

## Phase 5: User Story 3 - Reserve Space For Future Backend Controls (Priority: P3)

**Goal**: Reserve a backend-specific settings mechanism and improve diagnostics without exposing inactive advanced options for current direct backends.

**Independent Test**: Use a supported direct backend and confirm `gmuse msg` and `gmuse info` expose the resolved backend/model context without requiring new backend-specific options; verify help and config surfaces do not advertise inactive backend-specific controls.

### Tests for User Story 3

- [X] T016 [P] [US3] Add unit coverage for the reserved backend-settings namespace and resolution-source fields in tests/unit/test_llm.py
- [X] T017 [P] [US3] Add diagnostics and help-surface regression coverage ensuring inactive backend-specific options stay hidden in tests/unit/test_cli_main_additional.py and tests/unit/test_cli_config.py

### Implementation for User Story 3

- [X] T018 [US3] Add reserved backend-settings namespace handling to the resolution context without exposing concrete options in src/gmuse/llm.py and src/gmuse/config.py
- [X] T019 [US3] Update `gmuse info` to report resolved backend, resolved model, and resolution source while omitting inactive backend-settings output in src/gmuse/cli/main.py
- [X] T020 [US3] Rename user-facing selection/help text from provider-centric wording to backend-centric wording where the backend/model distinction matters in src/gmuse/cli/main.py and src/gmuse/llm.py

**Checkpoint**: The abstraction exposes a future-safe backend namespace and clearer diagnostics without adding unused controls to the current UX.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Update documentation and run final regression checks across the full feature.

- [X] T021 [P] Document backend selection and terminology changes in README.md, docs/source/how_to/configuration.md, and docs/source/how_to/troubleshooting.md
- [X] T022 [P] Update CLI and configuration reference pages for `backend`, direct-backend defaults, and reserved namespaces in docs/source/reference/cli.md, docs/source/reference/configuration.md, and docs/source/reference/default_models.md
- [X] T023 Run the quickstart scenarios and align examples with final behavior in specs/007-backend-transport-abstraction/quickstart.md
- [X] T024 Run final regression checks for backend resolution using tests/unit/test_llm.py, tests/unit/test_cli_main.py, tests/integration/test_cli.py, tests/integration/test_cli_config.py, and noxfile.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories
- **User Stories (Phases 3-5)**: Depend on Foundational completion
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only and delivers the MVP path for existing single-backend users.
- **US2 (P2)**: Depends on Foundational only; recommended after US1 because it changes the same backend-resolution files but remains independently testable.
- **US3 (P3)**: Depends on Foundational only; recommended after US2 so diagnostics reflect the final backend-selection behavior.

### Within Each User Story

- Write the listed tests first and confirm they fail before implementing behavior.
- Update backend-resolution primitives before threading changes through CLI or commit-generation call paths.
- Finish validation and diagnostics for a story before moving to the next priority.

### Parallel Opportunities

- T006 and T007 can run in parallel once Foundational is complete.
- T011 and T012 can run in parallel once US2 implementation details are agreed.
- T016 and T017 can run in parallel once the reserved namespace shape is agreed.
- T021 and T022 can run in parallel after the user-facing wording is settled.

---

## Parallel Execution Examples

### Parallel Example: User Story 1

- Task: T006 [US1] tests/unit/test_llm.py
- Task: T007 [US1] tests/unit/test_commit.py and tests/integration/test_cli.py

### Parallel Example: User Story 2

- Task: T011 [US2] tests/unit/test_config.py and tests/unit/test_cli_load_config_llm_overrides.py
- Task: T012 [US2] tests/unit/test_cli_main.py and tests/integration/test_cli_config.py

### Parallel Example: User Story 3

- Task: T016 [US3] tests/unit/test_llm.py
- Task: T017 [US3] tests/unit/test_cli_main_additional.py and tests/unit/test_cli_config.py

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (T001).
2. Complete Phase 2 (T002-T005).
3. Implement and validate Phase 3 (T006-T010).
4. Stop and validate the preserved single-backend workflow before expanding scope.

### Incremental Delivery

1. Deliver US1 to preserve existing direct-backend behavior under the new abstraction.
2. Add US2 for explicit backend control across CLI, environment, and config file.
3. Add US3 for future-safe backend namespaces and clearer diagnostics.
4. Finish documentation and final regression checks in Phase 6.

### Parallel Team Strategy

1. Complete Setup and Foundational work together because they touch shared configuration and resolution files.
2. After Foundational, split test authoring across US1-US3 while one developer handles shared llm/config changes.
3. Reserve documentation updates for the end so wording matches the final CLI and diagnostic behavior.

---

## Notes

- `[P]` tasks are safe to run in parallel when the referenced files do not overlap.
- Every user story is independently testable from the criteria listed in its phase.
- Prefer small, typed backend-resolution helpers in src/gmuse/llm.py over scattering backend logic across call sites.
- Keep the initial scope limited to the current built-in direct backends: `openai`, `anthropic`, `cohere`, `azure`, and `gemini`.
