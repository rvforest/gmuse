# Quickstart: eval baselines and comparison

This guide describes maintainer validation scenarios for baseline promotion and
comparison. It assumes result artifacts from spec 010 and scored outputs from
spec 012 already exist.

## Prerequisites

1. Install development dependencies:

   ```bash
   uv sync
   ```

2. Prepare local sample artifacts for:

   - a completed spec 010 eval result artifact,
   - a matching spec 012 scored output artifact,
   - a second candidate result/scored pair for comparison.

3. Confirm the artifacts contain the fields required by:

   - `specs/draft/013-eval-baselines-comparison/contracts/baseline-artifact.md`
   - `specs/draft/013-eval-baselines-comparison/contracts/comparison-cli.md`

## Scenario 1: promote a reviewed run as a baseline

Run the promotion command with explicit baseline metadata:

```bash
uv run gmuse eval baseline promote \
  --result-artifact path/to/spec010-result.json \
  --scored-artifact path/to/spec012-scored.json \
  --baseline-id core-current-model-2026-06-11 \
  --label "Core suite current model baseline" \
  --output path/to/baselines/core-current-model-2026-06-11.json
```

Expected outcome:

- The command validates that the result and scored artifacts describe the same
  run or a valid scoring relationship.
- The command rejects missing required suite, case, model, config, prompt, judge,
  score, hard-failure, or schema metadata.
- The command writes a versioned baseline artifact.
- Debug-only fields are stripped unless an explicit debug-retention option is
  used.

## Scenario 2: reject an unscored run

Run promotion with a result artifact but no scored output:

```bash
uv run gmuse eval baseline promote \
  --result-artifact path/to/spec010-result.json \
  --baseline-id invalid-unscored \
  --label "Invalid unscored baseline" \
  --output path/to/baselines/invalid.json
```

Expected outcome:

- The command fails.
- The error explains that scored outputs from spec 012 are required.
- No baseline artifact is created.

## Scenario 3: compare a same-model candidate against a baseline

Run comparison in the default regression mode:

```bash
uv run gmuse eval baseline compare \
  --baseline path/to/baselines/core-current-model-2026-06-11.json \
  --candidate-result path/to/candidate-spec010-result.json \
  --candidate-scored path/to/candidate-spec012-scored.json \
  --output path/to/reports/core-regression-comparison.json
```

Expected outcome:

- The report is generated offline without live candidate or judge calls.
- Every shared case appears in pairwise output.
- The report includes per-dimension score deltas, hard-failure deltas,
  prompt/token deltas, first-shot success deltas, error category deltas, and
  operational error deltas.
- Same-model metadata and generation config mismatches produce high-severity
  compatibility warnings.
- New privacy, severe injection, or production validation failures are flagged
  even if aggregate score improves.

## Scenario 4: inspect incompatible versions and configs

Compare artifacts with deliberate differences such as suite revision, case
revision, prompt version, judge prompt version, scoring schema version, or
artifact schema version.

Expected outcome:

- Each mismatch produces a structured compatibility warning.
- Warnings identify the affected scope and cases where applicable.
- The report classifies evidence as clean regression, degraded regression,
  benchmark, or invalid.
- Per-case details remain available unless a blocking schema incompatibility
  prevents safe parsing.

## Scenario 5: compare different models in benchmark mode

Run benchmark mode explicitly:

```bash
uv run gmuse eval baseline compare \
  --baseline path/to/baselines/core-current-model-2026-06-11.json \
  --candidate-result path/to/other-model-spec010-result.json \
  --candidate-scored path/to/other-model-spec012-scored.json \
  --mode benchmark \
  --output path/to/reports/core-model-benchmark-comparison.json
```

Expected outcome:

- Model metadata differences are allowed and shown in report metadata.
- Suite, case, config, prompt, judge, scoring, and schema mismatches still
  produce warnings.
- The report is labeled as benchmark evidence.
- The report does not include public recommendations, provider preference
  claims, or hardcoded accept/reject decisions.

## Validation commands

Run the focused test suite for this feature after implementation:

```bash
uv run pytest tests/unit/test_eval_baselines.py tests/unit/test_eval_compare.py
uv run pytest tests/contract/test_eval_baseline_contracts.py
uv run pytest tests/integration/test_eval_baseline_cli.py
```

Run standard quality checks before merging implementation:

```bash
uv run nox -s lint
uv run nox -s types
uv run nox -s test
```

## Out of scope

- Fixture importing from GitHub or other sources.
- Public recommendation pages.
- Provider preference claims.
- Live candidate or judge calls during comparison.
- Automatic accept/reject decisions beyond hard-failure flags and compatibility
  severity.
