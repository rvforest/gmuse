# Implementation Plan: Eval Baselines and Comparison

**Branch**: `013-eval-baselines-comparison` | **Date**: 2026-06-11 | **Spec**: ../013-eval-baselines-comparison/spec.md
**Input**: Feature specification from `specs/draft/013-eval-baselines-comparison/spec.md`


## Summary

Add maintainer-only eval baseline and comparison artifacts on top of the eval
runner outputs from spec 010 and scored outputs from spec 012. The feature
introduces an explicit promotion step that converts a reviewed scored run into a
stable baseline artifact, plus comparison commands that produce offline,
pairwise evidence for same-model regression review and explicit optional
different-model benchmark review.

The implementation should preserve generated messages, score metadata, hard
failure flags, prompt hashes, prompt size/token estimates, model/config/suite
metadata, judge metadata, and schema versions while stripping debug-only fields
from promoted baselines by default. Comparison reports should expose warnings for
incompatible versions or configs and should never collapse evidence into an
automatic accept/reject decision beyond hard-failure flags and compatibility
severity.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Existing gmuse eval artifacts from specs 010 and 012,
standard library JSON/path/date handling, Typer CLI surfaces, pytest, Ruff,
pyrefly

**Storage**: Local filesystem artifacts for eval results, scored outputs,
promoted baselines, and comparison reports; no new persistent service

**Testing**: pytest unit, contract, and integration tests with small checked-in
sample artifacts and temporary output directories

**Target Platform**: Maintainer-only local Python CLI on Linux, macOS, and
Windows; default CI must not require provider credentials

**Project Type**: Single Python package (`src/gmuse`) with maintainer-focused
eval CLI helpers

**Performance Goals**: Generate comparison reports offline without live model or
judge calls; process smoke and core-sized artifact sets in seconds; preserve
memory usage by streaming or incremental loading for larger future benchmark
artifacts where practical

**Constraints**: Promotion must be explicit; baseline artifacts must be
versioned; comparison must be reproducible from saved artifacts; same-model
regression mode must warn strongly on model/config differences; benchmark mode
must be explicit for different-model comparisons; no fixture importer or public
recommendation pages are included

**Scale/Scope**: Smoke and core eval suites from upstream eval specs, with data
model choices that can extend to larger private benchmark artifacts later

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution gates for this feature:

- **Code Quality Gate**: Pass. The feature can be implemented as small
  eval-specific baseline, compatibility, and reporting modules with typed public
  functions and docstrings, keeping artifact parsing and comparison logic
  testable without live provider calls.
- **Testing Gate**: Pass. Contract tests can lock baseline artifact and
  comparison report shapes, unit tests can cover compatibility classification
  and pairwise delta calculation, and integration tests can exercise promotion
  and comparison CLI flows with local sample artifacts.
- **UX Gate**: Pass. The CLI is maintainer-focused but still requires clear
  command help, actionable promotion rejection messages, explicit benchmark mode,
  and structured compatibility warnings.
- **Performance Gate**: Pass. Comparison is offline and should avoid new model
  calls. The plan preserves summary and per-case data while allowing streaming or
  incremental parsing for future larger result sets.
- **Security/Privacy Gate**: Pass. Baseline promotion strips debug-only fields by
  default, avoids secret persistence, and relies on existing privacy hard-failure
  classifications from scored artifacts.
- **Release Discipline Gate**: Pass. Artifact schemas are versioned, warnings
  cover schema/config differences, and docs/contracts capture compatibility
  expectations before implementation.

Checklist:

- Code Quality Gate: Yes — use focused eval modules and typed contracts.
- Testing Gate: Yes — add contract, unit, and integration coverage for artifact
  shapes and comparison behavior.
- UX Gate: Yes — include explicit promotion, explicit benchmark mode, and
  actionable warnings.
- Performance Gate: Yes — offline report generation and no live calls.
- Security/Privacy Gate: Yes — stripped baselines by default and hard-failure
  preservation.
- Release Discipline Gate: Yes — versioned artifacts and compatibility warnings.

## Project Structure

### Documentation (this feature)

```text
specs/draft/013-eval-baselines-comparison/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── contracts/
    ├── baseline-artifact.md
    └── comparison-cli.md
```

### Source Code (repository root)

```text
src/gmuse/
├── evals/
│   ├── artifacts.py          # shared loading/validation for spec 010/012 artifacts
│   ├── baselines.py          # promotion validation and baseline artifact writing
│   ├── compare.py            # compatibility checks and pairwise deltas
│   ├── reports.py            # comparison summary/report serialization
│   └── cli.py                # maintainer eval baseline/comparison commands
└── cli/
    └── main.py               # command registration if eval commands are top-level

tests/
├── contract/
│   └── test_eval_baseline_contracts.py
├── integration/
│   └── test_eval_baseline_cli.py
└── unit/
    ├── test_eval_baselines.py
    ├── test_eval_compare.py
    └── test_eval_reports.py

docs/source/
└── development/
    └── evals.md              # maintainer-only eval workflow documentation
```

