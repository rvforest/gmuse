# Implementation Plan: Understandable Eval Fixtures And Suites

**Branch**: `009-eval-fixtures-and-suites` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

Revise the maintainer-only eval foundation so a validation report clearly shows
what scenarios a suite represents, and so reviewable assessment assets explain
how future scoring will work. The revision replaces ambiguous coverage sets and
concept lists with counted suite composition, value-specific composition goals,
reusable scoring profiles, case assessment guidance, objective gate declarations,
and annotated examples. It remains offline: no candidate generation, judge
execution, aggregate scoring, or public product command is added.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Typer maintainer CLI; Pydantic structural
asset validation; existing Git reconstruction and staged-diff extraction;
existing development test, lint, type, and documentation tools

**Storage**: Versioned TOML assets under `evals/`; temporary repositories only
during validation; no new network or provider storage

**Testing**: Unit tests for models, selectors, counts, profile/guidance
validation, and report rendering; integration tests for checked-in assets,
temporary asset failures, and CLI behavior; existing reconstruction/provenance
coverage remains in force

**Target Platform**: Local maintainer environments on Linux, macOS, and Windows

**Performance Goals**: The smoke suite validates offline in under 30 seconds;
composition collection and guidance validation add no provider calls

**Constraints**: Schema 2.0 is a direct pre-release migration; asset loading
remains deterministic and selected-graph scoped; source assets remain
framework-neutral; raw generation prompts are not ordinary validation artifacts;
no public `gmuse` command or live evaluation work

**Scale/Scope**: Two migrated synthetic smoke cases; shared initial
`commit-message-v1` scoring profile; core composition goals are ready for
curation but are intentionally modest until the corpus grows

## Constitution Check

*Gate: Pass before research; re-checked after design.*

- **Code Quality**: Pass. The revision keeps source models, validation, report
  rendering, and Inspect adaptation separated; it removes legacy semantics
  rather than maintaining two opaque data shapes.
- **Testing**: Pass. Model, selector/count, report, asset, and integration
  tests can prove every requirement offline.
- **UX**: Pass. The central deliverable is a clearer maintainer report and
  reviewable assessment guidance with actionable errors.
- **Performance**: Pass. The validation path remains local, bounded, and free
  of model calls.
- **Security/Privacy**: Pass. Fake-secret and literal marker evidence stay
  explicit; semantic injection findings remain judge work; no raw prompts are
  introduced into ordinary validation output.
- **Release Discipline**: Pass. Schema, profile, guidance, fixture, and
  composition-goal identities are versioned. The direct migration is safe for
  pre-release maintainer assets.

## Project Structure

### Documentation and design artifacts

```text
specs/009-eval-fixtures-and-suites/
├── research.md
├── data-model.md
├── plan.md
├── quickstart.md
└── contracts/
    ├── fixture-schema.md
    ├── scoring-profile-schema.md
    ├── assessment-guidance-schema.md
    ├── suite-schema.md
    └── validation-cli.md
```

### Maintainer assets and implementation

```text
evals/
├── fixtures/
├── scoring_profiles/
│   └── commit-message-v1.toml
├── rubrics/                         # case assessment guidance
├── cases/
└── suites/

tools/evals/gmuse_evals/
├── models.py                         # schema 2.0 asset and report models
├── load.py                           # scoring-profile catalog discovery
├── validate.py                       # guidance, composition, and goal checks
├── cli.py                            # human-readable composition rendering
└── inspect_adapter.py                # stable handoff identities only

tests/unit/
tests/integration/
```

**Structure Decision**: Retain `rubrics/` as the file location to minimize
asset churn, but use **case assessment guidance** as the canonical data-model
meaning. Add `scoring_profiles/` for shared rating anchors. Feature 010, not
feature 009, renders these assets into Inspect targets and metadata.

## Phase 0: Research Decisions

Research is complete in [research.md](research.md).

1. Report suite composition as grouped case counts, not raw coverage sets.
2. Use typed, value-specific composition goals.
3. Use a shared four-level scoring profile and categorical usability.
4. Put independently assessable case criteria, failure conditions, objective
   gate declarations, and examples in case assessment guidance.
5. Keep semantic injection-obedience findings out of offline validation.
6. Migrate all feature assets directly to schema 2.0.
7. Require an immutable assessment-evidence handoff policy in downstream runner
   planning.

## Phase 1: Data and Contract Design

Design artifacts:

- [data-model.md](data-model.md) defines schema 2.0 identities,
  relationships, selector rules, rating/profile rules, gate boundaries, and
  report states.
- [fixture-schema.md](contracts/fixture-schema.md) retains reproducible fixture
  and provenance contracts under schema 2.0.
- [scoring-profile-schema.md](contracts/scoring-profile-schema.md) defines the
  reusable profile and its four anchors.
- [assessment-guidance-schema.md](contracts/assessment-guidance-schema.md)
  defines criteria, failure conditions, objective gates, and examples.
- [suite-schema.md](contracts/suite-schema.md) defines counted composition and
  value-specific goals.
- [validation-cli.md](contracts/validation-cli.md) defines the maintainer
  report and strict-composition behavior.
- [quickstart.md](quickstart.md) provides success and failure walkthroughs
  without model credentials.

Post-design constitution re-check: all gates remain passed. No unresolved
technical or policy decision remains before task generation.

## Phase 2: Implementation Plan

1. Add failing schema-2.0 model and loader tests for profiles, case assessment
   guidance, composition summaries, and value-specific goals.
2. Replace legacy coverage model/report types with typed composition groups and
   counted entries. Preserve composition for successfully resolved cases when
   selected-graph errors are also reported.
3. Replace generic coverage-policy validation with selector/value/minimum-case
   composition goals. Count matching cases, not distinct metadata values; reject
   unknown selectors, values, duplicates, and conflicting goals.
4. Replace legacy rubric concept/example fields with case assessment guidance
   that references a profile and validates criteria, failure conditions,
   objective gate declarations, and two annotated examples.
5. Add the `commit-message-v1` profile with four anchors for its subjective
   dimensions, definitions for all four usability labels, and intermediate
   usability illustrations.
6. Migrate checked-in fixture, case-guidance, and suite TOML assets to schema
   2.0. Give smoke minimal required scenarios and leave core goals ready for
   later expansion.
7. Render grouped `Suite composition` output with case counts and clear
   ordinary/safety wording. Rename `--strict-balance` to
   `--strict-composition`; preserve the former only as a documented temporary
   compatibility alias if the implementation needs one.
8. Extend the Inspect adapter descriptor with profile and case-guidance
   identity/revision/digest. It does not render scoring prompts or execute
   scoring.
9. Update maintainer documentation and quickstart, removing all user-facing
   coverage terminology.
10. Update draft features 010–013 before their implementation begins:
    - 010 resolves a canonical assessment target, preserves profile/guidance
      identities and a privacy-reviewed immutable assessment-evidence reference.
    - 011 treats those identities as reuse compatibility inputs where relevant.
    - 012 consumes profile-driven 1–4 ratings, separate usability, objective
      deterministic gates, and judge-sourced semantic injection findings; it
      does not add an aggregate.
    - 013 compares compatible profile/guidance identities and named dimensions,
      distinguishing deterministic from judge-sourced gates.
11. Run focused tests, the smoke/core validation commands, full lint/format/type
    checks, and documentation checks. Verify no provider calls, raw prompt
    exposure, or ordinary-product CLI changes.

## Complexity Tracking

No constitution violation or complexity exception is required.
