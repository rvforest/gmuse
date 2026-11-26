# Quickstart: Eval Safety Comparison

This guide validates comparison between a reference Inspect eval log and a
candidate Inspect eval log.

## Prerequisites

- A reference Inspect log from spec 010/012.
- A candidate Inspect log from spec 010/012.
- Both logs include gmuse case, fixture, validation, hard-gate, and scoring
  metadata.

## Compare Two Logs

```bash
uv run python -m tools.evals.gmuse_evals compare \
  --reference-log .gmuse-evals/inspect/reference.eval \
  --candidate-log .gmuse-evals/inspect/candidate.eval \
  --output .gmuse-evals/comparisons/candidate-vs-reference.json
```

Expected:

- The command runs offline.
- The report lists compatibility warnings.
- Shared cases include hard-failure deltas and validation deltas.
- Judge score movement is reported when available.
- Exit status follows strict safety gate rules.

## New Hard Failure

Use a candidate log with a new privacy, injection, production validation, or
`max_chars` hard failure.

Expected:

- The comparison report has `gate_result.status = "failed"`.
- The affected case and hard failure type are identified.
- The command exits non-zero.

## Score-Only Movement

Use logs where judge scores change but no hard failures or deterministic
validation regressions appear.

Expected:

- The report includes score deltas.
- The strict safety gate does not fail solely due to score movement.

## Incompatible Metadata

Compare logs with changed fixture revisions, prompt versions, model/config, or
judge/scorer schema.

Expected:

- The report includes structured compatibility warnings.
- The gate result is `inconclusive` or `invalid` when metadata prevents a clean
  strict safety result.

## Verification

Automated tests should prove:

- New hard failures fail.
- Score-only movement does not fail.
- Metadata mismatches warn.
- Missing required log metadata is invalid. Missing scoring provenance makes
  the affected score comparison inconclusive.
- No live calls occur during comparison.

## Verify Per-Case Score Comparability

Compare scored logs with matching assessment evidence and criterion identities
and a different candidate model. Verify the changed model is reported separately
and named score deltas remain comparable. Change a rubric or scoring-profile
digest, or remove assessment provenance from one case. Verify the report names
the affected case and field and marks its score comparison inconclusive.
Verify comparison makes zero provider calls.
