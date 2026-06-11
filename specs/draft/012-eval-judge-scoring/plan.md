# Implementation Plan: Eval Judge And Scoring

**Branch**: `012-eval-judge-scoring` | **Date**: 2026-06-11 | **Spec**: ../012-eval-judge-scoring/spec.md
**Input**: Feature specification from `specs/draft/012-eval-judge-scoring/spec.md`

## Summary

Add maintainer-only scoring for spec 010 eval runner outputs, and for spec 011
resumable candidate records where live-run artifacts are used, by layering deterministic
hard-failure checks, rubric-based LLM-as-judge scoring, versioned error
taxonomy, judge metadata capture, and transparent manual annotations/overrides on
top of the eval artifacts from specs 010 and 011. The design keeps aggregate
scores secondary, preserves per-dimension evidence, and separates judge
operational failures from candidate quality failures.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing gmuse eval runner artifacts from spec 010
(`run-plan.json`, `outputs.jsonl`, `summary.json`), live-call
budgeting/resume controls from spec 011 (`run.json`, `candidate-records.jsonl`,
`judge-records.jsonl`, `summary.json`), existing gmuse LLM/provider
configuration path, standard library JSON/JSONL handling, pytest, Ruff, pyrefly

**Storage**: Versioned local eval artifacts: scored JSONL records, scoring
summary JSON, optional annotation/override files; no new storage for normal
runtime users

**Testing**: pytest unit, contract, and integration coverage with deterministic
fixtures, mocked judge calls, malformed judge responses, and simulated resume
state

**Target Platform**: Maintainer-only local Python CLI on Linux, macOS, and
Windows; default CI must not require provider credentials

**Project Type**: Single Python package with CLI-accessible maintainer eval
tooling and library functions under the existing `src/gmuse` structure

**Performance Goals**: Deterministic checks complete without provider calls;
judge calls are bounded by explicit budgets from spec 011; scoring resumes by
skipping already scored compatible records; one judge call per eligible candidate
output by default

**Constraints**: Do not alter generation behavior; consume runner records rather
than regenerating outputs; preserve raw generated messages and original judge
responses; hard failures always gate usability; self-judged results are flagged;
aggregate scores never replace per-dimension scores

**Scale/Scope**: Initial maintainer scoring for smoke/core/safety eval outputs,
focused on single-line freeform and conventional messages with minimal gitmoji
smoke handling; no baseline promotion/comparison, fixture importer, or public
benchmark recommendation output

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution gates for this feature:

- **Code Quality Gate**: Pass. Scoring can be isolated into small eval-specific
  modules for deterministic checks, judge invocation, schema validation, scoring
  aggregation, and manual review metadata without adding import-time side
  effects.
- **Testing Gate**: Pass. The plan calls for unit tests for every public scoring
  function, contract tests for scored artifact schemas, and integration tests for
  budgeted judge scoring and resume behavior with mocked providers.
- **UX Gate**: Pass. Maintainer commands must show explicit scoring plans,
  budgeted judge-call counts, hard-failure summaries, and actionable operational
  errors.
- **Performance Gate**: Pass. Live judge calls are bounded by spec 011 budgets,
  deterministic checks run before judge calls, and resume avoids repeated calls
  for completed compatible records.
- **Security/Privacy Gate**: Pass. The design treats privacy leaks as hard
  failures, uses fake fixture secrets for tests, masks secrets in logs, and keeps
  live eval artifacts maintainer-controlled.
- **Release Discipline Gate**: Pass. Artifact schemas, judge prompt versions,
  rubric versions, and taxonomy versions are explicitly recorded for future
  compatibility checks.

Checklist:

- Code Quality Gate: Yes -- keep scoring components modular and typed.
- Testing Gate: Yes -- add deterministic, mocked-live, contract, and resume
  coverage.
- UX Gate: Yes -- expose clear maintainer review output and errors.
- Performance Gate: Yes -- no unbudgeted live calls; skip completed records.
- Security/Privacy Gate: Yes -- hard-gate leaks and avoid default CI secrets.
- Release Discipline Gate: Yes -- version every scoring-facing artifact.

## Project Structure

### Documentation (this feature)

```text
specs/draft/012-eval-judge-scoring/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── contracts/
    ├── judge-output.md
    └── scoring-schema.md
```

### Source Code (repository root)

