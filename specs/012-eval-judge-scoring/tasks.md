# Tasks: Eval Judge And Scoring

**Design**: [specification](spec.md), [plan](plan.md), [data model](data-model.md), [contracts](contracts/), and [quickstart](quickstart.md).

## Phase 1: Setup

- [X] T001 Verify the eval tooling environment and run the existing Inspect runner and artifact contract tests in `tests/unit/test_eval_runner_inspect_runner.py` and `tests/contract/test_eval_runner_artifacts.py`.

## Phase 2: Foundations

- [X] T002 [P] Cover schema versions and the disjoint quality and judge operational category sets in `tests/unit/test_eval_taxonomy.py`.
- [X] T003 Define scoring, judge-output, judge-prompt and taxonomy versions and typed categories in `tools/evals/gmuse_evals/taxonomy.py`, reusing the existing asset schema and usability labels.
- [X] T004 Reconcile the invalid-output rule with the profile's 1–4 anchors in `specs/012-eval-judge-scoring/contracts/judge-output.md`.

## Phase 3: User Story 1 (P1) — Deterministic gates

**Independent test**: Apply deterministic scoring to saved runner samples with known validation, length, privacy and injection failures. Verify gate precedence, preserved input records and zero provider calls.

- [X] T005 [P] [US1] Test recorded production validation, production-equivalent character counting, fixture marker matching, extra output and privacy-safe evidence in `tests/unit/test_eval_deterministic_checks.py`.
- [X] T006 [US1] Implement typed deterministic check and gate records in `tools/evals/gmuse_evals/deterministic_checks.py`.
- [X] T007 [US1] Test and implement source traceability, candidate operational unscored status and hard-gate precedence in `tests/unit/test_eval_scoring.py` and `tools/evals/gmuse_evals/scoring.py`.
- [X] T008 [US1] Test and connect offline scoring to saved Inspect logs using the scorer and metadata contract in `tests/contract/test_eval_scoring_contracts.py`, `tests/integration/test_eval_scoring_cli.py`, `tools/evals/gmuse_evals/inspect_scorers.py` and `tools/evals/gmuse_evals/cli.py`.

## Phase 4: User Story 2 (P1) — Fixed judge and rubric

**Independent test**: Score a completed run with a mocked judge and verified evidence. Check one fixed configuration, source and rubric identity, named ratings, rationales, and self-judge flags.

- [X] T009 [P] [US2] Test strict structured judge output, including scale bounds, null applicability, rationales, unknown categories and raw-response preservation in `tests/unit/test_eval_judge.py`.
- [X] T010 [US2] Implement strict structured response parsing and typed judge results in `tools/evals/gmuse_evals/judge.py`.
- [X] T011 [P] [US2] Test exact evidence round trips, mutation or missing evidence, and rubric/profile changes in `tests/integration/test_eval_scoring_evidence.py`.
- [X] T012 [US2] Complete runner evidence capture where needed and verify the staged diff, case context, rubric and profile identities before judging in `tools/evals/gmuse_evals/execution.py`, `tools/evals/gmuse_evals/inspect_runner.py` and `tools/evals/gmuse_evals/scoring_evidence.py`.
- [X] T013 [US2] Assemble the versioned judge prompt with case evidence and profile anchors, hide candidate identity by default, and test diagnostic identity inclusion and self-judge detection in `tools/evals/gmuse_evals/judge.py` and `tests/unit/test_eval_judge.py`.
- [X] T014 [US2] Test zero calls without confirmation, budget limits, and default skip of hard-gated samples in `tests/integration/test_eval_judge_scoring.py`.
- [X] T015 [US2] Add the guarded live judge plan and execution with judge metadata, per-dimension evidence and effective usability to `tools/evals/gmuse_evals/cli.py`, `tools/evals/gmuse_evals/scoring.py` and `tools/evals/gmuse_evals/inspect_scorers.py`.

## Phase 5: User Story 3 (P2) — Calibration

**Independent test**: Run mocked calibration against manually annotated examples and verify expected and observed labels, agreement, parse failures, and identity controls.

- [X] T016 [P] [US3] Test calibration examples, label agreement, parse failures and incompatible judge or rubric identities in `tests/unit/test_eval_calibration.py`.
- [X] T017 [US3] Build versioned calibration reports and record compatible report references or missing calibration in `tools/evals/gmuse_evals/calibration.py` and `tools/evals/gmuse_evals/scoring.py`.

## Phase 6: User Story 4 (P2) — Manual review

**Independent test**: Apply an annotation and override and verify effective results, hard-gate precedence, and unchanged automated evidence.

- [X] T018 [P] [US4] Test event validation, ordered overlays and original result preservation in `tests/unit/test_eval_annotations.py`.
- [X] T019 [US4] Implement append-only annotations and overrides keyed to original scoring identities in `tools/evals/gmuse_evals/review_events.py`.

## Phase 7: User Story 5 (P3) — Judge failures and resume

**Independent test**: Simulate operational failures and interruption, then verify compatible completed records are skipped and remaining calls stay within budget.

- [X] T020 [P] [US5] Test auth, rate limit, timeout, network, context length, empty and parse failures and run compatibility in `tests/integration/test_eval_judge_scoring.py`.
- [X] T021 [US5] Map provider and parser failures to operational categories with no fabricated ratings in `tools/evals/gmuse_evals/judge.py` and `tools/evals/gmuse_evals/scoring.py`.
- [X] T022 [US5] Add compatibility-checked scoring resume and enforce remaining judge budget in `tools/evals/gmuse_evals/inspect_scorers.py` and `tools/evals/gmuse_evals/cli.py`.

## Phase 8: Validation and documentation

- [X] T023 [P] Document offline scoring, live confirmation, evidence retention, calibration and review events in `docs/source/development/contributing.md` and `specs/012-eval-judge-scoring/quickstart.md`.
- [X] T024 Verify the quickstart with mocked providers and run the unit, integration and contract suites under `tests/`.

## Dependencies and parallel execution

- Verify the setup before merging foundation work. T002 precedes T003 and T004 can run alongside the taxonomy work.
- T005 precedes T006, then T007 connects deterministic checks and T008 proves the offline path. This is the first usable increment.
- Judge parser tests and evidence verification tests can be prepared independently. Live judge execution depends on the deterministic scoring path, verified evidence and strict parser.
- Manual event implementation can proceed independently of calibration after the scoring metadata format is stable. Operational resume requires the guarded live path and compatibility metadata.
- Keep changes to shared scorer, judge and CLI modules sequential. Finish by verifying the full mocked scoring flow.
