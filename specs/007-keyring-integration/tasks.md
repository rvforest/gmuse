---

description: "Task list for implementing secure API key management"

---

# Tasks: Secure API Key Management

**Input**: Design documents from `/specs/007-keyring-integration/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. The feature spec and plan require unit and integration coverage for backend qualification, auth flows, runtime resolution, and completion timeout behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the required dependency and confirm the current baseline before feature work starts.

- [X] T001 Add the `keyring` runtime dependency and any supporting test configuration in pyproject.toml
- [X] T002 Run baseline quality checks (`uv sync` + `uv run nox -s check`) using pyproject.toml and noxfile.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Introduce the shared credential abstraction and error surfaces that all user stories depend on.

**CRITICAL**: No user story work should begin until this phase is complete.

- [X] T003 Create shared credential-store scaffolding for service constants, index constants, masking, and empty-env normalization in src/gmuse/credentials.py
- [X] T004 [P] Add secure-backend qualification and auth/keyring exception types in src/gmuse/credentials.py and src/gmuse/exceptions.py
- [X] T005 [P] Add managed-index read/write helpers for `__gmuse_index__` in src/gmuse/credentials.py
- [X] T006 Implement env-first, empty-string-aware, keyring-fallback credential resolution hooks in src/gmuse/llm.py
- [X] T007 Implement shared actionable auth error formatting for CLI consumers in src/gmuse/exceptions.py and src/gmuse/cli/main.py

**Checkpoint**: The repo has one shared credential abstraction, secure backend checks, and a reusable runtime resolution path.

---

## Phase 3: User Story 1 - One-time interactive setup on a secure machine (Priority: P1) MVP

**Goal**: Users can securely store credentials once and use `gmuse msg` later without exporting env vars in each shell.

**Independent Test**: Run `gmuse auth set OPENAI_API_KEY`, start a fresh shell with no related env vars, then run `gmuse msg`; the credential resolves from the keyring and `gmuse auth status` shows the managed key with a masked value.

### Tests for User Story 1

- [X] T008 [P] [US1] Add unit tests for masking, managed-index reads, and empty-env fallthrough in tests/unit/test_credentials.py
- [X] T009 [P] [US1] Add CLI unit tests for `gmuse auth set` and `gmuse auth status [provider]` in tests/unit/test_cli_auth.py
- [X] T010 [P] [US1] Add integration coverage for storing a credential and resolving it through `gmuse msg` in tests/integration/test_keyring_auth_integration.py

### Implementation for User Story 1

- [X] T011 [US1] Implement secure credential read/write helpers and overwrite confirmation behavior in src/gmuse/credentials.py
- [X] T012 [US1] Implement `gmuse auth set` and `gmuse auth status [provider]` in src/gmuse/cli/auth.py
- [X] T013 [US1] Register the `gmuse auth` command group and help text in src/gmuse/cli/main.py
- [X] T014 [US1] Pass keyring-resolved credentials into the message generation flow in src/gmuse/llm.py and src/gmuse/commit.py

**Checkpoint**: US1 is independently functional; interactive users can store credentials once and reuse them across shells.

---

## Phase 4: User Story 4 - No auth configured anywhere (Priority: P1)

**Goal**: New users get a clear error that points them to both supported setup paths when no credentials exist.

**Independent Test**: Run `gmuse msg` with no relevant env vars and no keyring entries; the command exits non-zero and tells interactive users to run `gmuse auth set` while directing CI users to environment variables.

### Tests for User Story 4

- [X] T015 [P] [US4] Add unit regression tests for missing-credential guidance in tests/unit/test_llm.py
- [X] T016 [P] [US4] Add CLI integration coverage for the no-env/no-keyring error path in tests/integration/test_cli.py

### Implementation for User Story 4

- [X] T017 [US4] Update missing-credential error construction to name the interactive and CI setup paths in src/gmuse/llm.py and src/gmuse/exceptions.py
- [X] T018 [US4] Ensure `gmuse msg` renders the actionable auth guidance consistently in src/gmuse/cli/main.py

**Checkpoint**: US4 is independently functional; missing-credential failures are actionable instead of generic.

---

## Phase 5: User Story 2 - Linux/WSL without a secure keyring backend (Priority: P2)

**Goal**: Users on systems without a secure keyring fail before prompting and get clear fallback guidance.

**Independent Test**: Run `gmuse auth set OPENAI_API_KEY` with mocked `NoKeyringError`, `keyrings.alt`, and null backends; each path exits before prompting and directs the user to environment variables.

### Tests for User Story 2

- [X] T019 [P] [US2] Add unit tests for `NoKeyringError`, `keyrings.alt`, and null backend rejection in tests/unit/test_credentials.py
- [X] T020 [P] [US2] Add integration coverage that `gmuse auth set` fails before prompting on insecure or unavailable backends in tests/integration/test_keyring_auth_integration.py

### Implementation for User Story 2

- [X] T021 [US2] Map unavailable and insecure backend states to dedicated auth failures in src/gmuse/credentials.py and src/gmuse/exceptions.py
- [X] T022 [US2] Surface Linux/WSL fallback guidance from `gmuse auth set` in src/gmuse/cli/auth.py

**Checkpoint**: US2 is independently functional; unsupported backends are rejected safely and clearly.

---

## Phase 6: User Story 3 - Removing stored credentials (Priority: P2)

**Goal**: Users can remove one or more stored credentials and inspect the remaining managed entries.

**Independent Test**: Store multiple credentials, run `gmuse auth remove VAR1 VAR2`, then run `gmuse auth status`; removed entries no longer appear and missing variables are reported gracefully.

### Tests for User Story 3

- [X] T023 [P] [US3] Add unit tests for multi-entry removal and `__gmuse_index__` maintenance in tests/unit/test_credentials.py
- [X] T024 [P] [US3] Add CLI and integration coverage for `gmuse auth remove` and default `gmuse auth status` output in tests/unit/test_cli_auth.py and tests/integration/test_keyring_auth_integration.py

### Implementation for User Story 3

- [X] T025 [US3] Implement credential deletion and missing-entry handling in src/gmuse/credentials.py
- [X] T026 [US3] Implement `gmuse auth remove` and default managed-key status table output in src/gmuse/cli/auth.py

**Checkpoint**: US3 is independently functional; users can rotate or clean up stored credentials without corrupting the index.

---

## Phase 7: User Story 5 - Tab completions degrade gracefully (Priority: P3)

**Goal**: Shell completions never hang when keyring access blocks, prompts, or exceeds the timeout budget.

**Independent Test**: Trigger the completion helper with a keyring backend that blocks or prompts; the command returns within 200ms with no suggestion and no shell-visible auth error.

### Tests for User Story 5

- [X] T027 [P] [US5] Add unit tests for bounded completion credential lookup in tests/unit/test_cli_completions.py
- [X] T028 [P] [US5] Add integration coverage for 200ms completion timeout degradation in tests/integration/test_completions_run.py

### Implementation for User Story 5

- [X] T029 [US5] Add completion-safe keyring lookup helpers with a 200ms budget in src/gmuse/credentials.py and src/gmuse/cli/completions.py
- [X] T030 [US5] Map timeout, prompt, and backend failures to silent no-suggestion completion results in src/gmuse/cli/completions.py

**Checkpoint**: US5 is independently functional; completion paths degrade silently and stay responsive.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Finish documentation and run end-to-end validation for the feature.

- [X] T031 [P] Document auth commands, keyring precedence, masking, and CI guidance in docs/source/reference/cli.md and docs/source/reference/configuration.md
- [X] T032 [P] Document privacy, completions, configuration, and troubleshooting updates in docs/source/explanation/privacy.md, docs/source/how_to/completions.md, docs/source/how_to/configuration.md, and docs/source/how_to/troubleshooting.md
- [X] T033 Run the feature quickstart scenarios for interactive setup, fallback, removal, and completions using specs/007-keyring-integration/quickstart.md
- [X] T034 Run final quality checks (`uv run nox -s check`) using noxfile.py and pyproject.toml

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories
- **User Stories (Phases 3-7)**: Depend on Foundational completion
- **Polish (Phase 8)**: Depends on all target user stories being complete

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational and delivers the MVP credential storage and fallback path
- **US4 (P1)**: Starts after Foundational and reuses the shared resolution/error path; independent from auth command UX
- **US2 (P2)**: Starts after Foundational and shares the credential backend qualification helpers
- **US3 (P2)**: Starts after Foundational and benefits from the auth command scaffolding introduced in US1
- **US5 (P3)**: Starts after Foundational and reuses the credential resolution helpers introduced earlier

### Within Each User Story

- Tests should be written before implementation and fail first
- Shared credential helpers should land before Typer command wiring that consumes them
- Runtime wiring should be completed before final integration assertions

---

## Parallel Execution Examples

### Parallel Example: User Story 1

These can run in parallel after Phase 2 completes:

- Task: T008 [US1] in tests/unit/test_credentials.py
- Task: T009 [US1] in tests/unit/test_cli_auth.py
- Task: T010 [US1] in tests/integration/test_keyring_auth_integration.py

### Parallel Example: User Story 2

These can run in parallel after Phase 2 completes:

- Task: T019 [US2] in tests/unit/test_credentials.py
- Task: T020 [US2] in tests/integration/test_keyring_auth_integration.py

### Parallel Example: User Story 3

These can run in parallel after Phase 2 completes:

- Task: T023 [US3] in tests/unit/test_credentials.py
- Task: T024 [US3] in tests/unit/test_cli_auth.py and tests/integration/test_keyring_auth_integration.py

### Parallel Example: User Story 5

These can run in parallel after Phase 2 completes:

- Task: T027 [US5] in tests/unit/test_cli_completions.py
- Task: T028 [US5] in tests/integration/test_completions_run.py

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (T001-T002)
2. Complete Phase 2 (T003-T007)
3. Implement and validate Phase 3 (T008-T014)
4. Stop and validate `gmuse auth set` + `gmuse msg` keyring fallback before expanding scope

### Incremental Delivery

1. Deliver US1 for secure interactive setup and runtime fallback
2. Add US4 so missing-credential failures are actionable for new users
3. Add US2 for insecure backend safety
4. Add US3 for credential removal and managed-status maintenance
5. Add US5 for completion-time timeout guarantees
6. Finish docs and final checks in Phase 8

### Parallel Team Strategy

1. One developer completes Setup + Foundational
2. After Phase 2, split work by story:
   - Developer A: US1 or US4
   - Developer B: US2 or US3
   - Developer C: US5 and documentation follow-up

---

## Notes

- [P] tasks target different files or are safe to execute concurrently
- Each story phase is independently testable using the stated acceptance path
- Default `auth status` behavior stays scoped to gmuse-managed variables via the hidden index entry
- Provider-specific status validation belongs to US1 because it shares the `auth status` command surface
