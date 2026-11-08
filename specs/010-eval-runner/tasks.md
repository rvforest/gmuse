# Tasks: Production-Path Eval Runner

**Input**: Design documents from `/specs/010-eval-runner/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/runner-cli.md`, `contracts/result-artifacts.md`, `quickstart.md`

**Tests**: Tests are required by the feature specification, implementation plan, and project constitution. Write each story's tests first and verify they fail before implementing that story.

**Organization**: Tasks are grouped by user story so check mode, production execution, result inspection, and normal-user isolation can each be implemented and tested as a distinct increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel after the preceding dependency checkpoint because it changes different files and does not depend on another incomplete task in the same group
- **[Story]**: Maps a task to a user story from `spec.md`
- Every task names the exact repository file or directory it changes or validates

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add maintainer-only Inspect tooling without changing gmuse's normal runtime dependency path.

- [X] T001 Add `inspect-ai` to the development dependency group in `pyproject.toml` and refresh the resolved dependency graph in `uv.lock`
- [X] T002 [P] Ignore generated Inspect logs, run directories, and debug artifacts under `.gmuse-evals/` in `.gitignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Expose an observable production-generation attempt without changing the existing `generate_message()` contract.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Add failing unit coverage for prompt metadata, injected deterministic responses, preserved invalid output, operational failures, and unchanged `generate_message()` raising behavior in `tests/unit/test_commit_attempt.py`
- [X] T004 Add typed `GenerationPromptMetadata`, `ValidationOutcome`, and `GenerationAttemptResult` records plus SHA-256 prompt hashing, byte sizing, prompt-version capture, and token estimation in `src/gmuse/commit.py` using the existing constants and helpers in `src/gmuse/prompts.py`
- [X] T005 Implement a typed response-generation injection seam and `generate_message_attempt()` in `src/gmuse/commit.py`, then refactor `generate_message()` to delegate to it while preserving the current public result and exception behavior

**Checkpoint**: The same production prompt, provider boundary, and validation behavior can now be observed by eval tooling without altering normal generation.

---

## Phase 3: User Story 1 - Check An Eval Run Before Live Provider Calls (Priority: P1) 🎯 MVP

**Goal**: Resolve and display one validated suite, execute it through Inspect with deterministic local output, write Inspect logs, and guarantee zero provider calls.

**Independent Test**: Run `uv run python -m tools.evals.gmuse_evals run --mode check --suite smoke`; every selected case/config entry is reconstructed and logged exactly once, effective settings and the log location are displayed, and a provider spy records zero calls. Unknown, empty, or invalid suites fail before any completed sample result is written.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests first and verify they fail before implementation.**

- [X] T006 [P] [US1] Add failing run-plan tests for check-mode suite validation, case/format expansion, stable entry IDs, forbidden models, empty selections, sample limits, and conflicting log locations in `tests/unit/test_eval_runner_plan.py`
- [X] T007 [P] [US1] Add failing Inspect adapter tests for one sample per check entry, stable fixture/rubric metadata, deterministic candidate markers, and a solver path that never constructs a provider client in `tests/unit/test_eval_runner_inspect_tasks.py`
- [X] T008 [P] [US1] Add failing CLI/integration tests for successful smoke checks, displayed effective settings, Inspect log creation, zero provider calls, invalid fixture rejection, and no completed results for unknown or empty suites in `tests/integration/test_eval_runner_check.py`

### Implementation for User Story 1

- [X] T009 [P] [US1] Implement the built-in `format_valid_v1` deterministic output policy for freeform, conventional, and gitmoji cases in `tools/evals/gmuse_evals/deterministic.py`
- [X] T010 [P] [US1] Implement independent default Inspect log identities under `.gmuse-evals/inspect/`, explicit `--log-dir` creation, and pre-execution conflict detection in `tools/evals/gmuse_evals/logs.py`
- [X] T011 [US1] Implement typed check-mode `EvalRun`, `RunPlan`, `RunEntry`, guardrail, and effective-generation-config resolution from `validate_suite()` results in `tools/evals/gmuse_evals/runner.py`
- [X] T012 [US1] Execute each check entry inside `reconstruct_fixture()`, verify a non-empty staged diff/digest, invoke `generate_message_attempt()` with the deterministic response seam, and clean up temporary repositories on success and failure in `tools/evals/gmuse_evals/execution.py`
- [X] T013 [US1] Build the Inspect dataset, task, and production-path solver for check entries and emit one framework result per reached entry in `tools/evals/gmuse_evals/inspect_tasks.py`
- [X] T014 [US1] Add the Typer `run` command with required `--mode`/`--suite`, check-mode option validation, plan rendering, Inspect orchestration, and actionable pre-execution errors in `tools/evals/gmuse_evals/cli.py`

**Checkpoint**: Check mode is a complete offline MVP that validates fixtures, exercises production plumbing, and produces Inspect evidence without credentials or provider calls.

---

## Phase 4: User Story 2 - Generate Outputs Through Gmuse Production Behavior (Priority: P1)

**Goal**: Execute every fixture/model/config entry in an isolated repository through gmuse's real git, context, prompt, generation, and validation behavior, including guarded live runs.

**Independent Test**: Execute a tiny validated suite with deterministic and injected live responses; the observed staged diff, history, branch context, hint, repository instructions, format, `max_chars`, model, temperature, and token cap match the effective entry config, temporary repositories are cleaned up, and invalid raw messages remain available alongside failed production validation.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests first and verify they fail before implementation.**

- [X] T015 [P] [US2] Add failing unit tests for config precedence, case/format/model matrix expansion, repository reconstruction, staged-diff verification, temporary-repository cleanup, and raw invalid-message preservation in `tests/unit/test_eval_runner_execution.py`
- [X] T016 [P] [US2] Add failing production-path integration tests for history, sanitized branch context, hints, fixture/override repository instructions, `max_chars`, model, temperature, token limits, and no-staged-diff setup failures in `tests/integration/test_eval_runner_production_path.py`
- [X] T017 [P] [US2] Add failing live CLI tests for repeatable `--model`, plan/sample counts, required guardrails, limit overflow, interactive confirmation, `--yes`, cancellation, and zero calls before successful preflight in `tests/integration/test_eval_runner_live.py`

### Implementation for User Story 2

- [X] T018 [US2] Expand `RunPlan` construction to resolve suite/case defaults and CLI overrides for format, history depth, branch inclusion, hint, repository instructions, `max_chars`, model, temperature, and token cap across the case/model/config matrix in `tools/evals/gmuse_evals/runner.py`
- [X] T019 [US2] Extend case execution to gather production context from the reconstructed repository, apply the complete effective config, invoke live or injected generation through `generate_message_attempt()`, preserve raw invalid messages, and always clean up unless debug preservation is requested in `tools/evals/gmuse_evals/execution.py`
- [X] T020 [P] [US2] Extend the Inspect task/solver to execute live-model entries through the production attempt path while keeping check entries on deterministic local output in `tools/evals/gmuse_evals/inspect_tasks.py`
- [X] T021 [P] [US2] Implement live-mode model requirements, plan and guardrail display, sample/token/cost limits, interactive confirmation or `--yes`, and fail-closed preflight behavior in `tools/evals/gmuse_evals/cli.py`

**Checkpoint**: Check and guarded live runs both evaluate gmuse's production behavior, and received messages are retained even when deterministic validation rejects them.

---

## Phase 5: User Story 3 - Inspect Durable Result Logs (Priority: P1)

**Goal**: Make Inspect logs the canonical durable artifact with complete versioned gmuse run/sample metadata, privacy-safe prompt observations, operational error categories, and maintainer summaries.

**Independent Test**: Run a multi-entry suite with valid, invalid, timeout, authentication, context-length, and empty injected outcomes; the Inspect log contains exactly one result per reached entry, all required run/sample fields and summary counts, raw invalid outputs, separate operational errors, prompt hashes/sizes/token estimates, no raw prompts by default, and the reported log location.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests first and verify they fail before implementation.**

- [X] T022 [P] [US3] Add failing contract tests for every run-level and sample-level field, schema version, candidate kind, validation state, forbidden judge/baseline fields, and raw-prompt exclusion from `specs/010-eval-runner/contracts/result-artifacts.md` in `tests/contract/test_eval_runner_artifacts.py`
- [X] T023 [P] [US3] Add failing unit tests for stable error classification, JSON-compatible metadata builders, summary aggregation, prompt privacy, and debug-path separation in `tests/unit/test_eval_runner_artifacts.py`
- [X] T024 [P] [US3] Add failing integration tests that parse Inspect logs for multi-case/model/config completeness, invalid-output retention, per-entry operational failures, continued execution, summary counts, and log locations in `tests/integration/test_eval_runner_logs.py`

### Implementation for User Story 3

- [X] T025 [US3] Implement typed `OperationalError` categories and deterministic translation for authentication, rate limit, timeout, network, context-length, empty-response, fixture-setup, and unknown failures in `tools/evals/gmuse_evals/errors.py`
- [X] T026 [US3] Implement versioned run/sample metadata builders and `RunSummary` aggregation for identities, effective config, staged-diff digest, context/prompt metadata, validation, timing, guardrails, and operational errors in `tools/evals/gmuse_evals/logs.py`
- [X] T027 [US3] Attach complete gmuse metadata to Inspect runs and sample results, preserve generated output on validation failure, and continue safely after per-entry operational failures in `tools/evals/gmuse_evals/inspect_tasks.py`
- [X] T028 [US3] Implement opt-in `--preserve-debug` handling that stores raw prompts and preserved repositories only under separate `.gmuse-evals/debug/` paths while ordinary logs remain prompt-free in `tools/evals/gmuse_evals/execution.py` and `tools/evals/gmuse_evals/logs.py`
- [X] T029 [US3] Aggregate completed, validation-passed, validation-failed, and operational-error counts from Inspect results and render the final status plus canonical log locations in `tools/evals/gmuse_evals/runner.py` and `tools/evals/gmuse_evals/cli.py`

**Checkpoint**: Inspect logs and summaries contain the complete privacy-safe handoff contract for future scoring and strict comparison work without implementing either feature.

---

## Phase 6: User Story 4 - Keep Eval Tooling Isolated From Normal Users (Priority: P2)

**Goal**: Keep Inspect, fixtures, commands, logs, credentials, and live-call behavior out of ordinary `gmuse msg` use and default repository automation.

**Independent Test**: Install/import and run normal gmuse generation with no Inspect installation or provider credentials and observe unchanged behavior with no `.gmuse-evals/` output; run the offline eval test/session explicitly and verify default GitHub workflows expose no eval live-call command.

### Tests for User Story 4 ⚠️

> **NOTE: Write these tests first and verify they fail before implementation.**

- [X] T030 [P] [US4] Add regression tests proving `gmuse msg` does not import Inspect, load eval assets, or create `.gmuse-evals/` artifacts and retains its existing generation behavior in `tests/integration/test_eval_runner_isolation.py`
- [X] T031 [P] [US4] Add contract checks that Inspect remains outside `[project].dependencies` and no default workflow under `.github/workflows/` invokes a live eval runner in `tests/contract/test_eval_runner_automation.py`

### Implementation for User Story 4

- [X] T032 [P] [US4] Add a local-only `evals-check` nox session that runs the smoke suite in check mode with a temporary Inspect log directory and no credentials in `noxfile.py`
- [X] T033 [US4] Keep Inspect imports and runner orchestration confined to `tools/evals/gmuse_evals/inspect_tasks.py` and `tools/evals/gmuse_evals/runner.py`, using lazy imports where needed so validation tooling and `src/gmuse/` remain usable without Inspect
- [X] T034 [P] [US4] Document maintainer-only installation, validation, check/live commands, guardrails, privacy defaults, and the absence of default live CI in `docs/source/development/contributing.md`

**Checkpoint**: Eval execution is explicit maintainer tooling, while normal packaging, commands, imports, and credential-free automated checks remain unchanged.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete feature across its documented offline workflow and repository quality gates.

- [X] T035 Run the focused suites in `tests/unit/test_commit_attempt.py`, `tests/unit/test_eval_runner_plan.py`, `tests/unit/test_eval_runner_inspect_tasks.py`, `tests/unit/test_eval_runner_execution.py`, `tests/unit/test_eval_runner_artifacts.py`, `tests/contract/test_eval_runner_artifacts.py`, `tests/contract/test_eval_runner_automation.py`, `tests/integration/test_eval_runner_check.py`, `tests/integration/test_eval_runner_production_path.py`, `tests/integration/test_eval_runner_live.py`, `tests/integration/test_eval_runner_logs.py`, and `tests/integration/test_eval_runner_isolation.py`
- [X] T036 Run formatting, linting, type checking, and the full regression suite for `src/gmuse/commit.py`, `tools/evals/gmuse_evals/`, `tests/`, `pyproject.toml`, and `noxfile.py` with `uv run nox -s check` and `uv run nox -s test`
- [X] T037 Execute the check-mode and debug-preservation walkthroughs from `specs/010-eval-runner/quickstart.md`, inspect the resulting `.gmuse-evals/inspect/` metadata, and verify zero provider calls and cleanup/privacy expectations

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; T001 and T002 can run concurrently.
- **Foundational (Phase 2)**: Depends on Setup and blocks every user story.
- **User Story 1 (Phase 3)**: Depends on Foundational and delivers the offline MVP.
- **User Story 2 (Phase 4)**: Depends on User Story 1's run-plan, execution, Inspect, and CLI skeletons; it extends the same path to full config fidelity and guarded live generation.
- **User Story 3 (Phase 5)**: Depends on User Stories 1 and 2 so metadata and errors cover both check and live outcomes.
- **User Story 4 (Phase 6)**: Depends on the completed runner surface it isolates; its test tasks can be drafted after Foundational while implementation validation follows the P1 stories.
- **Polish (Phase 7)**: Depends on all selected user stories.

### User Story Dependency Graph

```text
Setup → Foundational → US1 (offline check MVP) → US2 (production/live path) → US3 (durable logs)
                         └──────────────────────────────────────────────→ US4 (isolation)
