# Contract: Optional Inspect-Backed Reuse

This contract replaces the earlier custom resume-state file contract. gmuse does
not define `run-plan.json`, `outputs.jsonl`, `summary.json`, or a custom resume
ledger for v1.

## Objective

Avoid repeating completed generations after interruption when Inspect provides a
safe and simple rerun/resume path. This is a convenience, not a correctness or
spend-safety requirement.

## Compatibility Fields

Check suite, fixture, case, model, effective generation settings, prompt version,
and log schema before any provider calls. For each reused entry, require
verified staged-diff and rendered prompt hashes that match the planned inputs.

## Rules

- An incompatible, missing, or unverifiable required identity or hash makes
  the entry ineligible for reuse.
- Apply normal plan limits and confirmation before generating a new candidate.
- Preserve prior Inspect logs and their generated messages.
- If Inspect cannot safely reuse completed entries, rerun bounded samples.

## Out of Scope

- Duplicate terminal-record detection in custom JSONL files.
- Retryable operational-error ledgers.
- Per-attempt provider-call budget accounting.
- Manual artifact repair workflows.
