# Feature Specification: Eval Live Guardrails

**Feature Branch**: `011-eval-live-budgeting-resume`

**Created**: 2026-06-11

**Status**: Draft

**Draft Note**: This specification describes proposed maintainer-only eval
tooling. It does not describe current gmuse behavior.

**Framework Alignment Update (2026-06-14)**: This feature is narrowed from a
custom provider-call budgeting and JSONL resume subsystem to live-run guardrails
around Inspect AI execution. The objective is preventing runaway spend through
preflight display, explicit confirmation, and configured Inspect/gmuse limits.
Resume is a convenience to use when Inspect provides clean rerun or partial-run
behavior; custom resume accounting is not a v1 requirement.

**Input**: User description: "Live eval guardrails: preflight planning, explicit
confirmation, Inspect/gmuse spend limits, local logs, and optional
framework-supported rerun/resume. Depend on Inspect-backed eval runner logs from
spec 010 and fixtures from spec 009. Do not include judge rubric design, custom
resume accounting, baseline promotion/comparison, fixture importer, or public
benchmark recommendations except as dependencies/out of scope."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview Live Eval Work Before Calls (Priority: P1)

As a maintainer preparing a live eval run, I want gmuse to show the planned
suite, cases, models, sample count, configured limits, and log location before
making provider calls so I can verify the run size and cost exposure.

**Independent Test**: Run a live eval command with `--plan` and verify the
command displays planned work and configured guardrails while making zero
provider calls and writing no live sample results.

### User Story 2 - Require Confirmation And Guardrails (Priority: P1)

As a maintainer running evals manually or from controlled automation, I want live
calls to require explicit guardrails and confirmation so copied commands cannot
start unbounded work.

**Independent Test**: Attempt live runs with missing limits, exceeded sample
limits, interactive confirmation, and non-interactive `--yes`. Verify provider
calls begin only after fixture validation, guardrail validation, plan display,
and confirmation requirements pass.

### User Story 3 - Preserve Inspect Logs During Interruption (Priority: P2)

As a maintainer running a live eval, I want completed Inspect sample results to
remain available after interruption so I can inspect partial work and avoid
rerunning it when the framework supports safe reuse.

**Independent Test**: Interrupt a bounded live run after at least one sample
completes and verify the local Inspect log remains readable.

### User Story 4 - Avoid Repeating Work When Framework Support Is Clean (Priority: P2)

As a maintainer, I want gmuse to use Inspect-supported rerun/resume behavior when
it is safe and simple, but I do not want gmuse to build a custom resume ledger
just to avoid small bounded reruns.

**Independent Test**: If Inspect reuse is enabled, rerun with compatible suite,
case, model, config, prompt, fixture, and log metadata and verify completed work
is not repeated. If reuse is unavailable, verify the rerun still requires the
same guardrails and confirmation.

### Edge Cases

- `--plan` must never make provider calls.
- A live run with zero selected cases or zero selected models must finish before
  provider calls and explain why.
- Missing or invalid guardrails must fail before provider calls.
- Planned samples above `--limit-samples` must fail before provider calls.
- Non-interactive live runs without `--yes` must fail before provider calls.
- Fixture validation failures from spec 009 must fail before provider calls.
- Missing or corrupt Inspect logs must reject optional reuse before provider
  calls.
- Reuse must not overwrite existing generated messages.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Live eval runs MUST display a pre-call plan with suite identity,
  case count, selected models, planned sample count, configured limits, and
  Inspect log location.
- **FR-002**: Live eval runs MUST require explicit guardrails for non-trivial
  provider work.
- **FR-003**: Guardrails MAY use Inspect-native sample, token, cost, time, or
  concurrency limits.
- **FR-004**: gmuse MUST reject planned work before provider calls when the
  planned sample count exceeds `--limit-samples`.
- **FR-005**: gmuse MUST require interactive confirmation before live calls
  unless the maintainer supplies `--yes`.
- **FR-006**: `--yes` MUST NOT imply unlimited work and MUST NOT suppress plan
  output or guardrail validation.
- **FR-007**: `--plan` MUST make zero provider calls and write no live sample
  results.
- **FR-008**: Completed live execution evidence MUST be stored in local Inspect
  logs from spec 010.
- **FR-009**: gmuse SHOULD use Inspect-supported rerun/resume behavior when it is
  safe and simple.
- **FR-010**: gmuse MUST NOT introduce a custom JSONL resume ledger in v1 solely
  to avoid repeated generations.
- **FR-011**: Optional reuse MUST reject incompatible suite, fixture, case,
  model, generation config, prompt version, or log schema metadata before
  provider calls.
- **FR-012**: Default repository automation MUST NOT expose a live-call path or
  require provider credentials.
- **FR-013**: This feature MUST NOT define judge execution, judge rubric design,
  custom scoring artifacts, baseline promotion, baseline comparison, fixture
  importer behavior, or public benchmark recommendations.

### Key Entities

- **Live Run Plan**: Pre-call plan for selected suite cases, models, sample
  count, guardrails, confirmation mode, and Inspect log location.
- **Guardrail Configuration**: Explicit limits that bound live work.
- **Inspect Log Reference**: Local Inspect log evidence produced by spec 010.
- **Optional Reuse Compatibility**: Metadata used only when Inspect-backed
  rerun/resume is enabled.

## Success Criteria *(mandatory)*

- **SC-001**: In all live-run acceptance tests, no provider call occurs before
  plan display, guardrail validation, and confirmation requirements pass.
- **SC-002**: Commands with missing guardrails or exceeded `--limit-samples`
  fail before provider calls.
- **SC-003**: `--plan` performs zero provider calls in automated tests.
- **SC-004**: Interrupted runs preserve readable Inspect logs for completed
  samples.
- **SC-005**: Optional reuse rejects incompatible metadata before provider calls.

## Assumptions

- Spec 009 provides validated fixture and suite identities, revisions, case
  selections, and staged-diff reconstruction guarantees.
- Spec 010 provides Inspect-backed runner logs with gmuse metadata.
- The spend-control objective can be satisfied by preflight display,
  confirmation, and configured limits rather than exact custom call accounting.
- Eval tooling is maintainer-only and not part of ordinary `gmuse msg`,
  `gmuse generate`, or commit-message workflows.
