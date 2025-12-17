# Tasks: zsh completions for gmuse

**Branch**: `002-zsh-completions` | **Spec**: [specs/002-zsh-completions/spec.md](specs/002-zsh-completions/spec.md)
**Status**: Complete

## Phase 1: Setup
*Goal: Initialize project structure for the new feature.*

- [x] T001 Create `src/gmuse/cli/completions.py` with initial command group and register in `src/gmuse/cli/main.py`
- [x] T002 Create test files `tests/unit/test_cli_completions.py` and `tests/integration/test_completions_run.py`

## Phase 2: Foundational
*Goal: Establish core data structures and shared utilities.*

- [x] T003 Define `CompletionRequest` and `CompletionResponse` data structures in `src/gmuse/cli/completions.py`

## Phase 3: User Story 1 - Emit zsh completion script
*Goal: Allow users to generate the zsh completion script.*

- [x] T004 [US1] Define Zsh completion script template in `src/gmuse/cli/completions.py` (implementing `_gmuse`)
- [x] T005 [US1] Implement `gmuse completions zsh` command to print the template to stdout
- [x] T006 [US1] Add unit test for `gmuse completions zsh` output in `tests/unit/test_cli_completions.py`

## Phase 4: User Story 2 - Generate suggestion when -m has no user-provided text
*Goal: Core functionality - generate commit message from staged changes.*

- [x] T007 [P] [US2] Implement `gmuse completions-run` CLI skeleton with arguments in `src/gmuse/cli/completions.py`
- [x] T008 [P] [US2] Implement logic to fetch staged diff using `gmuse.git` in `src/gmuse/cli/completions.py`
- [x] T009 [P] [US2] Implement logic to call LLM and format response as JSON in `src/gmuse/cli/completions.py`
- [x] T010 [US2] Handle "no staged changes" case (return status `no_staged_changes`) in `src/gmuse/cli/completions.py`
- [x] T011 [US2] Update Zsh template to call `gmuse completions-run` and parse JSON output using `sed`/`awk`
- [x] T012 [US2] Update Zsh template to show warning for `no_staged_changes` using `_message`
- [x] T013 [US2] Add unit tests for `completions-run` (mocking git/llm) in `tests/unit/test_cli_completions.py`
- [x] T014 [US2] Add integration test for `completions-run` output format in `tests/integration/test_completions_run.py`

## Phase 5: User Story 3 - Generate suggestion using a partial hint
*Goal: Support partial hints to guide generation.*

- [x] T015 [P] [US3] Update `completions-run` to handle `--hint` argument in `src/gmuse/cli/completions.py`
- [x] T016 [P] [US3] Update LLM prompt generation to include hint in `src/gmuse/cli/completions.py`
- [x] T017 [US3] Update Zsh template to capture current word as hint and pass to runtime
- [x] T018 [US3] Add unit tests for hint handling in `tests/unit/test_cli_completions.py`

## Phase 6: User Story 4 - Timeout and fallback behavior
*Goal: Ensure reliability and graceful degradation.*

- [x] T019 [P] [US4] Implement timeout enforcement in `completions-run` (Python side) in `src/gmuse/cli/completions.py`
- [x] T020 [P] [US4] Implement error handling for offline/API errors (return status `offline`/`error`) in `src/gmuse/cli/completions.py`
- [x] T021 [US4] Update Zsh template to handle non-ok statuses gracefully
- [x] T022 [US4] Add tests for timeout and error scenarios in `tests/unit/test_cli_completions.py`

## Phase 7: User Story 5 - User opt-out and configuration
*Goal: Provide user control and performance optimization.*

- [x] T023 [US5] Update Zsh template to check `GMUSE_COMPLETIONS_ENABLED`
- [x] T024 [US5] Implement Zsh-side caching (`_store_cache`, `_retrieve_cache`, cache policy) in template
- [x] T025 [US5] Pass `GMUSE_COMPLETIONS_TIMEOUT` to runtime helper in Zsh template
- [x] T026 [US5] Add tests for configuration logic in `tests/unit/test_cli_completions.py`

## Phase 8: Polish
*Goal: Final cleanup and verification.*

- [x] T027 Review and update help text for new commands in `src/gmuse/cli/completions.py`
- [x] T028 Update installation instructions to use eval-based approach

## Phase 9: Eval-based Installation Update
*Goal: Simplify installation by using `eval "$(gmuse completions zsh)"` approach.*

- [x] T029 Update spec.md, quickstart.md, research.md, plan.md for eval approach
- [x] T030 Update ZSH_COMPLETION_TEMPLATE installation comments
- [x] T031 Update docs/source/getting_started/completions.md
- [x] T032 Update tests to verify new installation instructions

## Dependencies

- **US1** (Emit Script) is independent.
- **US2** (Runtime) depends on Setup and Foundational.
- **US3** (Hint), **US4** (Timeout), **US5** (Config) depend on US2 (Runtime).
- **US3**, **US4**, **US5** can be developed in parallel after US2.

## Parallel Execution Examples

- **US2**: T007 (CLI skeleton), T008 (Git logic), and T009 (LLM logic) can be implemented in parallel.
- **US3/US4**: T015 (Hint arg) and T019 (Timeout logic) can be implemented in parallel.

## Implementation Strategy

1.  **MVP (US1 + US2)**: Deliver the ability to generate the script and get a basic suggestion. This provides immediate value.
2.  **Enhancement (US3)**: Add hint support for better control.
3.  **Reliability (US4)**: Add timeouts and error handling.
4.  **Optimization (US5)**: Add caching and configuration.
