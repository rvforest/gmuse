---

description: "Task list for implementing max_chars commit message limit"
---

# Tasks: Commit Message Max Characters (`max_chars`)

**Input**: Design documents from `/specs/006-commit-message-max-chars/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included (explicitly requested in the feature spec’s Constitution Check).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm development environment and baseline checks are green before making changes.

- [ ] T001 Run baseline quality checks (`uv sync` + `uv run nox -s check`) using noxfile.py and pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core configuration plumbing required by all user stories.

- [X] T002 Add `max_chars` default (`None`) and constants (`MAX_CHARS_MIN/MAX_CHARS_MAX`) in src/gmuse/config.py
- [X] T003 Implement range/type validation for `max_chars` (1–500) in src/gmuse/config.py
- [X] T004 Add environment variable mapping `GMUSE_MAX_CHARS` → `max_chars` in src/gmuse/config.py
- [X] T005 Document `GMUSE_MAX_CHARS` in the environment variable list and config docs section in src/gmuse/config.py

**Checkpoint**: `max_chars` can be loaded from TOML/env and validated; no user story behavior changes yet.

---

## Phase 3: User Story 1 - Limit commit message size (Priority: P1) 🎯 MVP

**Goal**: Users can set `max_chars` and generated messages respect it; the value is included in the prompt context.

**Independent Test**: With `GMUSE_MAX_CHARS=50`, generating a message that is 51+ characters fails with an error that includes actual length and configured limit; when the message is ≤50 characters, generation succeeds.

### Tests for User Story 1 ⚠️

- [X] T006 [P] [US1] Add unit test asserting `max_chars` is included in the user prompt in tests/unit/test_prompts.py
- [X] T007 [P] [US1] Add unit test asserting Conventional Commit prompt has no conflicting fixed length rule when `max_chars` is set in tests/unit/test_prompts.py
- [X] T008 [P] [US1] Add unit test asserting length-exceeded error includes actual length and configured limit in tests/unit/test_prompts.py
- [X] T009 [P] [US1] Add CLI integration test that `GMUSE_MAX_CHARS` triggers non-zero exit when the generated message exceeds the limit in tests/integration/test_cli.py

### Implementation for User Story 1

- [X] T010 [US1] Extend prompt building to accept and embed an optional `max_chars` constraint in src/gmuse/prompts.py
- [X] T011 [US1] Update Conventional Commit task prompt generation to avoid conflicting length guidance when `max_chars` is set in src/gmuse/prompts.py
- [X] T012 [US1] Thread config `max_chars` into prompt generation flow (pass through to prompt builder) in src/gmuse/commit.py
- [X] T013 [US1] Use `max_chars` as the effective max length for validation when set (fallback to `max_message_length` when unset) in src/gmuse/commit.py
- [X] T014 [US1] Ensure `InvalidMessageError` surfaces as a non-zero CLI exit with an actionable message in src/gmuse/cli/main.py

**Checkpoint**: US1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Default behavior remains usable (Priority: P2)

**Goal**: Users who do not configure `max_chars` see no workflow breakage and no new required settings.

**Independent Test**: With no `max_chars` configured, `gmuse msg` works as before and prompt content does not include a max-chars rule.

- [X] T015 [P] [US2] Add unit test asserting default `max_chars=None` and no prompt rule is included when unset in tests/unit/test_prompts.py
- [X] T016 [P] [US2] Add regression coverage asserting validation uses `max_message_length` when `max_chars` is unset in tests/unit/test_commit.py

**Checkpoint**: US2 is verified; backwards compatibility is preserved.

---

## Phase 5: User Story 3 - Clear validation errors for invalid values (Priority: P3)

**Goal**: Invalid `max_chars` values fail fast with clear, actionable errors.

**Independent Test**: Setting `GMUSE_MAX_CHARS=0` or `GMUSE_MAX_CHARS=abc` causes a `ConfigError` explaining valid type and range.

- [X] T017 [P] [US3] Add unit tests for invalid `max_chars` values (non-integer, zero/negative, >500) in tests/unit/test_config.py
- [X] T018 [US3] Ensure `ConfigError` messages for invalid `max_chars` match the config contract examples in src/gmuse/config.py

**Checkpoint**: US3 is verified; config errors are actionable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and end-to-end verification.

- [X] T019 [P] Document `max_chars` (key, default, range, env var, interaction with `max_message_length`) in docs/source/reference/configuration.md
- [X] T020 [P] Add an entry for `GMUSE_MAX_CHARS` in docs/source/reference/configuration.md
- [ ] T021 Run the feature quickstart steps and ensure they remain accurate in specs/006-commit-message-max-chars/quickstart.md
- [ ] T022 Run final quality checks (`uv run nox -s check`) using noxfile.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup
- **User Stories (Phase 3+)**: Depend on Foundational
- **Polish (Phase 6)**: Depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational; delivers MVP.
- **US2 (P2)**: Depends on US1 implementation (logic exists) but is independently testable as a backward-compatibility slice.
- **US3 (P3)**: Depends on Foundational validation wiring; can proceed in parallel with US1 tests/implementation after Foundational.

---

## Parallel Execution Examples

### Parallel Example: User Story 1

These can be executed in parallel after Foundational completes:

- Task: T006 [US1] tests/unit/test_prompts.py
- Task: T007 [US1] tests/unit/test_prompts.py
- Task: T008 [US1] tests/unit/test_prompts.py
- Task: T009 [US1] tests/integration/test_cli.py

### Parallel Example: User Story 3

- Task: T017 [US3] tests/unit/test_config.py (tests)
- Task: T019 docs/source/reference/configuration.md (docs) *(can run in parallel once behavior is agreed, but should be finalized after implementation)*

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (T001)
2. Complete Phase 2 (T002–T005)
3. Implement and validate Phase 3 (T006–T014)
4. Stop and validate US1 independently before moving on

### Incremental Delivery

- Add US2 (T015–T016) for backward compatibility confidence
- Add US3 (T017–T018) for config UX robustness
- Finish docs and final checks (T019–T022)
