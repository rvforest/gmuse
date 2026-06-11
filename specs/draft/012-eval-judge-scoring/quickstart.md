# Quickstart: Eval Judge And Scoring Validation

**Date**: 2026-06-11
**Feature**: `012-eval-judge-scoring`

This guide describes how maintainers should validate the judge scoring feature
after implementation. Commands are illustrative until tasks define exact CLI
names.

## Prerequisites

- Eval fixtures and suites from the fixture foundation spec are available.
- Production-path runner outputs from spec 010 exist for at least the smoke
  suite, including `outputs.jsonl` and `summary.json`.
- Live-call budgeting and resume behavior from spec 011 is available, including
  `candidate-records.jsonl`, optional `judge-records.jsonl`, and `run.json`
  compatibility metadata.
- Provider credentials are configured only for manual live judge runs.

## Validate Deterministic Checks Offline

1. Prepare runner output records that include:
   - A valid generated message.
   - A production validation failure.
   - A `max_chars` violation.
   - A fake secret leak.
   - A severe injection-following output.
2. Run scoring in deterministic-only mode.
3. Confirm no provider calls are made.
4. Confirm hard failure gates are present for the invalid, privacy, injection,
   and applicable `max_chars` records.

Expected outcome:

- Scored JSONL records are written.
- Hard-failed records have effective usability `unusable`.
- Per-record evidence identifies the check that fired.

## Validate Budgeted Judge Scoring

1. Start from a completed spec 010 `outputs.jsonl` file or compatible spec 011
   `candidate-records.jsonl` file with generated messages.
2. Run judge scoring with an explicit judge model, rubric version, judge prompt
   version, and judge-call budget.
3. Review the planned judge-call count before calls begin.
4. Confirm the run interactively, or use non-interactive confirmation only with
   an explicit budget.

Expected outcome:

- Each eligible output receives one judge call by default.
- Each scored record includes judge metadata, structured judge output,
  per-dimension scores, usability, error categories, and rationales.
- Budget accounting records planned, budgeted, actual, skipped, and remaining
  judge calls.

## Validate Judge Calibration

1. Prepare a small calibration set with manually annotated expected labels for
   accuracy, quality, usability, and hard-failure gates.
2. Run calibration for one judge model, judge prompt version, rubric version, and
   parameter set.
3. Inspect the calibration report.

Expected outcome:

- The report records expected labels and judge labels separately.
- Agreement is reported by dimension.
- Parse failures are counted.
- Bias-control metadata records that candidate model identity was hidden.
- Any future pairwise judge mode records candidate ordering and supports
  order-swapped or randomized calibration examples.

## Validate Resume

1. Interrupt a scoring run after at least one scored record has been written.
2. Resume with the same source runner outputs, judge configuration, rubric
   version, judge prompt version, and schema versions.
3. Confirm completed compatible records are skipped.
4. Attempt resume with a changed judge model or rubric version.

Expected outcome:

- Compatible resume skips completed records and spends budget only on remaining
  records.
- Incompatible resume is rejected or requires a new scoring run.

## Validate Judge Operational Errors

Simulate these judge failures with mocked provider behavior:

- Authentication failure.
- Rate limit.
- Timeout.
- Network failure.
- Context length failure.
- Empty response.
- Malformed structured output.

Expected outcome:

- Failures are recorded under judge operational errors.
- No fabricated judge scores are created.
- Candidate output quality summaries do not count judge operational failures as
  model quality failures.

## Validate Manual Annotations And Overrides

1. Add an annotation to a scored output without changing scores.
2. Add an override that changes one effective score or usability category.
3. Inspect the scored record and summary.

Expected outcome:

- The original deterministic checks and judge output remain unchanged.
- The annotation includes reviewer, timestamp, and note.
- The override includes reviewer, timestamp, target fields, replacement values,
  and rationale.
- Effective scores show whether they derive from automated scoring, manual
  override, or mixed evidence.

## Validate Contract Compatibility

Use the contracts in this spec as acceptance references:

- `contracts/judge-output.md`
- `contracts/scoring-schema.md`

Expected outcome:

- Valid judge output parses successfully.
- Missing fields, invalid enum values, out-of-range scores, and malformed
  structured responses produce `judge_parse_error`.
- Scored JSONL and summary JSON include all required schema, source, judge, and
  taxonomy version fields.
- Calibration report JSON includes judge configuration, expected label version,
  agreement counts, parse failures, and bias-control metadata.

## Out Of Scope For This Validation

- Promoting baselines.
- Comparing against promoted baselines.
- Importing fixtures.
- Publishing public benchmark recommendations.
