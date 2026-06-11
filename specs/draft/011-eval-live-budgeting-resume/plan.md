# Implementation Plan: Eval Live Run Budgeting And Resume

**Branch**: `011-eval-live-budgeting-resume` | **Date**: 2026-06-11 | **Spec**: ../011-eval-live-budgeting-resume/spec.md

**Input**: Feature specification from `specs/draft/011-eval-live-budgeting-resume/spec.md`

## Summary

Add maintainer-only live eval run controls around the production-path eval runner:
plan each live run before calls, require explicit candidate and judge call
budgets, require confirmation, write candidate and judge records incrementally,
and resume interrupted runs only when prior artifacts are compatible with the
requested suite, models, configs, prompt and judge versions, and schemas.

The design depends on spec 009 for validated fixtures and suite identities and
on spec 010 for production-path runner outputs, prompt metadata, validation
outcomes, operational error categories, and artifact schema versions. It does
not design judge rubrics, baseline promotion/comparison, fixture import, or
public benchmark recommendations.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing gmuse CLI stack, spec 009 eval fixture/suite
artifacts, spec 010 production-path eval runner artifacts, standard library file
I/O and JSON/JSONL handling, pytest, Ruff, pyrefly

**Storage**: Local maintainer-chosen output directory containing run metadata,
incremental JSONL records, and JSON summary files

**Testing**: pytest unit, integration, and contract tests with mocked provider
calls; temporary output directories for interruption and resume behavior

**Target Platform**: Local Python CLI on Linux, macOS, and Windows; interactive
terminal and non-interactive maintainer automation

**Project Type**: Single Python package and maintainer CLI tooling

**Performance Goals**: Planning should finish without provider calls; resume
should scan existing run artifacts once and skip completed records without
replaying provider calls; incremental writes should keep completed records
durable after each item

**Constraints**: Live calls must never run without explicit budgets; planning
mode must make zero provider calls; ordinary package users and default CI must not require
eval provider credentials; resume must reject incompatible artifacts before live
calls; completed records must not be overwritten during resume

**Scale/Scope**: Maintainer eval suites from smoke through core scale, multiple
candidate models, optional judge work, and partial runs interrupted by provider
errors or user cancellation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution gates for this feature:

- **Code Quality Gate**: Pass. The feature can be implemented as eval-specific
  planning, budgeting, artifact writing, and resume helpers that wrap the
  production-path runner without changing ordinary generation behavior.
- **Testing Gate**: Pass. The plan requires unit, integration, and contract tests
  for budget validation, confirmation, planning-mode behavior, incremental writes,
  resume skipping, and incompatible resume rejection.
- **UX Gate**: Pass. Live calls are guarded by an explicit plan, clear budgets,
  confirmation prompts, and actionable incompatibility messages.
- **Performance Gate**: Pass. Planning and resume are bounded by selected suite
  size and artifact scan size, and no extra provider calls are made for skipped
  records.
- **Security/Privacy Gate**: Pass. The design uses maintainer-controlled local
  artifacts, does not store provider credentials, and does not add live evals to
  default CI or normal user workflows.
- **Release Discipline Gate**: Pass. Runtime behavior changes are isolated to
  maintainer eval commands and covered by contracts and quickstart validation.

Checklist:

- Code Quality Gate: Yes - keep budgeting and resume as focused eval runner
  orchestration rather than a second generation pipeline.
- Testing Gate: Yes - include contract and integration coverage for call
  accounting and resume compatibility.
- UX Gate: Yes - require readable plans, confirmations, and mismatch reasons.
- Performance Gate: Yes - skip completed records without provider calls and
  avoid reprocessing outputs unnecessarily.
- Security/Privacy Gate: Yes - no credential persistence or default CI live
  provider calls.
- Release Discipline Gate: Yes - artifact schemas and compatibility fields are
  versioned and documented.

## Project Structure

### Documentation (this feature)

```text
specs/draft/011-eval-live-budgeting-resume/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── contracts/
    ├── live-run-cli.md
    └── resume-state.md
```

