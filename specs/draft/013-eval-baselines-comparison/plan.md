# Implementation Plan: Eval Safety Comparison

**Branch**: `013-eval-baselines-comparison` | **Date**: 2026-06-11 | **Spec**: ../013-eval-baselines-comparison/spec.md

## Summary

Add a maintainer-only comparison command that compares two local Inspect eval
logs: a reference run and a candidate run. The v1 automated gate is strict
safety. It fails on new hard failures or clear deterministic validation
regressions, reports judge score movement as evidence, and marks incompatible
comparisons inconclusive or invalid. Custom baseline promotion and baseline
artifact management are deferred.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Inspect AI log reading/analysis APIs, spec 009 fixture
and case identities, spec 012 scoring metadata, Typer CLI, Pydantic models for
report validation, pytest, Ruff, pyrefly

**Storage**: Local comparison report JSON written near the candidate log or to
an explicit `--output` path. Inspect logs remain the source evidence.

**Testing**: pytest unit and integration tests with small saved Inspect log
fixtures or log-like test objects.

**Constraints**: Offline only. No live candidate calls, judge calls, hosted
platforms, public recommendation pages, or broad model-ranking claims.

## Constitution Check

- **Code Quality Gate**: Pass. Comparison logic is a small library over Inspect
  logs plus typed report models.
- **Testing Gate**: Pass. Compatibility warnings, hard-failure deltas, and gate
  outcomes are deterministic.
- **UX Gate**: Pass. Output names whether evidence passed, failed, is
  inconclusive, or invalid.
- **Performance Gate**: Pass. Comparison runs offline over local logs.
- **Security/Privacy Gate**: Pass. No new raw prompt persistence is introduced.
- **Release Discipline Gate**: Pass. Report schema and warning categories are
  versioned.

## Project Structure

```text
tools/
└── evals/
    └── gmuse_evals/
        ├── cli.py              # compare command wiring
        ├── compare.py          # compatibility checks and case deltas
        ├── inspect_logs.py     # log reading helpers
        └── reports.py          # comparison report serialization

tests/
├── integration/
│   └── test_eval_compare_cli.py
└── unit/
    ├── test_eval_compare.py
    └── test_eval_reports.py
```

## Phase 0 - Research

- Define minimum Inspect log metadata required for comparison.
- Define compatibility warnings and evidence classification.
- Define strict safety gate rules.
- Decide report shape and non-zero exit behavior.

## Phase 1 - Design & Contracts

- `data-model.md`: comparison request, warning, case delta, gate result, report.
- `contracts/comparison-cli.md`: command contract.
- `contracts/baseline-artifact.md`: replaced by reference-log contract note.
- `quickstart.md`: validation guide.

## Phase 2 - Future Implementation Planning

1. Add Inspect log readers that extract gmuse metadata from reference and
   candidate runs.
2. Add compatibility checks for suite, cases, fixtures, model/config, prompt,
   judge, scorer, and schema.
3. Add per-case hard-failure and deterministic validation deltas.
4. Add optional score/category deltas for review evidence.
5. Add strict safety gate classification and command exit behavior.
6. Add report serialization with stable warning and delta schemas.
7. Add tests for new hard failures, metadata mismatches, score-only movement,
   and offline operation.
