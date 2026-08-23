# Contract: Optional Inspect-Backed Reuse

This contract replaces the earlier custom resume-state file contract. gmuse does
not define `run-plan.json`, `outputs.jsonl`, `summary.json`, or a custom resume
ledger for v1.

## Objective

Avoid repeating completed generations after interruption when Inspect provides a
safe and simple rerun/resume path. This is a convenience, not a correctness or
spend-safety requirement.

## Compatibility Fields

Any reuse attempt must compare:

- suite ID and revision
- selected case IDs
- fixture revisions or digests
- candidate model set
- prompt-affecting generation config
- prompt version
- Inspect task/log schema version when available
- gmuse eval metadata schema version

## Rules

- Missing or corrupt Inspect logs reject reuse before provider calls.
- Incompatible metadata rejects reuse or forces a fresh run before provider
  calls.
- Reuse must not overwrite generated messages in existing Inspect logs.
- If Inspect does not provide safe partial-run reuse for a scenario, gmuse may
  rerun bounded samples instead of implementing custom bookkeeping.

## Out of Scope

- Duplicate terminal-record detection in custom JSONL files.
- Retryable operational-error ledgers.
- Per-attempt provider-call budget accounting.
- Manual artifact repair workflows.
