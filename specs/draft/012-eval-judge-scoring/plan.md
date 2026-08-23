# Implementation Plan: Eval Judge And Scoring

**Branch**: `012-eval-judge-scoring` | **Date**: 2026-06-11 | **Spec**: ../012-eval-judge-scoring/spec.md
**Input**: Feature specification from `specs/draft/012-eval-judge-scoring/spec.md`

## Summary

Add Inspect AI scorer support for existing spec 010/011 Inspect eval logs. The
scoring layer adds gmuse deterministic hard-failure checks, rubric-based
LLM-as-judge scoring, versioned error taxonomy, judge metadata capture, explicit
unscored states, and optional manual-review metadata on top of immutable
candidate sample results. Inspect logs are the canonical scored evidence. The
design keeps aggregate scores secondary, preserves per-dimension evidence, and
separates judge operational failures from candidate quality failures.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Inspect AI scorer/log support, existing gmuse Inspect
eval logs from specs 010 and 011, live-run guardrails from spec 011, existing
gmuse LLM/provider configuration path, pytest, Ruff, pyrefly

**Storage**: Inspect logs are canonical for scored results and judge metadata.
gmuse may add compact local sidecar metadata only if the Inspect spike shows a
required metadata gap. Source candidate sample results must not be mutated in a
way that loses original generated messages or validation evidence.

**Testing**: pytest unit, contract, and integration coverage with deterministic
fixtures, mocked judge calls, malformed judge responses, and simulated resume
state

**Target Platform**: Maintainer-only local Python CLI on Linux, macOS, and
Windows; default CI must not require provider credentials

**Project Type**: Single Python package plus maintainer-only repository tooling
under `tools/evals/gmuse_evals`

**Performance Goals**: Deterministic checks complete without provider calls;
judge calls are bounded by guardrails from spec 011; one judge call per eligible
candidate output by default; optional rerun/resume uses Inspect behavior when
simple and safe

**Constraints**: Do not alter generation behavior; consume runner records rather
than regenerating outputs; preserve raw generated messages and original judge
responses; write explicit unscored records for candidate operational failures;
do not judge deterministic hard failures by default; hard failures always gate
usability; self-judged results are flagged; aggregate scores never replace
per-dimension scores

**Scale/Scope**: Initial maintainer scoring for smoke/core/safety eval outputs,
focused on single-line freeform and conventional messages with minimal gitmoji
smoke handling; no baseline promotion/comparison, fixture importer, or public
benchmark recommendation output

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution gates for this feature:

- **Code Quality Gate**: Pass. Scoring can be isolated into Inspect scorer
  adapters plus small gmuse modules for deterministic checks, schema validation,
  scoring aggregation, and manual review metadata without adding import-time side
  effects.
- **Testing Gate**: Pass. The plan calls for unit tests for every public scoring
  function, contract tests for scored artifact schemas, and integration tests for
  budgeted judge scoring and resume behavior with mocked providers.
- **UX Gate**: Pass. Maintainer commands must show explicit scoring plans,
  budgeted judge-call counts, hard-failure summaries, and actionable operational
  errors.
- **Performance Gate**: Pass. Live judge calls are bounded by spec 011
  guardrails, deterministic checks run before judge calls, and optional reuse
  relies on Inspect where practical.
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
tools/
└── evals/
    └── gmuse_evals/
        ├── cli.py                  # add score command wiring
        ├── scoring.py              # Inspect scorer orchestration and effective result calculation
        ├── deterministic_checks.py # format, validation, privacy, injection, max_chars gates
        ├── judge.py                # judge request/response handling and metadata capture
        ├── inspect_scorers.py      # Inspect scorer adapters
        ├── taxonomy.py             # versioned quality and operational error categories
        ├── review_events.py        # append-only annotations and overrides
        └── schemas.py              # scored artifact schema constants and validation helpers

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

**Structure Decision**: Keep judge scoring in the maintainer-only tooling package
selected by specs 009 and 010. The feature primarily adds Inspect scorers that
consume existing Inspect run logs, reuse spec 011 guardrails for live judge
calls, and record scoring metadata in Inspect logs without changing candidate
generation, the production generation path, or normal user CLI behavior.

## Complexity Tracking

No constitution violations are expected for this feature.

## Phase 0 - Outline & Research (Output: `research.md`)

Research focus areas:

- Decide which failures are deterministic hard gates and which require judge
  assessment.
- Define the absolute rubric score dimensions, usability categories, aggregate
  weighting, and gate precedence.
- Decide the scoring command/scorer boundary and how multiple scoring
  configurations are represented in Inspect logs.
- Decide how the judge input is assembled from runner records, run-plan
  identity, canonical staged diffs, case rubrics, and generation context without
  using the rendered prompt as the primary evidence.
- Define the versioned quality/compliance taxonomy and separate judge
  operational taxonomy.
- Define self-judge detection and metadata requirements.
- Define explicit unscored records, append-only manual annotations and
  overrides, and calibration recording while preserving immutable automated
  outputs.

Output artifact:

- `specs/draft/012-eval-judge-scoring/research.md`

## Phase 1 - Design & Contracts (Outputs: `data-model.md`, `contracts/`, `quickstart.md`)

Design artifacts:

- Scoring entities, Inspect scorer relationships, validation rules, and state transitions:
  `specs/draft/012-eval-judge-scoring/data-model.md`
- Judge structured-output contract:
  `specs/draft/012-eval-judge-scoring/contracts/judge-output.md`
- Inspect scoring metadata contract:
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
3. Add scoring orchestration that consumes Inspect sample results, records one
   scored result per candidate input in Inspect logs, marks candidate
   operational failures as explicit unscored states, runs deterministic checks
   first, and decides judge eligibility.
4. Add judge request assembly that resolves the canonical staged diff and case
   rubric from Inspect sample metadata plus spec 009 assets, then combines them
   with the generated message, format/config context, and relevant
   history/branch/hint/repo-instruction context when present in the case.
5. Add judge invocation through Inspect/gmuse provider paths while enforcing spec
   011 guardrails and confirmation.
6. Add structured judge response parsing and validation against the judge output
   contract.
7. Add hard failure gate calculation and effective scoring so hard failures force
   unusable status, skip judge calls by default, and preserve per-dimension
   numeric scores when diagnostic judging is explicitly enabled.
8. Add aggregate scoring as a documented secondary field using accuracy 50%,
   quality 35%, and style/history fit 15% when applicable.
9. Add judge input controls that hide candidate model identity by default and
   record any diagnostic reason for including it.
10. Add calibration artifact support for manually annotated examples and
    warn/record when scoring proceeds without calibration; a rich calibration
    command can be deferred unless immediately needed.
11. Add self-judge detection based on candidate and judge model/provider metadata.
12. Add append-only manual annotation and override event schemas plus overlay
    loading/validation with immutable original automated result preservation; a
    dedicated review-editing CLI is not required for v1.
13. Add Inspect log metadata validation and optional compact sidecar writers only
    if required by the Inspect spike.
14. Add maintainer `score` CLI/scorer wiring and docs for offline validation,
    guarded live scoring, calibration status, and manual review metadata.
