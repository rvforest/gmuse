# Implementation Plan: Production-Path Eval Runner

**Branch**: `010-eval-runner` | **Date**: 2026-06-11 | **Spec**: ../010-eval-runner/spec.md
**Input**: Feature specification from `specs/draft/010-eval-runner/spec.md`

## Summary

Add maintainer-only eval runner tooling that consumes the fixture and suite
foundation from spec 009, exposes validated cases as Inspect AI samples,
reconstructs each selected case in an isolated temporary git repository, and
invokes gmuse's production generation path from an Inspect solver. The runner
supports a no-provider `check` mode with deterministic local output and a live
mode with explicit maintainer confirmation plus Inspect/gmuse spend guardrails.
Inspect logs are the canonical execution artifacts. This slice stops at
deterministic production validation and raw output capture; custom judge
scoring, custom resume accounting, baselines, importers, and public
recommendations remain out of scope.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Inspect AI as the local eval execution/logging
framework; existing gmuse generation stack (`gmuse.commit`, `gmuse.git`, config
resolution, validation); fixture/suite contracts and maintainer package from
spec 009; Typer CLI app under `tools/evals/gmuse_evals`; standard library
(`tempfile`, `pathlib`, `hashlib`, `time`, `uuid`); pytest, Ruff, pyrefly

**Storage**: Inspect log files are canonical and written to the configured local
Inspect log directory or a gmuse-selected local eval directory; temporary git
repositories for case execution; optional debug artifacts only under explicit
debug/preserve settings; no hosted service or account-backed storage

**Testing**: pytest unit, contract, and integration tests with deterministic
local output and temporary git repositories; smoke suite validation from spec
009; optional local `nox -s evals-check` convenience session, not wired into
GitHub Actions

**Target Platform**: Local maintainer CLI on Linux, macOS, and Windows; default CI must not require provider credentials

**Project Type**: Single Python package (`src/gmuse`) plus maintainer-only
repository tooling under `tools/evals/gmuse_evals`; no public `gmuse eval`
command

**Performance Goals**: Check mode makes zero provider calls; live mode requires
preflight review and configured runaway-spend guardrails using Inspect-native
limits where practical; log writing uses Inspect-native behavior

**Constraints**: Must use production generation behavior; must not mutate normal
`gmuse msg`/generation workflows; must preserve invalid generated outputs in
Inspect logs; must keep raw prompts out of normal logs unless Inspect/gmuse debug
settings explicitly opt in; must depend on spec 009 fixture/suite validation
rather than redefining fixture ingestion; live mode requires explicit model
selection, preflight display, confirmation, and spend guardrails; check mode
forbids live model calls; one suite per run in this slice

**Scale/Scope**: Smoke and core maintainer suites from spec 009, initially tens
of cases and multiple candidate models/configs; not a broad public benchmark
system; no default CI live-call path

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution gates for this feature:

- **Code Quality Gate**: Pass. The runner can be implemented as focused
  maintainer/eval modules that adapt spec 009 cases into Inspect datasets and
  call existing production generation services through a narrow internal attempt
  API.
- **Testing Gate**: Pass. The plan requires contract tests for artifact schemas,
  unit tests for run-plan/result classification, and integration tests with
  temporary repositories and deterministic local output.
- **UX Gate**: Pass. The runner is maintainer-facing and explicit; required
  `--mode check|live`, live preflight, configured limits, and clear error
  reporting prevent surprising live calls.
- **Performance Gate**: Pass. Check mode is no-call, live mode uses explicit
  preflight plus Inspect/gmuse limits, and Inspect owns result logging.
- **Security/Privacy Gate**: Pass. Raw prompts are not written to main artifacts,
  temporary repos are isolated, debug preservation is opt-in, and secrets remain
  environment/config driven.
- **Release Discipline Gate**: Pass. The feature adds versioned artifact schemas and does not alter normal user-facing generation behavior.

Checklist:

- Code Quality Gate: Yes — isolate runner planning, Inspect task construction,
  and production-path solver code under `tools/evals`.
- Testing Gate: Yes — include deterministic check-mode tests and schema/contract coverage.
- UX Gate: Yes — make check/live mode and maintainer scope explicit.
- Performance Gate: Yes — rely on Inspect logging and configured live-run limits.
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
tools/
└── evals/
    └── gmuse_evals/
        ├── cli.py              # Typer app with validate/run commands
        ├── inspect_tasks.py    # Inspect task/dataset/scorer construction
        ├── runner.py           # run-plan construction and Inspect orchestration
        ├── execution.py        # temporary repo execution through production path
        ├── logs.py             # gmuse helpers around Inspect logs/metadata
        ├── deterministic.py    # check-mode local output policy
        └── errors.py           # operational/setup error categories

