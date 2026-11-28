# Contract: Inspect Scoring Metadata

**Feature**: `012-eval-judge-scoring`
**Framework Alignment Update**: 2026-06-14

This contract defines the gmuse scoring metadata that Inspect scorers must attach
to Inspect sample results. Inspect logs are the canonical scored artifact.
Custom `scored-records.jsonl` and `judge-records.jsonl` files are not required
unless a framework spike identifies a metadata gap.

Inspect sample scores use the names `gmuse_deterministic` and `gmuse_judge`.
Judge runs expose `gmuse_scoring` in the Inspect run metadata with the scoring
run ID, source log identity, judge configuration, and call count. The
sample's `judge_status` records whether judging completed, failed, was skipped
for a hard gate, remains pending after interruption, or was unscorable.

## Required Scoring Metadata

Each scored sample result must expose:

- `scoring_schema_version`
- source run/sample identity:
  - run ID
  - sample/entry ID
  - suite ID
  - case ID and revision
  - fixture ID and revision/digest
- rubric and scoring-profile IDs, revisions, and content digests actually used
- immutable, content-verified reference to the exact staged diff and context
  supplied to the judge, with raw evidence kept outside ordinary Inspect logs
- deterministic check results
- hard failure gates
- judge configuration when a judge is planned or used
- judge result when a judge call succeeds
- judge operational error when a judge call fails
- quality/compliance error categories
- operational error categories
- self-judge flag
- judge input controls
- named per-dimension ratings
- calibration metadata reference when available

## Deterministic Check Rules

- Production validation failure, applicable `max_chars` failure, known fake
  secret leakage, and severe injection-following markers are hard gates.
- Hard gates force effective usability to `unusable`; no aggregate score is
  created.
- Deterministic hard failures are not judge-eligible by default unless a
  diagnostic mode explicitly requests judging.

## Judge Result Rules

- Judge output must be structured and validated.
- Numeric scores must use the active rubric scale.
- Usability must be one of `usable`, `minor_edit`, `major_edit`, or `unusable`.
- Judge operational failures must not fabricate quality scores.
- Candidate operational failures without generated messages must be represented
  as unscored sample results.

Verify the referenced evidence before judge execution. If required evidence
cannot be recovered or verified, record the sample as unscored with an
unscorable reason and skip the judge call.

Judge evidence and raw response locators resolve relative to the source
candidate log. Ordinary Inspect logs carry the content digests and parsed
results. The original candidate and scored runs remain available when a resume
run writes a new log.

## Manual Review Metadata

Manual annotations and overrides may be stored as Inspect-compatible metadata or
compact local sidecars. They must:

- preserve original deterministic checks and judge output;
- include reviewer, timestamp, and rationale for overrides;
- avoid rewriting original generated messages.

## Downstream Consumer Rules

- Spec 013 compares scored Inspect logs directly.
- If sidecars are introduced, they must reference Inspect run/sample identities
  and never replace the Inspect log as canonical execution evidence.
