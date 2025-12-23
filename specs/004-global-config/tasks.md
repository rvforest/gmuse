---

description: "Task list for Global Config CLI implementation"
---

# Tasks: Global Config CLI

**Input**: Design documents from `/specs/004-global-config/`

- plan.md (required): `specs/004-global-config/plan.md`
- spec.md (required): `specs/004-global-config/spec.md`
- research.md: `specs/004-global-config/research.md`
- data-model.md: `specs/004-global-config/data-model.md`
- contracts/: `specs/004-global-config/contracts/`
- quickstart.md: `specs/004-global-config/quickstart.md`

**Tests**: Included (explicitly required by spec “User Scenarios & Testing” + Constitution Testing Standards).

## Format

Every task is a strict checklist item:

- [ ] T001 [P?] [US?] Description with file path

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US1] / [US2]**: Maps task to a user story

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Confirm CLI UX and outputs match spec in specs/004-global-config/spec.md
- [X] T002 [P] Add `tomlkit` runtime dependency in pyproject.toml
- [X] T003 [P] Create `config` Typer sub-app scaffold in src/gmuse/cli/config.py
- [X] T004 Register `config` subcommand group in src/gmuse/cli/main.py

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T005 Add `ALLOWED_CONFIG_KEYS` allowlist derived from `DEFAULTS` in src/gmuse/config.py
- [X] T006 Add `parse_config_value(key, raw)` for bool/int/float/optional-string parsing in src/gmuse/config.py
- [X] T007 Add safe raw-file loader (`load_config_raw`) in src/gmuse/config.py
- [X] T008 Add TOML round-trip helpers (load/update/write) using tomlkit in src/gmuse/config.py
- [X] T009 Implement atomic write helper (temp file + `os.replace`) in src/gmuse/config.py
- [X] T010 Fix config precedence so env overrides file (align `merge_config()` with CLI docstring) in src/gmuse/config.py
- [X] T011 [P] Add unit tests for merge precedence and parsing helpers in tests/unit/test_config.py

**Checkpoint**: After Phase 2, config read/write + precedence rules are stable, and user stories can be implemented.

---

## Phase 3: User Story 1 — View Global Config (Priority: P1) 🎯 MVP

**Goal**: Provide `gmuse config view` to display global config file location, raw file contents (if present), and an effective merged summary highlighting overrides from env/defaults.

**Independent Test**:
- Run `gmuse config view` with no config file and see a clear “no config file” message plus effective defaults.
- Create a config file with a few keys and run `gmuse config view` to see:
  - raw file contents
  - merged table
  - override warnings when `GMUSE_*` env vars supersede stored values

### Tests (US1)

- [X] T012 [P] [US1] Add unit tests for `gmuse config view` formatting and error handling in tests/unit/test_cli_config.py
- [X] T013 [P] [US1] Add integration test: no config file prints location + defaults in tests/integration/test_cli_config.py
- [X] T014 [P] [US1] Add integration test: existing config file prints contents + merged summary in tests/integration/test_cli_config.py
- [X] T015 [P] [US1] Add integration test: invalid TOML returns exit 1 with actionable error in tests/integration/test_cli_config.py
- [X] T016 [P] [US1] Add integration test: unreadable file returns exit 1 with actionable error in tests/integration/test_cli_config.py

### Implementation (US1)

- [X] T017 [US1] Implement `gmuse config view` command output contract in src/gmuse/cli/config.py
- [X] T018 [US1] Implement source tracking + override highlighting (env over file, default under both) in src/gmuse/cli/config.py
- [X] T019 [US1] Ensure `config view` does not import LLM/provider code (no network calls) in src/gmuse/cli/config.py

**Checkpoint**: US1 demoable: `gmuse config view` works end-to-end and passes tests.

---

## Phase 4: User Story 2 — Set Global Config Values (Priority: P2)

