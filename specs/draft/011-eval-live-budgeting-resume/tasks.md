# Tasks: Eval Live Guardrails

**Inputs**: [Spec](spec.md), [plan](plan.md), [research](research.md),
[data model](data-model.md), [contracts](contracts/), and [quickstart](quickstart.md).

Use the existing spec 010 runner and mocked providers. Tasks marked [P] can
run in parallel with other work in separate files once their prerequisites
are complete.

## Phase 1 — Setup

- [ ] T001 Run the existing live, check, and automation tests in `tests/integration/test_eval_runner_live.py`, `tests/integration/test_eval_runner_check.py`, and `tests/contract/test_eval_runner_automation.py` to establish the runner baseline.
- [ ] T002 Align the option names and supported limits in `specs/draft/011-eval-live-budgeting-resume/contracts/live-run-cli.md` and `specs/draft/011-eval-live-budgeting-resume/quickstart.md` with the merged CLI. Keep `--limit-time` and `--concurrency`; document the direct provider path's required sample cap and its existing rejection of unsupported limits.

## Phase 2 — Foundation

- [ ] T003 Separate read-only log destination resolution from directory creation in `tools/evals/gmuse_evals/logs.py` so preview and execution use the same destination rules. Preserve existing execution behavior.
- [ ] T004 [P] Verify shared plan fields and validation of empty selections, unsupported limits, and over-cap matrix counts in `tests/unit/test_eval_runner_plan.py`. Keep offline check-mode truncation covered.

## Phase 3 — US1: Preview Live Eval Work Before Calls (P1)

**Independent test** — A valid live `--plan` displays suite identity, cases,
models, counts, settings, limits, and log destination with zero provider calls
and no live sample results.

- [ ] T005 [P] [US1] Add a CLI integration test in `tests/integration/test_eval_live_guardrails.py` that asserts the preview fields, no confirmation prompt, and zero Inspect runner calls or live output, including for a new log directory.
- [ ] T006 [US1] Add `--plan` and execution-mode display in `tools/evals/gmuse_evals/cli.py`. Reuse the validated plan, effective settings display, and shared log destination lookup. Return before confirmation and Inspect execution for a plan-only invocation.

## Phase 4 — US2: Require Confirmation And Guardrails (P1)

**Independent test** — Mock the provider and assert zero calls for invalid
fixtures, empty selections, missing or invalid limits, over-cap plans, declined
confirmation, and non-interactive runs without `--yes`. Assert successful
interactive and `--yes` runs display the plan before execution.

- [ ] T007 [P] [US2] Extend `tests/integration/test_eval_runner_live.py` with mocked provider call-order and rejection cases, including `--yes` with missing or exceeded limits.
- [ ] T008 [US2] Enforce the terminal/confirmation rules after preflight and before calling Inspect in `tools/evals/gmuse_evals/cli.py`. Give non-interactive callers actionable `--yes` guidance and keep limit checks mandatory.
- [ ] T009 [P] [US2] Verify in `tests/contract/test_eval_runner_automation.py` that default repository automation stays offline and credential-free.

## Phase 5 — US3: Preserve Inspect Logs During Interruption (P2)

**Independent test** — Interrupt a mocked bounded run after a sample completes,
then read that sample and its generated message from the local Inspect log.

- [ ] T010 [US3] Add an interruption scenario using the pinned Inspect version in `tests/integration/test_eval_runner_logs.py`. Verify completed sample evidence remains readable after interruption.
- [ ] T011 [US3] If T010 exposes a gap, adjust native Inspect log handling in `tools/evals/gmuse_evals/inspect_runner.py` and rerun the interruption scenario.

## Phase 6 — US4: Avoid Repeating Work When Framework Support Is Clean (P2)

**Independent test** — With reuse enabled, compatible verified entries are
skipped and mismatched or unverifiable entries are ineligible before provider
calls. With reuse unavailable, reruns still enforce ordinary guardrails and
confirmation.

- [ ] T012 [US4] Time-box a spike on the pinned Inspect version and record the decision in `specs/draft/011-eval-live-budgeting-resume/research.md`. Require per-entry verification before calls and preserve earlier generated messages. If Inspect needs a custom ledger or cannot verify the inputs, defer reuse and validate the bounded rerun scenario in T015.
- [ ] T013 [US4] If the spike passes, add matching and mismatch cases in `tests/integration/test_eval_live_reuse.py`. Cover changed settings, same IDs with changed staged diff or prompt, missing or unverifiable hashes, and corrupt logs. Verify prior logs remain intact.
- [ ] T014 [US4] If the spike passes, wire the native Inspect reuse adapter into `tools/evals/gmuse_evals/inspect_runner.py` and its pre-call CLI path in `tools/evals/gmuse_evals/cli.py`. Require compatible suite, fixture, case, model, effective settings, prompt version, and log schema plus verified matching staged-diff and rendered-prompt hashes. Count any fresh work against normal limits and require confirmation.
- [ ] T015 [US4] Verify in `tests/integration/test_eval_runner_live.py` that a fresh rerun, including any work ineligible for reuse when supported, makes zero provider calls if normal limits or confirmation fail.

## Phase 7 — Documentation and Validation

- [ ] T016 [P] Document the live preflight workflow and the reuse decision in `docs/source/development/contributing.md` and `specs/draft/011-eval-live-budgeting-resume/quickstart.md`.
- [ ] T017 Run the quickstart's offline and mocked scenarios in `specs/draft/011-eval-live-budgeting-resume/quickstart.md` and the repo lint, type, and test gates defined in `noxfile.py`.

## Dependencies and Parallel Work

Setup precedes the shared foundation. US1 establishes the preflight flow
that US2 enforces. US3 can exercise native log behavior independently of US1
and US2 once the baseline is established. US4 needs US2's guardrails and US3's
readable logs. T013 and T014 run only if T012 confirms safe Inspect support.

- US1 preview test T005 can run alongside the US3 interruption test T010.
- US2 automation check T009 can run alongside CLI confirmation work T008.
- US3 log investigation can run alongside US1 rendering work in separate files.
- US4 compatibility tests T013 and the bounded-rerun test T015 can be drafted
  in parallel after the spike, using separate test files.

## Implementation Strategy

Use US1 and US2 as the MVP. Validate the pre-call behavior with mocked providers
before expanding to interruption handling. Deliver US3 with native Inspect
logs. Add reuse only if the spike demonstrates safe verification on the pinned
framework. Judge execution and offline comparison belong to specs 012 and 013.