**Structure Decision**: Keep the feature inside the existing Python package and
eval tooling area. The comparison logic should be usable as a small library so
CLI commands, tests, and future private benchmark tooling share the same
compatibility and delta calculations.

## Complexity Tracking

No constitution violations are expected for this feature.

## Phase 0 — Outline & Research (Output: `research.md`)

Research focus areas:

- Define the baseline artifact boundary: which fields are required from spec 010
  result artifacts and spec 012 scored outputs, and which debug-only fields are
  stripped by default.
- Define promotion validation rules so baselines are intentionally created only
  from complete, scored, compatible result sets.
- Define same-model regression compatibility rules and severity levels for suite,
  case, model, config, prompt, judge, scoring, and schema mismatches.
- Define different-model benchmark mode rules so model differences are allowed
  only when explicitly requested and the report does not become a recommendation
  page.
- Define pairwise delta calculations for scores, hard failures, prompt
  size/tokens, first-shot success, and error categories.

Output artifact:

- `specs/draft/013-eval-baselines-comparison/research.md`

## Phase 1 — Design & Contracts (Outputs: `data-model.md`, `contracts/`, `quickstart.md`)

Design artifacts:

- Baseline, comparison, warning, and pairwise delta data model:
  `specs/draft/013-eval-baselines-comparison/data-model.md`
- Baseline artifact contract:
  `specs/draft/013-eval-baselines-comparison/contracts/baseline-artifact.md`
- Promotion and comparison CLI contract:
  `specs/draft/013-eval-baselines-comparison/contracts/comparison-cli.md`
- Maintainer validation walkthrough:
  `specs/draft/013-eval-baselines-comparison/quickstart.md`

Post-design constitution re-check:

- Code Quality: artifact parsing, baseline promotion, compatibility checking, and
  report serialization remain separate and testable.
- Testing: contract tests cover schema shape; unit tests cover warning severity
  and pairwise deltas; integration tests cover CLI promotion/comparison flows.
- UX: maintainer commands require explicit promotion and explicit benchmark mode,
  with actionable incompatibility warnings.
- Performance: all comparison report generation is offline from saved artifacts.
- Security/Privacy: debug-only fields are stripped by default and hard-failure
  flags preserve privacy/injection evidence.
- Release Discipline: baseline and report schemas are versioned and comparison
  warnings surface schema/rubric/prompt/judge changes.

## Phase 2 — Future Implementation Planning

Planned implementation steps:

1. Add versioned artifact readers that validate the required spec 010 result
   metadata and spec 012 score metadata needed for baseline promotion and
   comparison.
2. Implement baseline promotion validation:
   - require explicit source artifact, baseline label, and output path,
   - reject unscored or incomplete result sets,
   - reject missing suite/case/model/config/prompt/judge/schema metadata,
   - strip debug-only fields by default,
   - optionally retain debug fields behind an explicit maintainer flag.
3. Define and serialize the promoted baseline artifact shape with generated
   messages, scores, hard-failure flags, prompt metadata, model/config metadata,
   suite/case metadata, judge metadata, manual override metadata, and source
   artifact references.
4. Implement compatibility checks that compare baseline and candidate metadata
   for suite version, suite membership, case IDs, case revisions, fixture
   revisions, model identity, generation config, prompt version, judge model,
   judge prompt version, rubric version, scoring schema version, and artifact
   schema version.
5. Implement same-model regression comparison mode that treats model/config
   mismatches as high-severity incompatibilities and labels output as degraded or
   invalid regression evidence when appropriate.
6. Implement explicit different-model benchmark mode that permits model
   differences while preserving all other compatibility warnings and avoiding
   recommendations or accept/reject decisions.
7. Implement pairwise case matching and delta calculation:
   - per-dimension score deltas,
   - hard-failure new/removed/changed flags,
   - prompt hash and prompt size/token deltas,
   - first-shot success deltas,
   - quality/compliance error category deltas,
   - operational error category deltas.
8. Implement report serialization with summary counts, compatibility warnings,
   pairwise case records, missing/extra case records, and source artifact
   references.
9. Add maintainer CLI commands for promotion and comparison with clear help,
   dry-run/validation output, non-interactive behavior, and explicit benchmark
   mode.
10. Add contract, unit, and integration tests using small local sample artifacts
    that do not require provider credentials or live judge calls.
11. Document the maintainer workflow in development docs, including promotion
    review expectations, compatibility warning interpretation, and the boundary
    between regression evidence and benchmark evidence.
