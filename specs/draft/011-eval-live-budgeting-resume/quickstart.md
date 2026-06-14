# Quickstart: Eval Live Guardrails

This guide describes maintainer validation scenarios for live eval guardrails.
It assumes spec 009 fixture/suite validation and the Inspect-backed runner from
spec 010.

## Prerequisites

- A validated smoke suite from spec 009.
- Inspect-backed check mode from spec 010.
- Mocked providers for automated tests.
- Real provider credentials only for manual live validation.

## Validate Plan-Only Mode

```bash
uv run python -m tools.evals.gmuse_evals run \
  --mode live \
  --suite smoke \
  --model example-model \
  --limit-samples 2 \
  --plan
```

Expected:

- The command displays suite, case count, model list, planned samples, limits,
  and Inspect log location.
- No provider calls occur.
- No live sample results are written.

## Validate Guardrail Rejection

```bash
uv run python -m tools.evals.gmuse_evals run \
  --mode live \
  --suite smoke \
  --model example-model \
  --limit-samples 1 \
  --yes
```

Expected when the smoke suite plans more than one sample:

- The command fails before provider calls.
- The error names the planned sample count and configured sample limit.

## Validate Confirmation

Interactive:

```bash
uv run python -m tools.evals.gmuse_evals run \
  --mode live \
  --suite smoke \
  --model example-model \
  --limit-samples 2
```

Non-interactive:

```bash
uv run python -m tools.evals.gmuse_evals run \
  --mode live \
  --suite smoke \
  --model example-model \
  --limit-samples 2 \
  --yes
```

Expected:

- Interactive mode prompts after displaying the plan.
- Non-interactive mode requires `--yes`.
- `--yes` does not suppress plan output.

## Validate Optional Reuse Behavior

If Inspect supports safe rerun/resume for the selected execution path:

1. Interrupt a bounded live run after one sample completes.
2. Rerun with the same suite, models, generation config, and log identity using
   the supported Inspect/gmuse reuse option.
3. Verify completed work is not repeated.

If Inspect does not support safe reuse, the v1 behavior may rerun bounded
samples. That is acceptable as long as guardrails and confirmation still apply.

## Verification

Automated tests should prove:

- `--plan` makes zero provider calls.
- Missing guardrails fail before provider calls.
- Sample limits fail before provider calls when exceeded.
- Non-interactive live mode without `--yes` fails before provider calls.
- Fixture validation failures stop before provider calls.
