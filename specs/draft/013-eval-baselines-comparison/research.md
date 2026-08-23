# Phase 0 Research: Eval Safety Comparison

## Decision: Compare Inspect logs directly

**Rationale**: Specs 010-012 adopt Inspect logs as canonical execution and
scoring evidence. Comparison should use those logs directly instead of promoting
custom baseline artifacts before there is implementation experience.

**Alternatives considered**:

- Custom baseline JSON artifacts: deferred because they duplicate Inspect logs
  and add workflow before the core objective is proven.
- Hosted comparison dashboards: rejected because evals must remain local and
  account-free.

## Decision: Use strict safety as the first automated gate

**Rationale**: The maintainer's first automated question is whether an intended
improvement introduced unacceptable safety or deterministic regressions.
Subjective judge scores are useful evidence, but should not drive the first
automated pass/fail gate.

**Alternatives considered**:

- Threshold gate over aggregate judge scores: rejected for v1 because it can
  over-trust subjective scoring.
- Case-count improvement gate: rejected for v1 because it requires mature
  scoring calibration and policy choices.

## Decision: Mark incompatible evidence inconclusive

**Rationale**: Model/config, fixture, prompt, judge, or schema mismatches can
make a comparison misleading. The command should still produce evidence when it
can, but should avoid a clean pass when compatibility is weak.

**Alternatives considered**:

- Reject every mismatch: rejected because exploratory comparisons can still be
  useful.
- Ignore mismatches: rejected because it would create false confidence.

## Decision: Keep named baselines as a future convenience

**Rationale**: A prior Inspect log can serve as the reference for v1. Named
baseline promotion may become useful later for workflow ergonomics, but it is
not necessary to answer whether a candidate run introduced hard failures.

**Alternatives considered**:

- Require promotion before every comparison: rejected because it adds ceremony
  and custom artifacts before the comparison rules have been exercised.

## Phase 1 implications

- Data model centers on comparison reports, warnings, case deltas, and gate
  results.
- Contracts accept `--reference-log` and `--candidate-log`.
- Reports are durable JSON summaries that point to Inspect logs.