### Source Code (repository root)

```text
src/gmuse/
├── cli/
│   └── main.py                    # maintainer eval command registration
└── evals/
    ├── fixtures.py                # spec 009 fixture/suite loading dependency
    ├── runner.py                  # spec 010 production-path runner dependency
    ├── live_plan.py               # live run planning and budget validation
    ├── live_artifacts.py          # incremental artifact writing and summaries
    ├── resume.py                  # compatibility checks and completed-record lookup
    └── schemas.py                 # shared artifact schema constants and identities

tests/
├── contract/
│   └── test_eval_live_contracts.py
├── integration/
│   └── test_eval_live_resume.py
└── unit/
    ├── test_eval_live_plan.py
    ├── test_eval_live_artifacts.py
    └── test_eval_resume.py
```

**Structure Decision**: Keep eval live-run orchestration under an eval-specific
package and CLI surface. The feature wraps spec 010's production-path runner and
spec 009's validated suite model instead of introducing another generation or
fixture pipeline.

## Complexity Tracking

No constitution violations are expected for this feature.

## Phase 0 - Outline & Research (Output: `research.md`)

Research focus areas:

- Decide how budgets are expressed and enforced for candidate calls, judge calls,
  and total reporting.
- Decide the run plan and confirmation contract for interactive terminals,
  non-interactive `--yes`, and zero-call planning.
- Decide the incremental artifact layout so interrupted runs preserve completed
  records and summaries remain readable.
- Decide the resume compatibility fingerprint and mismatch behavior across suite,
  fixture, config, model, prompt, judge, and schema fields.
- Decide how to count provider attempts, operational errors, skipped records, and
  partial completion without designing judge scoring itself.

Output artifact:

- `specs/draft/011-eval-live-budgeting-resume/research.md`

## Phase 1 - Design & Contracts (Outputs: `data-model.md`, `contracts/`, `quickstart.md`)

Design artifacts:

- Run planning, call accounting, artifact, and resume entities:
  `specs/draft/011-eval-live-budgeting-resume/data-model.md`
- CLI contract for planning, confirmation, budgets, zero-call planning, and resume:
  `specs/draft/011-eval-live-budgeting-resume/contracts/live-run-cli.md`
- Resume artifact and compatibility contract:
  `specs/draft/011-eval-live-budgeting-resume/contracts/resume-state.md`
- Maintainer validation guide:
  `specs/draft/011-eval-live-budgeting-resume/quickstart.md`

Post-design constitution re-check:

- Code Quality: pass - design remains modular and eval-specific.
- Testing: pass - contracts identify observable behavior for automated tests.
- UX: pass - live runs are explicit, planned, and confirmed.
- Performance: pass - resume skips prior work and planning mode makes no calls.
- Security/Privacy: pass - no credential persistence and no default CI live calls.
- Release Discipline: pass - artifact schema and compatibility versions are
  explicit design entities.

## Phase 2 - Future Implementation Planning

Planned implementation steps:

1. Add a live run planner that expands spec 009 suite selections and spec 010
   runner configuration into candidate and optional judge planned work items.
2. Add budget validation that requires explicit candidate budgets and, when judge
   work is enabled, explicit judge budgets before provider calls.
3. Add a run plan display that reports suite identity, selected cases, models,
   judge config, planned calls, budgets, resume status, and artifact paths.
4. Add interactive confirmation and non-interactive `--yes` handling while
   preserving `--plan` as a zero-call planning mode.
5. Add incremental artifact writers for run metadata, candidate JSONL records,
   judge JSONL records, and run summaries.
6. Add resume artifact loading, completed-record indexing, duplicate/corrupt
   record detection, and compatibility checks.
7. Wire resume planning so completed records are skipped and only missing work
   consumes the new run's budgets.
8. Add tests for missing budgets, over-budget rejection, planning-mode zero-call
   behavior, confirmation behavior, interruption durability, compatible resume,
   incompatible resume, and corrupt/duplicate prior artifacts.
9. Update maintainer documentation for live eval usage when the implementation
   tasks are generated.
