# Feature Specification: Eval Safety Comparison

**Feature Branch**: `013-eval-baselines-comparison`
**Created**: 2026-06-11
**Status**: Draft

**Draft Note**: This specification describes proposed maintainer-only eval
tooling. It does not describe current gmuse behavior.

**Framework Alignment Update (2026-06-14)**: Replace first-class baseline
promotion and custom baseline artifacts with comparison between two local
Inspect eval logs. The initial automated gate is strict safety: fail on new hard
failures or clear deterministic validation regressions, report subjective judge
score movement as evidence, and mark incompatible comparisons inconclusive.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compare An Intended Improvement (Priority: P1)

As a maintainer, I want to compare a candidate Inspect eval run against a prior
reference Inspect eval run so I can tell whether a change meant as an
improvement introduced safety or deterministic regressions.

**Independent Test**: Compare two compatible scored Inspect logs and verify the
report includes shared cases, new/removed hard failures, production validation
changes, score movement, and compatibility status.

### User Story 2 - Fail On New Hard Failures (Priority: P1)

As a maintainer, I want the automated gate to fail when the candidate introduces
a new privacy leak, severe injection-following behavior, production validation
failure, or applicable `max_chars` failure.

**Independent Test**: Compare a reference log without hard failures to a
candidate log with one new hard failure and verify the command exits non-zero
and identifies the affected case.

### User Story 3 - Mark Incompatible Comparisons Inconclusive (Priority: P1)

As a maintainer, I want comparison to warn or mark the result inconclusive when
runs differ in suite, case set, fixture revisions, model/config, prompt version,
judge version, or scoring schema so I do not mistake incomparable evidence for a
clean result.

**Independent Test**: Compare logs with deliberate metadata mismatches and
verify the report identifies each mismatch and avoids a false pass.

### User Story 4 - Report Quality Movement Without Over-Gating (Priority: P2)

As a maintainer, I want judge score movement and case-level deltas visible, but I
do not want the first automated gate to fail solely on subjective score changes.

**Independent Test**: Compare logs with changed judge scores but no new hard
failures and verify the command reports deltas without failing the strict safety
gate.

## Requirements *(mandatory)*

- **FR-001**: The comparison command MUST consume two local Inspect eval logs:
  a reference log and a candidate log.
- **FR-002**: The command MUST compare stable case identities from spec 009 and
  scoring metadata from spec 012.
- **FR-003**: The command MUST report new, removed, and unchanged hard failures.
- **FR-004**: New privacy leak, severe injection-following, production
  validation failure, or applicable `max_chars` failure MUST fail the strict
  safety gate.
- **FR-005**: The command MUST report deterministic validation deltas separately
  from judge score deltas.
- **FR-006**: The command MUST report judge score movement and quality/category
  deltas when available, but MUST NOT fail solely on subjective score movement
  in v1.
- **FR-007**: The command MUST emit compatibility warnings for suite, case,
  fixture, model, config, prompt, judge, scorer, and schema mismatches.
- **FR-008**: Incompatible or insufficient metadata MUST produce
  `inconclusive` or `invalid` evidence classification rather than a clean pass.
- **FR-009**: The command MUST run offline without live candidate or judge calls.
- **FR-010**: Named baseline promotion and custom baseline artifact management
  are out of scope for v1; a prior Inspect log can serve as the reference.

## Key Entities

- **Comparison Request**: Reference Inspect log, candidate Inspect log, and gate
  mode.
- **Compatibility Warning**: Structured mismatch that affects confidence.
- **Case Delta**: Per-case hard-failure, validation, score, and category delta.
- **Safety Gate Result**: `passed`, `failed`, `inconclusive`, or `invalid`.
- **Comparison Report**: Durable local JSON report summarizing warnings, case
  deltas, and gate result.

## Success Criteria *(mandatory)*

- **SC-001**: In hard-failure tests, 100% of new privacy, injection, production
  validation, and applicable `max_chars` failures fail the strict safety gate.
- **SC-002**: In compatibility tests, 100% of configured metadata mismatches
  produce structured warnings.
- **SC-003**: Score-only movement without new hard failures does not fail the v1
  strict safety gate.
- **SC-004**: Comparison completes offline from saved Inspect logs.

## Assumptions

- Spec 010 provides Inspect logs with source case/model/config/prompt metadata.
- Spec 012 provides hard-failure and scoring metadata in Inspect logs.
- The first automated gate should be conservative: fail on new hard failures and
  deterministic regressions; report subjective quality movement for review.