**Goal**: Provide `gmuse config set KEY VALUE` to persist validated config values into the global XDG config file, without deleting unrelated settings.

**Independent Test**:
- Run `gmuse config set format conventional` then `gmuse config view` and confirm the value persists.
- Attempt `gmuse config set unknown_key value` and confirm it errors (exit 1) with valid keys list.

### Tests (US2)

- [X] T020 [P] [US2] Add unit tests for `parse_config_value()` (bool/int/float/null parsing) in tests/unit/test_config_write.py
- [X] T021 [P] [US2] Add unit tests for key allowlist errors in tests/unit/test_cli_config.py
- [X] T022 [US2] Add integration test: `config set` creates directories + file when missing in tests/integration/test_cli_config.py
- [X] T023 [US2] Add integration test: `config set` then `config view` persists value in tests/integration/test_cli_config.py
- [X] T024 [US2] Add integration test: unknown key rejected with exit 1 in tests/integration/test_cli_config.py
- [X] T025 [US2] Add integration test: invalid value (range/choice) rejected with exit 1 in tests/integration/test_cli_config.py
- [X] T026 [US2] Add integration test: unwritable file returns exit 1 with actionable error in tests/integration/test_cli_config.py

### Implementation (US2)

- [X] T027 [US2] Implement `gmuse config set` command (args, validation, messages) in src/gmuse/cli/config.py
- [X] T028 [US2] Implement “preserve unrelated settings” TOML update behavior using tomlkit in src/gmuse/config.py
- [X] T029 [US2] Ensure `config set` rejects unknown keys (allowlist) and never stores credentials (env-only) in src/gmuse/cli/config.py
- [X] T030 [US2] Implement deterministic success output including file path in src/gmuse/cli/config.py

**Checkpoint**: US2 demoable: `gmuse config set` persists validated values and integrates with `view`.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T031 [P] Update docs to include `gmuse config view/set` examples in docs/source/how_to/configuration.md
- [X] T032 [P] Update configuration reference docs for new commands in docs/source/reference/configuration.md
- [X] T033 [P] Ensure CLI help text and examples are accurate in src/gmuse/cli/config.py
- [X] T034 Run formatting + lint checks (Ruff) for changed files in pyproject.toml
- [X] T035 Run tests for this feature (unit + integration) in tests/

---

## Dependencies & Execution Order

### Dependency Graph (User Story Completion Order)

- Phase 1 (Setup) → Phase 2 (Foundational) → US1 (P1) → US2 (P2) → Polish

Notes:
- US2 depends on the same foundational read/write utilities as US1.
- US2 is easiest to verify after US1 exists (spec acceptance uses “set then view”).

### Parallel Opportunities

- Setup: T002, T003 can run in parallel.
- Foundational: T011 can run in parallel once T010 is ready.
- US1 tests T012–T016 can run in parallel.
- US2 tests T020–T021 can run in parallel; integration tests can be split across team members if separated into different files.
- Polish docs tasks T031–T033 can run in parallel.

---

## Parallel Example: User Story 1

- Run these in parallel:
  - T012 (tests/unit/test_cli_config.py)
  - T013–T016 (tests/integration/test_cli_config.py) split into separate files if needed for true parallelism
- Then implement:
  - T017–T019 (src/gmuse/cli/config.py)

---

## Parallel Example: User Story 2

- Run these in parallel:
  - T020 (tests/unit/test_config_write.py)
  - T021 (tests/unit/test_cli_config.py)
- Then implement:
  - T027 (src/gmuse/cli/config.py)
  - T028 (src/gmuse/config.py)

---

## Implementation Strategy

### MVP Scope (Recommended)

Implement **US1 only** first:
1. Phase 1 Setup
2. Phase 2 Foundational
3. Phase 3 US1
4. Validate via `gmuse config view` acceptance scenarios

### Incremental Delivery

- Add US2 after US1 is stable and released.
- Finish with Polish tasks to ensure docs/help/tests are complete.
