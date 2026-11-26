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
  --limit-samples 5 \
  --plan
```

Expected:

- The command displays the suite, selected cases, model, planned entries,
  sample cap, privacy-safe per-entry generation settings, and log location.
- No provider calls occur.
- No live sample results or run artifacts are written.

The checked-in smoke suite currently plans five entries with one model, so the
sample cap must be at least `5` for this example.

`--limit-samples` is required for every live run and must be positive. An
optional `--max-tokens` sets the per-response output token cap. It does not
limit total tokens across the run.

The direct provider path rejects run-wide `--limit-tokens`, `--limit-cost`,
and `--limit-time`. `--concurrency` may be omitted or set to `1`; any other
value is rejected.

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
  --limit-samples 5
```

Non-interactive:

```bash
uv run python -m tools.evals.gmuse_evals run \
  --mode live \
  --suite smoke \
  --model example-model \
  --limit-samples 5 \
  --yes
```

Expected:

- Interactive mode prompts after displaying the plan.
- Non-interactive mode requires `--yes`.
- `--yes` does not suppress plan output.

## Reuse Decision

The pinned Inspect version cannot reconstruct gmuse's ephemeral task closure.
Its native sample lookup checks sample ID, epoch, and success state, but does
not verify the staged diff or rendered prompt hashes. Safe reuse is therefore
deferred; interrupted runs may generate entries again. Use a fresh bounded run
and retain its Inspect log. Do not assume a previous successful sample will be
reused. Any future reuse support must verify each entry's inputs before making
provider calls.

## Run Offline And Mocked Scenarios

Run the repository's offline smoke check and the mocked live preflight and
guardrail scenarios without provider credentials:

```bash
uv run nox -s evals-check
uv run pytest tests/integration/test_eval_live_guardrails.py \
  tests/integration/test_eval_runner_live.py tests/integration/test_eval_runner_logs.py
```

The mocked scenarios cover plan-only output without Inspect execution or log
creation, required sample caps, cap overflow, unsupported run-wide limits,
serial concurrency, and the confirmation rules. Live execution prompts only
when both stdin and stdout are TTYs; use `--yes` in non-interactive invocations.

## Verification

Automated tests should prove:

- `--plan` makes zero provider calls.
- `--plan` does not prompt or create a log directory.
- Missing, zero, or negative `--limit-samples` fails before provider calls.
- Unsupported run-wide token, cost, and time limits fail before provider calls.
- `--concurrency` values other than `1` fail before provider calls.
- Sample limits fail before provider calls when exceeded.
- Non-interactive live mode without `--yes` fails before provider calls.
- Live plans display privacy-safe effective settings for each entry.
- Fixture validation failures stop before provider calls.
