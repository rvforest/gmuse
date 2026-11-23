# Implementation Plan: Eval Fixtures And Suites

**Branch**: `009-eval-fixtures-and-suites` | **Date**: 2026-09-06 | **Spec**: [spec.md](spec.md)

## Summary

Create a maintainer-only eval foundation whose validation report clearly shows
what scenarios a suite represents and whose reviewable assets explain how future
scoring works. The foundation uses counted suite composition, value-specific
composition goals, reusable scoring profiles, case rubrics, objective gate
declarations, and annotated examples. It remains offline: no candidate
generation, judge execution, aggregate scoring, or public product command is
added.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing Typer maintainer CLI; Pydantic structural
asset validation; existing Git reconstruction and staged-diff extraction;
existing development test, lint, type, and documentation tools

**Storage**: Versioned TOML assets under `evals/`; temporary repositories only
during validation; no new network or provider storage

**Testing**: Unit tests for models, selectors, counts, profile/rubric validation,
and report rendering; integration tests for checked-in assets, temporary asset
failures, and CLI behavior; reconstruction and provenance coverage remain in
force

**Target Platform**: Local maintainer environments on Linux, macOS, and Windows

**Performance Goals**: The smoke suite validates offline in under 30 seconds;
composition collection and rubric validation add no provider calls

**Constraints**: Schema 1.0 asset loading remains deterministic and
selected-graph scoped; source assets remain framework-neutral; raw generation
prompts are not ordinary validation artifacts; no public `gmuse` command or
live evaluation work

**Scale/Scope**: Two synthetic smoke cases; shared initial
`commit-message-v1` scoring profile; core composition goals are ready for
curation and expand with the corpus

## Constitution Check

*Gate: Pass before research; re-checked after design.*

- **Code Quality**: Pass. Source models, validation, report rendering, and
  Inspect adaptation stay separate.
- **Testing**: Pass. Model, selector/count, report, asset, and integration
  tests can prove every requirement offline.
- **UX**: Pass. The central deliverable is a clear maintainer report and
  reviewable rubrics with actionable errors.
- **Performance**: Pass. The validation path remains local, bounded, and free
  of model calls.
- **Security/Privacy**: Pass. Fake-secret and literal marker evidence stay
  explicit; semantic injection findings remain judge work; no raw prompts are
  introduced into ordinary validation output.
- **Release Discipline**: Pass. Schema, profile, rubric, fixture, and
  composition-goal identities are versioned.

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
    ├── rubric-schema.md
    ├── suite-schema.md
    └── validation-cli.md
```

### Maintainer assets and implementation

```text
evals/
├── fixtures/
├── scoring_profiles/
│   └── commit-message-v1.toml
├── rubrics/
├── cases/
└── suites/

tools/evals/gmuse_evals/
├── composition.py
├── fixture_models.py
├── report_models.py
├── results.py
├── rubric_models.py
├── schema.py
├── suite_models.py
├── validation_rules.py
├── models.py  # canonical import surface
├── load.py
├── validate.py
├── cli.py
└── inspect_adapter.py

tests/unit/
tests/integration/
```

**Structure Decision**: A scoring profile holds reusable rating anchors and
usability definitions. A rubric holds the criteria, failure conditions,
objective gates, and examples for one case. Composition collection and domain
rules live outside the validation orchestrator so each module has one purpose.
Feature 010, not feature 009, renders source assets into Inspect targets and
metadata.

## Phase 0: Research Decisions

Research is complete in [research.md](research.md).

1. Report suite composition as grouped case counts.
2. Use typed, value-specific composition goals.
3. Use a shared four-level scoring profile and categorical usability.
4. Put independently assessable criteria, failure conditions, objective gates,
   and examples in case rubrics.
5. Keep semantic injection-obedience findings out of offline validation.
6. Require an immutable assessment-evidence handoff policy in downstream runner
   planning.

## Phase 1: Data and Contract Design

Design artifacts:

- [data-model.md](data-model.md) defines asset identities, relationships,
  selectors, rating/profile rules, gate boundaries, and report states.
- [fixture-schema.md](contracts/fixture-schema.md) defines reproducible fixture
  and provenance data.
- [scoring-profile-schema.md](contracts/scoring-profile-schema.md) defines the
  reusable profile and its four anchors.
- [rubric-schema.md](contracts/rubric-schema.md) defines criteria, failure
  conditions, objective gates, and examples.
- [suite-schema.md](contracts/suite-schema.md) defines counted composition and
  value-specific goals.
- [validation-cli.md](contracts/validation-cli.md) defines the maintainer
  report and strict-composition behavior.
- [quickstart.md](quickstart.md) provides success and failure walkthroughs
  without model credentials.

Post-design constitution re-check: all gates remain passed. No unresolved
technical or policy decision remains before task generation.

## Phase 2: Implementation Plan

1. Add failing model and loader tests for profiles, rubrics, composition
   summaries, and value-specific goals.
2. Add typed composition groups and counted entries. Preserve composition for
   successfully resolved cases when selected-graph errors are also reported.
3. Add selector/value/minimum-case composition-goal validation. Count matching
   cases, not distinct metadata values; reject unknown selectors, values,
   duplicates, and conflicts.
4. Add rubrics that reference a profile and validate criteria, failure
   conditions, objective gate declarations, and two annotated examples.
5. Add the `commit-message-v1` profile with four anchors for its subjective
   dimensions, definitions for all four usability labels, and intermediate
   usability illustrations.
6. Author checked-in fixture, profile, rubric, case, and suite TOML assets.
   Give smoke minimal required scenarios and leave core goals ready for later
   expansion.
7. Render grouped `Suite composition` output with case counts and clear
   ordinary/safety wording. Provide `--strict-composition` for advisory-goal
   promotion.
8. Extend the Inspect adapter descriptor with profile and rubric
   identity/revision/digest. It does not render scoring prompts or execute
   scoring.
9. Update maintainer documentation and quickstart.
10. Update draft features 010–013 before their implementation begins:
    - 010 resolves a canonical assessment target, preserves profile/rubric
      identities and a privacy-reviewed immutable assessment-evidence reference.
    - 011 treats those identities as reuse compatibility inputs where relevant.
    - 012 consumes profile-driven 1–4 ratings, separate usability, objective
      deterministic gates, and judge-sourced semantic injection findings; it
      does not add an aggregate.
    - 013 compares compatible profile/rubric identities and named dimensions,
      distinguishing deterministic from judge-sourced gates.
11. Run focused tests, the smoke/core validation commands, full lint/format/type
    checks, and documentation checks. Verify no provider calls, raw prompt
    exposure, or ordinary-product CLI changes.

## Complexity Tracking

No constitution violation or complexity exception is required.