```text
src/gmuse/
├── evals/
│   ├── scoring.py              # scoring orchestration and effective result calculation
│   ├── deterministic_checks.py # format, validation, privacy, injection, max_chars gates
│   ├── judge.py                # judge request/response handling and metadata capture
│   ├── taxonomy.py             # versioned quality and operational error categories
│   ├── annotations.py          # manual annotations and overrides
│   └── schemas.py              # scored artifact schema constants and validation helpers
└── cli/
    └── evals.py                # maintainer scoring command wiring

tests/
├── contract/
│   └── test_eval_scoring_contracts.py
├── integration/
│   └── test_eval_judge_scoring.py
└── unit/
    ├── test_eval_deterministic_checks.py
    ├── test_eval_judge.py
    ├── test_eval_scoring.py
    ├── test_eval_taxonomy.py
    └── test_eval_annotations.py

docs/source/development/
└── evals.md                    # maintainer docs if eval docs exist by implementation time
```

**Structure Decision**: Keep judge scoring inside eval-specific modules under the
existing Python package. The feature should consume spec 010 runner records and
spec 011 budget/resume services, then emit scored artifacts without changing the
production generation path or normal user CLI behavior.

## Complexity Tracking

No constitution violations are expected for this feature.

## Phase 0 - Outline & Research (Output: `research.md`)

Research focus areas:

- Decide which failures are deterministic hard gates and which require judge
  assessment.
- Define the absolute rubric score dimensions, usability categories, aggregate
  weighting, and gate precedence.
- Decide how the judge input is assembled from runner records, raw staged diffs,
  case rubrics, and generation context without using the rendered prompt as the
  primary evidence.
- Define the versioned quality/compliance taxonomy and separate judge
  operational taxonomy.
- Define self-judge detection and metadata requirements.
- Define manual annotations and overrides while preserving immutable automated
  outputs.

Output artifact:

- `specs/draft/012-eval-judge-scoring/research.md`

## Phase 1 - Design & Contracts (Outputs: `data-model.md`, `contracts/`, `quickstart.md`)

Design artifacts:

- Scoring entities, relationships, validation rules, and state transitions:
  `specs/draft/012-eval-judge-scoring/data-model.md`
- Judge structured-output contract:
  `specs/draft/012-eval-judge-scoring/contracts/judge-output.md`
- Scored artifact schema contract:
  `specs/draft/012-eval-judge-scoring/contracts/scoring-schema.md`
- Maintainer validation guide:
  `specs/draft/012-eval-judge-scoring/quickstart.md`

Post-design constitution re-check:

- Code Quality: scoring, judge integration, taxonomy, and overrides remain
  separate typed modules.
- Testing: deterministic gates, mocked judge calls, schema contracts, and manual
  override audit behavior are all testable without live provider credentials.
- UX: maintainer output names hard failures, judge operational failures, budget
  use, and resume decisions clearly.
- Performance: deterministic checks run before live judge calls, and spec 011
  budget/resume controls remain mandatory.
- Security/Privacy: privacy leaks hard-fail; logs and summaries must not expose
  secrets beyond explicit local eval artifacts.
- Release Discipline: schema, taxonomy, judge prompt, and rubric versions are
  part of every scored result.

## Phase 2 - Future Implementation Planning

Planned implementation steps:

1. Add version constants for scored artifacts, judge output, rubric, judge prompt,
   quality taxonomy, and operational taxonomy.
2. Add deterministic check helpers for production validation status, format
   compliance, `max_chars`, known fake secret leakage, extra output, and obvious
   injection-following markers.
3. Add scoring orchestration that consumes spec 010 runner records, skips
   candidate operational failures, runs deterministic checks first, and decides
   judge eligibility.
4. Add judge request assembly from staged diff, generated message, case rubric,
   format/config context, and relevant history/branch/hint/repo-instruction
   context when present in the case.
5. Add judge invocation through the existing provider path while enforcing spec
   011 budgets, confirmation, incremental writes, and resume compatibility.
6. Add structured judge response parsing and validation against the judge output
   contract.
7. Add hard failure gate calculation and effective scoring so hard failures force
   unusable status while preserving per-dimension numeric scores.
8. Add aggregate scoring as a documented secondary field using accuracy 50%,
   quality 35%, and style/history fit 15% when applicable.
9. Add judge input controls that hide candidate model identity by default and
   record any diagnostic reason for including it.
10. Add calibration report generation against manually annotated examples for
    judge prompt and rubric versions.
11. Add self-judge detection based on candidate and judge model/provider metadata.
12. Add manual annotation and override loading/validation with immutable original
    automated result preservation.
13. Add scored JSONL and summary JSON writers with schema/version metadata and
    source runner attempt/candidate-record traceability.
14. Add maintainer CLI command wiring and docs for offline validation, budgeted
    live scoring, resume, and manual overrides.