src/gmuse/
├── commit.py              # production generation path reused; add internal attempt API
├── prompts.py             # prompt version/token estimate helpers reused
└── git.py                 # existing git helpers reused for staged diff/context behavior

noxfile.py                 # optional evals-check local convenience session
.gitignore                 # ignore .gmuse-evals/

tests/
├── contract/
│   └── test_eval_runner_artifacts.py
├── integration/
│   └── test_eval_runner_check.py
└── unit/
    ├── test_eval_runner_plan.py
    ├── test_eval_runner_execution.py
    ├── test_eval_runner_artifacts.py
    └── test_commit_attempt.py
```

**Structure Decision**: Keep eval runner implementation in the same
maintainer-only package as spec 009, outside `src/gmuse`, and use Inspect logs
as canonical execution evidence. The runner should call production generation
services directly from an Inspect solver instead of shelling out to the user CLI.
The product package change should be limited to a lower-level internal
`generate_message_attempt()` path, prompt metadata on generation results, and a
typed injection seam for deterministic local output; existing
`generate_message()` raising behavior remains unchanged.

## Complexity Tracking

No constitution violations are expected for this feature.

## Phase 0 — Outline & Research (Output: `research.md`)

Research focus areas:

- Confirm the runner boundary with spec 009 fixture/suite validation so this
  feature consumes validated cases as Inspect samples rather than redefining
  fixture schemas.
- Decide how check mode represents case/config entries in an Inspect task and
  guarantees zero provider calls.
- Decide how live mode requires model selection, preflight display,
  confirmation, and Inspect/gmuse spend guardrails before provider calls.
- Define the production-path invocation pattern that observes prompt metadata, generated output, and validation outcomes without altering generation behavior.
- Define which gmuse metadata must be attached to Inspect logs for future
  scoring and strict safety comparison phases.
- Decide privacy defaults for prompt hashes, prompt text, temporary repositories, and debug preservation.
- Decide log directory defaults, collision behavior, and no hidden state between
  check and live runs.

Output artifact:

- `specs/draft/010-eval-runner/research.md`

## Phase 1 — Design & Contracts (Outputs: `data-model.md`, `contracts/`, `quickstart.md`)

Design artifacts:

- Eval run, Inspect task/sample mapping, case execution, log metadata, and
  operational error model:
  `specs/draft/010-eval-runner/data-model.md`
- Maintainer CLI contract for check and live execution:
  `specs/draft/010-eval-runner/contracts/runner-cli.md`
- Inspect log metadata contract:
  `specs/draft/010-eval-runner/contracts/result-artifacts.md`
- Maintainer validation walkthrough:
  `specs/draft/010-eval-runner/quickstart.md`

Post-design constitution re-check:

- Code Quality: runner modules remain focused and typed; production generation path is reused.
- Testing: artifact contracts, check mode, deterministic local output, and
  failure classification are testable offline.
- UX: live execution remains explicit and check mode is safe.
- Performance: live calls are bounded by configured Inspect/gmuse limits and
  Inspect owns result logging.
- Security/Privacy: prompt text and temporary repository preservation are opt-in debug behavior.
- Release Discipline: artifact schemas are versioned for future scoring and baseline specs.

## Phase 2 — Future Implementation Planning

Planned implementation steps for the future task phase:

1. Add an eval runner CLI surface with `run --mode check|live`, wired as
   maintainer tooling under `tools/evals/gmuse_evals`.
2. Add Inspect task construction that resolves one suite, cases, optional live
   models, and effective configs through the spec 009 fixture/suite APIs.
3. Add temporary repository execution that reconstructs each case and stages
   changes through the spec 009 foundation from inside the Inspect solver.
4. Add `generate_message_attempt()` and prompt metadata support while keeping
   `generate_message()` behavior unchanged.
5. Route each Inspect sample through the production generation path and capture
   generated output, validation outcome, context metadata, prompt hash, prompt
   size, token estimate, and timing as Inspect log metadata.
6. Add deterministic operational error classification for setup/provider failures.
7. Add check-mode deterministic local output tests plus contract tests for the
   Inspect log metadata required by downstream specs.
8. Add `nox -s evals-check` as a local-only convenience session that writes
   Inspect logs to a temporary directory.

`tasks.md` is intentionally not created in this design pass.
