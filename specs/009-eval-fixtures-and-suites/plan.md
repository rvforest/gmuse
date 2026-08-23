# Implementation Plan: Eval Fixtures And Suites

**Branch**: `009-eval-fixtures-and-suites` | **Date**: 2026-06-11 | **Spec**: ../009-eval-fixtures-and-suites/spec.md
**Input**: Feature specification from `specs/draft/009-eval-fixtures-and-suites/spec.md`

## Summary

Create the maintainer-only foundation for gmuse evals by defining versioned,
reviewable fixture, case, suite, and rubric data plus a manual validation command
that can reconstruct temporary git repositories and verify staged diff digests
without any model credentials. This slice proves the offline eval substrate
before downstream Inspect AI-based production-path runner, scoring, strict safety
comparison, importer, or public benchmark work.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Typer for the maintainer tool CLI; Pydantic v2 as an
explicit development dependency for structural TOML schema validation;
`license-expression` for SPDX-style source license expression validation;
existing `gmuse.git` staged-diff behavior for fidelity; `tomli`/`tomllib` and
`tomlkit` for TOML parsing/editing support already present in the project;
pytest, Ruff, pyrefly; avoid adding runtime dependencies for normal package
users; expose structured in-process helpers for later Inspect AI datasets,
solvers, and scorers without making them public product APIs

**Storage**: Checked-in maintainer fixture and suite TOML files under root
`evals/`, plus temporary git repositories created during validation

**Testing**: pytest unit tests with temporary TOML assets for schema/reference
failure cases; integration tests using temporary git repositories for
reconstruct/stage/digest behavior; one integration test validates the checked-in
`evals/suites/smoke.toml` suite

**Target Platform**: Local Python CLI on Linux, macOS, and Windows for
maintainer development environments

**Project Type**: Single Python package plus maintainer-only repository tooling
outside `src/`

**Performance Goals**: Validate the initial smoke suite in under 30 seconds and
avoid network access during normal validation

**Constraints**: No provider credentials, live model calls, judge calls, public
`gmuse` CLI command, or network fixture import during validation; smoke must be
a subset of core; fixtures must not pre-truncate diffs; real OSS fixtures must
include required attribution when introduced; initial checked-in smoke fixtures
are synthetic-only

**Scale/Scope**: Initial smoke suite with two synthetic cases and a path toward
a 20-25 case core suite; large public benchmark and importer automation deferred

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution gates for this feature:

- **Code Quality Gate**: Pass. The feature can be isolated in maintainer tool
  modules under `tools/evals/` and schema helpers without changing the ordinary
  generation path.
- **Testing Gate**: Pass. The plan requires unit coverage for schema validation
  and integration coverage for temporary git repository reconstruction.
- **UX Gate**: Pass. User-facing behavior is limited to maintainer commands with
  actionable validation messages and documentation.
- **Performance Gate**: Pass. Offline validation avoids provider calls and
  network access, with an explicit smoke-suite time target.
- **Security/Privacy Gate**: Pass. Fixture metadata distinguishes fake safety
  data from real source attribution and avoids storing functional secrets.
- **Release Discipline Gate**: Pass. Versioned schemas and suites are required
  from the first implementation and must expose stable identities usable from
  Inspect AI eval samples.

Checklist:

- Code Quality Gate: Yes - keep eval foundation modular, maintainer-only, and
  outside the installable `src/gmuse` package.
- Testing Gate: Yes - cover schema, provenance, suite membership, and git digest checks.
- UX Gate: Yes - validation output must identify actionable fixture and suite errors.
- Performance Gate: Yes - no live calls or network work in normal validation.
- Security/Privacy Gate: Yes - require provenance and fake/nonfunctional safety markers.
- Release Discipline Gate: Yes - version fixture, suite, rubric, and validation
  artifacts; keep stable IDs/digests for downstream Inspect logs and comparison.

## Project Structure

### Documentation (this feature)

```text
specs/draft/009-eval-fixtures-and-suites/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── fixture-schema.md
│   ├── suite-schema.md
│   └── validation-cli.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
evals/
├── fixtures/
├── rubrics/
├── cases/
└── suites/
    ├── smoke.toml
    └── core.toml

tools/
├── __init__.py
└── evals/
    ├── __init__.py
    └── gmuse_evals/
        ├── __init__.py
        ├── __main__.py      # module entrypoint
        ├── cli.py           # Typer app for maintainer commands
        ├── models.py        # Pydantic structural models
        ├── load.py          # TOML loading and path resolution
        ├── validate.py      # structured validation report and validated suite data
        ├── inspect_adapter.py # converts validated cases into Inspect samples
        └── git_reconstruct.py # temp repo reconstruction and staged diff checks

tests/
├── unit/
│   └── test_eval_foundation_*.py
└── integration/
    └── test_eval_foundation_*.py
```

**Structure Decision**: Keep maintainer eval implementation outside `src/gmuse`
so the installed product package is not expanded with draft eval tooling. Keep
eval assets under root `evals/` so fixtures, rubrics, cases, and suites are
reviewable data rather than product code. The tool may import `gmuse.git` for
production staged-diff fidelity, using a temporary working-directory context
rather than changing product git helpers for this first slice. The CLI is
human-readable, but the underlying loader, validator, and reconstruction modules
should return structured objects that spec 010 can call directly when building
Inspect AI datasets/samples instead of parsing CLI text.

## Complexity Tracking

No constitution violations are expected for this feature.

## Phase 0 - Outline & Research (Output: `research.md`)

Research focus areas:

- Decide how fixture patch data should be represented so validation can
  reconstruct a temporary repository without source clones.
- Decide how TOML fixture, rubric, case, and suite files are organized under
  root `evals/`.
- Decide how Pydantic structural validation and custom domain validation divide
  responsibilities.
- Decide how real, adapted, and synthetic provenance should be validated,
  including source license evidence and maintainer redistribution-review status.
- Decide how suite membership and coverage reporting should behave when balance
  is advisory rather than required.
- Decide how digest verification should define the canonical staged diff.
- Decide the first smoke fixture set: two synthetic fixtures, one with actual
  synthetic history commits and one injection-tagged fixture that validates
  metadata/reconstruction without model behavior.
- Decide the structured helper boundary that lets the Inspect-based
  production-path runner reuse suite loading, validation reports, validated suite
  data, and temporary repository reconstruction without shelling out to the
  validation CLI.

## Phase 1 - Design & Contracts (Output: `data-model.md`, `contracts/`, `quickstart.md`)

Design outputs:

- `data-model.md` defines `EvalFixture`, `FixtureProvenance`, `EvalRubric`,
  `EvalCase`, `EvalSuite`, and `ValidationReport`.
- `contracts/fixture-schema.md` documents required fixture and rubric fields.
- `contracts/suite-schema.md` documents suite membership and policy fields.
- `contracts/validation-cli.md` documents the maintainer validation command and
  expected validation outcomes.
- `quickstart.md` explains how to validate the initial smoke suite and inspect
  failure output.

Post-design constitution check:

- Code quality remains satisfied by isolated maintainer tool modules outside
  `src/gmuse` with shared internal helper APIs for later eval slices.
- Testing remains satisfied by schema, temp-repo validation coverage, and
  validation of checked-in synthetic smoke fixtures.
- UX remains satisfied by actionable maintainer validation output.
- Performance remains satisfied by offline validation.
- Security/privacy remains satisfied by provenance, fake-secret requirements,
  and injection pattern coverage tags.
- Release discipline remains satisfied by versioned schemas.