All selected stories → Polish
```

### Within Each User Story

- Write all listed tests first and verify they fail for the expected missing behavior.
- Resolve suite/case/config identities before executing repositories.
- Reconstruct and verify repositories before production generation.
- Produce per-entry results before aggregating summaries.
- Complete the story's independent test before starting its dependent story.

## Parallel Opportunities

- T001 and T002 can run in parallel.
- US1 tests T006-T008 can run in parallel; after they exist, T009 and T010 can run in parallel.
- US2 tests T015-T017 can run in parallel; after T018-T019, T020 and T021 can run in parallel.
- US3 tests T022-T024 can run in parallel.
- US4 tests T030-T031 can run in parallel; T032 and T034 can run in parallel after the runner interface stabilizes.
- Once the P1 production surface is stable, US4 isolation validation can proceed alongside US3 metadata work because their implementation files do not overlap except at final CLI verification.

## Parallel Example: User Story 1

```text
Task T006: Write run-plan tests in tests/unit/test_eval_runner_plan.py
Task T007: Write Inspect task tests in tests/unit/test_eval_runner_inspect_tasks.py
Task T008: Write check-mode integration tests in tests/integration/test_eval_runner_check.py

Then in parallel:
Task T009: Implement deterministic output in tools/evals/gmuse_evals/deterministic.py
Task T010: Implement log identity handling in tools/evals/gmuse_evals/logs.py
```

## Parallel Example: User Story 2

```text
Task T015: Write execution unit tests in tests/unit/test_eval_runner_execution.py
Task T016: Write production-path integration tests in tests/integration/test_eval_runner_production_path.py
Task T017: Write live preflight tests in tests/integration/test_eval_runner_live.py

