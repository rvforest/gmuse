---

description: "Task list for implementing `gmuse msg --dry-run`"
---

# Tasks: `gmuse msg --dry-run` (print prompt without calling LLM)

**Input**: Design documents from `/specs/003-msg-dry-run/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), plus `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Included (explicitly requested in `spec.md`).

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm existing code paths and test harness patterns to keep changes minimal.

- [X] T001 [P] Review current `gmuse msg` flow in src/gmuse/cli/main.py and src/gmuse/commit.py
- [X] T002 [P] Review prompt construction API in src/gmuse/prompts.py and confirm output layout in specs/003-msg-dry-run/contracts/cli.md
- [X] T003 [P] Review existing CLI test patterns in tests/integration/test_cli.py and tests/unit/test_cli_main.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create a single reusable formatter so behavior + tests share one source of truth.

- [X] T004 Create `_format_dry_run_output(model, format, truncated, system_prompt, user_prompt)` helper in src/gmuse/cli/main.py

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 3: User Story 1 - Preview prompt (Priority: P1) 🎯 MVP

**Goal**: `gmuse msg --dry-run` prints the exact prompt that would be sent to the LLM (plus metadata) and never calls a provider.

**Independent Test**: In a repo with staged changes, run `gmuse msg --dry-run` and verify stdout contains `MODEL:`, `FORMAT:`, `TRUNCATED:`, `SYSTEM PROMPT:`, and `USER PROMPT:`; verify exit code is 0 and no provider client methods are invoked.

### Tests for User Story 1 (write first; ensure they FAIL before implementation)

- [X] T005 [P] [US1] Add unit tests for `_format_dry_run_output` in tests/unit/test_cli_msg_dry_run.py
- [X] T006 [P] [US1] Add integration test for `gmuse msg --dry-run` stdout layout in tests/integration/test_cli_dry_run_integration.py
- [X] T007 [P] [US1] Add unit test asserting `gmuse.llm.LLMClient.generate` is NOT called during dry-run in tests/unit/test_cli_msg_dry_run.py

### Implementation for User Story 1

- [X] T008 [US1] Add `--dry-run` option to `msg` command signature/help in src/gmuse/cli/main.py
- [X] T009 [US1] Implement dry-run execution path in src/gmuse/cli/main.py (call `gather_context()`, `build_prompt()`, print metadata + prompts, exit 0)
- [X] T010 [US1] Ensure dry-run path does NOT call `generate_message()` (and therefore never initializes `LLMClient`) in src/gmuse/cli/main.py
- [X] T011 [US1] Ensure `TRUNCATED: true|false` reflects `context.diff_was_truncated` and truncation warning still goes to stderr in src/gmuse/cli/main.py
- [X] T012 [US1] Add CLI docstring example including `gmuse msg --dry-run` in src/gmuse/cli/main.py
- [X] T013 [US1] Run tests for MVP story via `uv run nox -s test` (see noxfile.py)

**Checkpoint**: US1 complete — dry-run works and is independently testable.

---

## Phase 4: User Story 2 - CLI discoverability and docs (Priority: P2)

**Goal**: Users can discover and understand `--dry-run` from help and documentation.

**Independent Test**: Run `gmuse msg --help` and confirm `--dry-run` appears; confirm docs contain a `--dry-run` example and describe output layout.

### Implementation for User Story 2

- [X] T014 [P] [US2] Update docs usage example in docs/source/getting_started/quickstart.md
- [X] T015 [P] [US2] Document `--dry-run` flag and output layout in docs/source/reference/cli.md
- [X] T016 [P] [US2] Add a short mention of `gmuse msg --dry-run` in README.md
- [X] T017 [US2] Build docs via `uv run nox -s docs` (see noxfile.py)

**Checkpoint**: US2 complete — help + docs are updated.

---

## Phase 5: User Story 3 - Safe integration with other options (Priority: P3)

**Goal**: `--dry-run` remains correct when combined with other flags and still never calls a provider.

**Independent Test**: Run `gmuse msg --dry-run --hint "x" --format conventional --model "m"` and confirm header fields match inputs and user prompt includes the hint; confirm no provider calls occur.

### Tests for User Story 3

- [X] T018 [P] [US3] Add unit tests covering combinations (`--hint`, `--format`, `--model`, `--history-depth`) in tests/unit/test_cli_msg_dry_run.py
- [X] T019 [P] [US3] Add unit test ensuring `--copy` does not copy anything during dry-run in tests/unit/test_cli_msg_dry_run.py
- [X] T020 [P] [US3] Add unit test verifying `TRUNCATED: true` when `context.diff_was_truncated=True` (monkeypatch `gather_context`) in tests/unit/test_cli_msg_dry_run.py

### Implementation for User Story 3

- [X] T021 [US3] Ensure dry-run passes `--history-depth` through to `gather_context()` and prompt builder inputs in src/gmuse/cli/main.py
- [X] T022 [US3] Run focused tests via `uv run nox -s test` (see noxfile.py)

**Checkpoint**: US3 complete — dry-run is robust with flag combinations.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Keep quality gates green and ensure docs/examples stay consistent.

- [X] T023 [P] Run lint/format/type gates via `uv run nox -s check` (see noxfile.py)

---

## Dependencies & Execution Order

### User Story Dependencies (graph)

- US1 → {US2, US3}
- US2 → (none)
- US3 → (none)

Interpretation: US2 and US3 depend on US1 being implemented (they validate docs and combinations of the dry-run behavior).

### Phase Dependencies

- Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1)
- Phase 3 (US1) → Phase 4 (US2) and Phase 5 (US3) (can proceed in parallel)
- Phase 6 (Polish) after all desired stories

---

## Parallel Opportunities

- Setup tasks T001–T003 are parallelizable.
- Within US1: T005–T007 can be written in parallel (different test concerns/files).
- Within US2: T014–T016 are parallelizable (different docs files).
- Within US3: T018–T020 are parallelizable (independent unit test additions).

---

## Parallel Example: User Story 1

- Task: T005 Add unit tests for formatter in tests/unit/test_cli_msg_dry_run.py
- Task: T006 Add integration test for CLI stdout layout in tests/integration/test_cli_msg_dry_run.py
- Task: T007 Add unit test asserting no `LLMClient.generate` call in tests/unit/test_cli_msg_dry_run.py

## Parallel Example: User Story 2

- Task: T014 Update docs quickstart example in docs/source/getting_started/quickstart.md
- Task: T015 Update CLI reference in docs/source/reference/cli.md
- Task: T016 Update README mention in README.md

## Parallel Example: User Story 3

- Task: T018 Add combination flag tests in tests/unit/test_cli_msg_dry_run.py
- Task: T019 Add `--copy` no-op test in tests/unit/test_cli_msg_dry_run.py
- Task: T020 Add truncation header correctness test in tests/unit/test_cli_msg_dry_run.py

---

## Implementation Strategy

### MVP First (User Story 1 Only)

- Complete T001–T013, then validate the CLI output + “no provider calls” invariant.

### Incremental Delivery

- Deliver US1 first (core feature), then US2 (docs), then US3 (combination robustness).
