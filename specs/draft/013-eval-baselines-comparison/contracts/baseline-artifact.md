# Contract: Reference Log

The previous baseline artifact contract is superseded for v1.

## Decision

Use a prior local Inspect eval log as the reference input for comparison. Do not
create a promoted baseline artifact by default.

## Required Reference Log Metadata

The reference Inspect log must expose:

- suite ID and version/revision
- case IDs and revisions
- fixture IDs and revisions/digests
- model metadata
- generation config metadata
- prompt version
- production validation outcomes
- deterministic hard-failure gates from spec 012
- judge/scoring metadata when available
- gmuse eval metadata schema version

## Rules

- A missing required field produces an `invalid` or `inconclusive` comparison
  result.
- Named baseline promotion may be added later as a convenience layer over
  Inspect logs.
- Comparison must not require copying full Inspect logs into a custom baseline
  JSON artifact.