After T018 and T019:
Task T020: Add live Inspect orchestration in tools/evals/gmuse_evals/inspect_tasks.py
Task T021: Add live CLI safeguards in tools/evals/gmuse_evals/cli.py
```

## Parallel Example: User Story 3

```text
Task T022: Write artifact contract tests in tests/contract/test_eval_runner_artifacts.py
Task T023: Write artifact/error unit tests in tests/unit/test_eval_runner_artifacts.py
Task T024: Write Inspect log integration tests in tests/integration/test_eval_runner_logs.py
```

## Parallel Example: User Story 4

```text
Task T030: Write normal-generation isolation tests in tests/integration/test_eval_runner_isolation.py
Task T031: Write dependency/workflow contract tests in tests/contract/test_eval_runner_automation.py

Then in parallel:
Task T032: Add the local evals-check session in noxfile.py
Task T034: Document the maintainer workflow in docs/source/development/contributing.md
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup and Foundational.
2. Complete User Story 1 through T014.
3. Run the independent smoke check and prove zero provider calls.
4. Stop here for the smallest safe, useful runner increment.

### Incremental Delivery

1. **US1**: Ship deterministic check mode and Inspect plumbing.
2. **US2**: Add full production config fidelity and guarded live generation.
3. **US3**: Complete durable metadata, privacy, error, and summary contracts.
4. **US4**: Prove and document normal-user/runtime/automation isolation.
5. **Polish**: Run the quickstart and all repository quality gates.

