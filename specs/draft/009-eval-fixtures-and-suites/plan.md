# Implementation Plan: Eval Fixtures And Suites

**Branch**: `009-eval-fixtures-and-suites` | **Date**: 2026-06-11 | **Spec**: ../009-eval-fixtures-and-suites/spec.md
**Input**: Feature specification from `specs/draft/009-eval-fixtures-and-suites/spec.md`

## Summary

Create the maintainer-only foundation for gmuse evals by defining versioned,
reviewable fixture, case, suite, and rubric data plus a manual validation command
that can reconstruct temporary git repositories and verify staged diff digests
without any model credentials. This slice proves the offline eval substrate
before production-path runner, live-call budgeting, judge scoring, baseline
comparison, importer, or public benchmark work.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Standard library git subprocess usage already present
in `gmuse.git`, existing gmuse config/prompt validation knowledge, pytest, Ruff,
pyrefly; avoid adding runtime dependencies for normal package users

**Storage**: Checked-in maintainer fixture and suite files under the repository,
plus temporary git repositories created during validation

**Testing**: pytest unit tests for schema validation and fixture validation;
integration tests using temporary git repositories for reconstruct/stage/digest
behavior

**Target Platform**: Local Python CLI on Linux, macOS, and Windows for
maintainer development environments

**Project Type**: Single Python package with maintainer-only CLI/tooling

**Performance Goals**: Validate the initial smoke suite in under 30 seconds and
avoid network access during normal validation

**Constraints**: No provider credentials, live model calls, judge calls, or
network fixture import during validation; smoke must be a subset of core;
fixtures must not pre-truncate diffs; real OSS fixtures must include required
attribution

**Scale/Scope**: Initial smoke suite with a few cases and a path toward a
20-25 case core suite; large public benchmark and importer automation deferred

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution gates for this feature:

- **Code Quality Gate**: Pass. The feature can be isolated in maintainer eval
  modules and schema helpers without changing the ordinary generation path.
- **Testing Gate**: Pass. The plan requires unit coverage for schema validation
  and integration coverage for temporary git repository reconstruction.
- **UX Gate**: Pass. User-facing behavior is limited to maintainer commands with
  actionable validation messages and documentation.
- **Performance Gate**: Pass. Offline validation avoids provider calls and
  network access, with an explicit smoke-suite time target.
- **Security/Privacy Gate**: Pass. Fixture metadata distinguishes fake safety
  data from real source attribution and avoids storing functional secrets.
- **Release Discipline Gate**: Pass. Versioned schemas and suites are required
  from the first implementation.

Checklist:

- Code Quality Gate: Yes - keep eval foundation modular and maintainer-only.
- Testing Gate: Yes - cover schema, provenance, suite membership, and git digest checks.
- UX Gate: Yes - validation output must identify actionable fixture and suite errors.
- Performance Gate: Yes - no live calls or network work in normal validation.
- Security/Privacy Gate: Yes - require provenance and fake/nonfunctional safety markers.
- Release Discipline Gate: Yes - version fixture, suite, rubric, and validation artifacts.

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
src/gmuse/
├── evals/
│   ├── __init__.py
│   ├── fixtures.py        # fixture/case/rubric loading and validation
│   ├── suites.py          # suite loading, membership checks, coverage summary
│   └── validation.py      # temporary repo reconstruction and digest checks
└── cli/
    └── main.py            # maintainer eval validation command wiring if exposed through CLI

tests/
├── unit/
│   └── test_evals_fixtures.py
└── integration/
    └── test_evals_fixture_validation.py

docs/planning/evals/
├── requirements.md
└── implementation-plan.md
```

**Structure Decision**: Keep eval support inside the existing single package but
isolated under `gmuse.evals` so normal generation code remains unchanged.
Fixture files and suite definitions should be checked-in maintainer assets whose
format is documented by contracts in this spec.

## Complexity Tracking

No constitution violations are expected for this feature.

## Phase 0 - Outline & Research (Output: `research.md`)

Research focus areas:

- Decide how fixture patch data should be represented so validation can
  reconstruct a temporary repository without source clones.
- Decide how real, adapted, and synthetic provenance should be validated,
  including source license evidence and maintainer redistribution-review status.
- Decide how suite membership and coverage reporting should behave when balance
  is advisory rather than required.
- Decide how digest verification should define the canonical staged diff.

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

- Code quality remains satisfied by isolated eval modules.
- Testing remains satisfied by schema and temp-repo validation coverage.
- UX remains satisfied by actionable maintainer validation output.
- Performance remains satisfied by offline validation.
- Security/privacy remains satisfied by provenance, fake-secret requirements,
  and injection pattern coverage tags.
- Release discipline remains satisfied by versioned schemas.
