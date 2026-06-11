# Implementation Plan: Production-Path Eval Runner

**Branch**: `010-eval-runner` | **Date**: 2026-06-11 | **Spec**: ../010-eval-runner/spec.md
**Input**: Feature specification from `specs/draft/010-eval-runner/spec.md`

## Summary

Add maintainer-only eval runner tooling that consumes the fixture and suite foundation from spec 009, reconstructs each selected case in an isolated temporary git repository, and invokes gmuse's production generation path with eval-only instrumentation. The runner supports a no-call planning mode, executes case/model/config attempts when explicitly requested, and writes versioned JSONL output records plus a JSON run summary. This slice stops at deterministic production validation and raw artifact capture; judge scoring, resume/budgeting, baselines, importers, and public recommendations remain out of scope.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing gmuse generation stack (`gmuse.commit`, `gmuse.git`, config resolution, validation), fixture/suite contracts from spec 009, standard library (`json`, `tempfile`, `pathlib`, `hashlib`, `time`, `uuid`), pytest, Ruff, pyrefly

**Storage**: Local result artifacts written to an explicit eval output directory; temporary git repositories for case execution; no new persistent application storage

**Testing**: pytest unit, contract, and integration tests with stubbed provider behavior and temporary git repositories; offline smoke suite validation from spec 009

**Target Platform**: Local maintainer CLI on Linux, macOS, and Windows; default CI must not require provider credentials

**Project Type**: Single Python package (`src/gmuse`) with CLI entrypoints and maintainer/development tooling

**Performance Goals**: Planning mode makes zero provider calls; each attempted case performs one production generation call per selected model/config combination; artifact writing streams JSONL records without holding full run output in memory

**Constraints**: Must use production generation behavior; must not mutate normal `gmuse msg`/generation workflows; must preserve invalid generated outputs; must keep raw prompts out of artifacts by default; must depend on spec 009 fixture/suite validation rather than redefining fixture ingestion

**Scale/Scope**: Smoke and core maintainer suites from spec 009, initially tens of cases and multiple candidate models/configs; not a broad public benchmark system

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution gates for this feature:

- **Code Quality Gate**: Pass. The runner can be implemented as focused maintainer/eval modules with typed public APIs and no import-time side effects, reusing existing production generation services.
- **Testing Gate**: Pass. The plan requires contract tests for artifact schemas, unit tests for planning/result classification, and integration tests with temporary repositories and stubbed providers.
- **UX Gate**: Pass. The runner is maintainer-facing and explicit; planning mode and clear error reporting prevent surprising live calls.
- **Performance Gate**: Pass. Provider calls are bounded to one generation per attempt, planning mode is no-call, and JSONL streaming avoids accumulating all result records.
- **Security/Privacy Gate**: Pass. Raw prompts are not written by default, temporary repos are isolated, debug preservation is opt-in, and secrets remain environment/config driven.
- **Release Discipline Gate**: Pass. The feature adds versioned artifact schemas and does not alter normal user-facing generation behavior.

Checklist:

- Code Quality Gate: Yes — isolate runner planning, execution, and artifact writing.
- Testing Gate: Yes — include offline smoke tests and schema/contract coverage.
- UX Gate: Yes — make no-call planning mode and maintainer scope explicit.
- Performance Gate: Yes — stream records and avoid duplicate generation calls.
- Security/Privacy Gate: Yes — hash prompts by default and gate debug artifacts.
- Release Discipline Gate: Yes — version result artifacts for future scoring/baseline specs.

## Project Structure

### Documentation (this feature)

```text
specs/draft/010-eval-runner/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── contracts/
    ├── runner-cli.md
    └── result-artifacts.md
```

### Source Code (repository root)

```text
src/gmuse/
├── evals/
│   ├── __init__.py
│   ├── runner.py          # run planning and orchestration
│   ├── execution.py       # temporary repo case execution through production path
│   ├── artifacts.py       # JSONL and summary writers
│   └── errors.py          # operational/setup error categories
├── cli/
│   └── main.py            # explicit maintainer-facing runner command registration
├── commit.py              # production generation path reused, with instrumentation hooks if needed
└── git.py                 # existing git helpers reused for staged diff/context behavior

tests/
├── contract/
│   └── test_eval_runner_artifacts.py
├── integration/
│   └── test_eval_runner.py
└── unit/
    ├── test_eval_runner_plan.py
    ├── test_eval_runner_execution.py
    └── test_eval_runner_artifacts.py
```

**Structure Decision**: Keep eval runner implementation inside the existing package but behind explicit maintainer-facing command surfaces and development/test paths. The runner should call production generation services directly instead of shelling out to the user CLI, while instrumentation observes prompt/context metadata without changing generation semantics.

## Complexity Tracking

No constitution violations are expected for this feature.

## Phase 0 — Outline & Research (Output: `research.md`)

Research focus areas:

- Confirm the runner boundary with spec 009 fixture/suite validation so this feature consumes validated cases rather than redefining fixture schemas.
- Decide how planning mode represents case/model/config attempts while guaranteeing zero provider calls.
- Define the production-path invocation pattern that observes prompt metadata, generated output, and validation outcomes without altering generation behavior.
- Define result artifact layout, schema versions, and operational error categories for future judge/baseline phases.
- Decide privacy defaults for prompt hashes, prompt text, temporary repositories, and debug preservation.

Output artifact:

- `specs/draft/010-eval-runner/research.md`

## Phase 1 — Design & Contracts (Outputs: `data-model.md`, `contracts/`, `quickstart.md`)

Design artifacts:

- Eval run, run plan, case execution, output record, run summary, and operational error model:
  `specs/draft/010-eval-runner/data-model.md`
- Maintainer CLI contract for planning and execution:
  `specs/draft/010-eval-runner/contracts/runner-cli.md`
- Result artifact schema contract:
  `specs/draft/010-eval-runner/contracts/result-artifacts.md`
- Maintainer validation walkthrough:
  `specs/draft/010-eval-runner/quickstart.md`

Post-design constitution re-check:

- Code Quality: runner modules remain focused and typed; production generation path is reused.
- Testing: artifact contracts, planning mode, execution with stubbed providers, and failure classification are testable offline.
- UX: live execution remains explicit and planning mode is safe.
- Performance: one generation call per attempt and streaming artifact writes.
- Security/Privacy: prompt text and temporary repository preservation are opt-in debug behavior.
- Release Discipline: artifact schemas are versioned for future scoring and baseline specs.

## Phase 2 — Future Implementation Planning

Planned implementation steps for the future task phase:

1. Add an eval runner CLI surface with planning and execution modes, wired as maintainer tooling.
2. Add run-plan construction that resolves suites/cases/models/configs through the spec 009 fixture/suite APIs.
3. Add temporary repository execution that reconstructs each case and stages changes through the spec 009 foundation.
4. Route each attempt through the production generation path and capture generated output, validation outcome, context metadata, prompt hash, prompt size, token estimate, and timing.
5. Add JSONL output record streaming and JSON summary writing with schema versions.
6. Add deterministic operational error classification for setup/provider failures.
7. Add offline tests with stubbed providers plus contract tests for the artifact schemas.

`tasks.md` is intentionally not created in this design pass.
