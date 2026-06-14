# Contract: Live Eval Guardrail CLI

This contract defines live-run planning, guardrails, and confirmation for the
Inspect-backed eval runner.

## Command Shape

```text
python -m tools.evals.gmuse_evals run \
  --mode live \
  --suite <suite-id> \
  --model <model>... \
  [--limit-samples <count>] \
  [--limit-tokens <count>] \
  [--limit-cost <amount>] \
  [--limit-time-seconds <seconds>] \
  [--limit-concurrency <count>] \
  [--plan] \
  [--yes]
```

## Plan Output

Before any provider call, the command must display:

- suite ID and revision
- selected case count
- selected candidate models
- planned Inspect sample count
- effective generation settings that affect prompts or validation
- configured guardrails
- Inspect log location
- whether execution is `plan_only`, interactive, or `--yes`

## Guardrail Rules

- Non-trivial live runs require at least one meaningful guardrail.
- `--limit-samples` fails before calls when planned samples exceed the limit.
- Token, cost, time, and concurrency limits should use Inspect-native
  mechanisms when available.
- Guardrails are required even when `--yes` is supplied.
- `--plan` performs zero provider calls and writes no live sample results.

## Confirmation Rules

- Interactive runs prompt after displaying the plan.
- Non-interactive runs require `--yes`.
- `--yes` skips only the prompt; it does not skip plan output or guardrail
  validation.

## Error Conditions

The command fails before provider calls when:

- no model is selected for live mode;
- no meaningful guardrail is configured for a non-trivial live run;
- planned samples exceed `--limit-samples`;
- Inspect limit configuration is invalid;
- fixture/suite validation fails;
- a non-interactive run omits `--yes`;
- optional Inspect-backed reuse is requested but prior logs are missing,
  corrupt, or incompatible.

## Out of Scope

- Custom provider-call ledgers.
- Custom JSONL resume accounting.
- Judge scoring configuration, which belongs to spec 012.
- Baseline or comparison behavior, which belongs to spec 013.
