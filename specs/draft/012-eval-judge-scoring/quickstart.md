# Quickstart: Eval Judge And Scoring

**Feature**: `012-eval-judge-scoring`

This guide describes how maintainers validate Inspect-backed scoring for gmuse
evals.

## Prerequisites

- A completed Inspect-backed eval run from spec 010 or 011.
- gmuse scoring metadata from spec 009 fixtures/rubrics.
- Mocked judge providers for automated tests.
- Real provider credentials only for manual live judge runs.

## Deterministic Scoring

Run scoring with deterministic gmuse scorers only.

Expected:

- Production validation failures are hard gates.
- Applicable `max_chars` failures are hard gates.
- Known fake secret leakage is a hard gate.
- Severe injection-following markers are hard gates.
- Hard-gated samples are not sent to a judge by default.
- Scoring metadata is attached to Inspect sample results.

## Judge Scoring

Run scoring with a fixed judge configuration and live guardrails.

Expected:

- The plan shows eligible sample count, judge model, rubric version, prompt
  version, configured limits, and Inspect log location.
- Live judge calls start only after spec 011 guardrails and confirmation pass.
- Judge results are structured and validated.
- Judge operational failures are recorded separately from quality errors.
- Self-judged outputs are flagged.

## Calibration

Run calibration examples for one judge prompt/rubric version when available.

Expected:

- Expected labels and judge labels are preserved separately.
- Agreement by dimension and parse failures are recorded.
- Missing calibration may warn, but does not block ordinary maintainer scoring.

## Candidate Operational Failures

Use Inspect sample results where candidate generation failed before a generated
message existed.

Expected:

- The sample is marked unscored for candidate operational failure.
- No judge call is made for that sample.
- Summary counts distinguish candidate operational failures from quality errors.

## Verification

Automated tests should prove:

- Deterministic hard gates fire on known cases.
- Hard-gated samples skip live judge calls by default.
- Valid judge output parses successfully.
- Malformed judge output is recorded as `judge_parse_error`.
- Scoring metadata preserves source run/sample identity.
