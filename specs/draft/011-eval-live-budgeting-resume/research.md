# Research: Eval Live Guardrails

## Decision: Use guardrails, not custom provider-call accounting

**Rationale**: The objective is to prevent runaway spend. Exact provider-call
budget accounting is not inherently valuable if Inspect and gmuse can provide
clear preflight planning, confirmation, and execution limits. Keeping the
guardrail model broad lets the implementation use Inspect-native sample, token,
cost, time, and concurrency limits where available.

**Alternatives considered**:

- Custom `--max-calls` ledger: rejected because it duplicates framework
  execution concerns and was only a means to the spend-control objective.
- Currency-only budgets: rejected because provider pricing and support vary.
- No limits beyond confirmation: rejected because copied commands and
  non-interactive runs still need hard guardrails.

## Decision: Always display the live plan before provider calls

**Rationale**: Maintainers should see selected suite, cases, models, sample
count, configured limits, and Inspect log location before live work starts.
`--yes` may skip the prompt, but it must not hide the plan.

**Alternatives considered**:

- Suppress plan output with `--yes`: rejected because logs from non-interactive
  runs should still show what was authorized.
- Require interactive prompts for all live runs: rejected because maintainers may
  run explicit bounded evals in controlled automation.

## Decision: `--plan` is zero-call and writes no live sample results

**Rationale**: Planning mode is for reviewing planned work and limits. It should
not create provider outputs or confusing partial run evidence.

**Alternatives considered**:

- Write a custom plan artifact: rejected because Inspect logs are canonical and
  plan display can be reproduced from the same task construction path.

## Decision: Rely on Inspect logs, not custom incremental JSONL

**Rationale**: Spec 010 adopts Inspect as the local execution/logging framework.
This feature should not reintroduce custom `outputs.jsonl` or `summary.json`
state solely for live guardrails.

**Alternatives considered**:

- Extend the old custom artifact layout for live accounting: rejected because it
  fights the framework adoption and increases maintenance.

## Decision: Resume is a convenience, not a v1 requirement

**Rationale**: Avoiding repeated generations after an interruption is useful,
but suite sizes are expected to be small at first and spend guardrails are the
required safety mechanism. If Inspect offers safe rerun/resume behavior, gmuse
should use it. If not, v1 may rerun bounded samples rather than build a custom
resume subsystem.

**Alternatives considered**:

- First-class custom resume compatibility fingerprints and ledgers: rejected as
  too much machinery for a convenience feature.
- Delete all partial-run reuse concerns: rejected because the design should
  remain open to thin Inspect-backed reuse.

## Phase 1 implications

- CLI contracts should name limits and confirmation, not `--max-calls`.
- Data models should represent planned work and guardrails, not custom output
  records.
- Resume contracts should document compatibility expectations for optional
  Inspect-backed reuse, not define gmuse-owned resume files.