## Notes

- `[P]` means different files and no dependency on another incomplete task in the same parallel group.
- Inspect logs are canonical; do not add bespoke `run-plan.json`, `outputs.jsonl`, or `summary.json` artifacts unless a demonstrated Inspect metadata gap requires a compact sidecar.
- Do not add judge scoring, aggregate quality scores, resume accounting, baselines, importers, or benchmark recommendations.
- Keep raw prompts out of ordinary logs and keep generated messages even when production validation fails.
- Commit after each task or coherent task group, and validate at every checkpoint.

## Checkpoint verification (2026-11-07)

- `uv run --frozen nox -s test`: 663 tests passed on each of Python 3.10,
  3.11, 3.12, 3.13, and 3.14.
- `uv run --frozen nox -s check`: all quality hooks passed, including newly
  staged tests.
- `uv run --frozen nox -s evals-check`: five offline samples passed.
- Check and debug quickstart runs: five samples each, prompt hashes present,
  raw prompts absent from sample metadata; debug prompts and repository copies
  stored separately under ignored `.gmuse-evals/debug/`.
- Live run limits: require a positive sample cap and serialize execution.
  Reject token, cost, and wall-clock run limits because Inspect cannot enforce
  them across direct gmuse provider calls. Per-response `--max-tokens` remains
  available. Added regression coverage for rejected limits and actual attempt
  counts with an injected live response; no paid provider calls were made.
- Corrected the nox session name/environment and the smoke live examples
  (five entries per model).
- `uv run --frozen nox -s docs -- -E`: clean rebuild passed without the old
  local navbar fallback. Preserved that unrelated, unnecessary template at
  `.gmuse-evals/recovery/navbar-logo.html` instead of shipping it.
