# Contract: Live Eval Guardrail CLI

This contract defines live-run planning, guardrails, and confirmation for the
Inspect-backed eval runner.

## Command Shape

```text
python -m tools.evals.gmuse_evals run \
  --mode live \
  --suite <suite-id> \
  --model <model>... \
  --limit-samples <positive-count> \
  [--max-tokens <per-response-count>] \
  [--concurrency 1] \
  [--plan] \
  [--yes]
```

The direct gmuse provider path requires an explicit positive `--limit-samples`
for every live run. `--max-tokens` caps output tokens for each response; it is
not a run-wide token budget. Run-wide `--limit-tokens`, `--limit-cost`, and
`--limit-time` are accepted as CLI options only to produce a clear validation
error: this execution path does not support them. `--concurrency` may be
omitted or set to `1`; larger values are rejected because fixture execution
changes directory.

## Plan Output

Before any provider call, the command must display:

- suite ID and revision
- selected case count
- selected candidate models
- planned Inspect sample count
- effective per-entry generation settings that affect prompts or validation
- the required sample cap and any per-response token cap
- Inspect log location
- whether execution is `plan_only`, interactive, or `--yes`

For live mode, the CLI always displays the effective per-entry settings in a
privacy-safe form. This does not include raw prompts or repository instructions.

## Guardrail Rules

- Every live run requires an explicit positive `--limit-samples` cap.
- `--limit-samples` fails before calls when planned samples exceed the limit.
- `--limit-tokens`, `--limit-cost`, and `--limit-time` are rejected by the
  direct provider path.
- `--concurrency` is supported only when omitted or set to `1`.
- `--max-tokens` applies to each generated response, not to the run total.
- Guardrails are required even when `--yes` is supplied.
- `--plan` displays the live plan, performs zero provider calls, and writes no
  live sample results or run artifacts.

## Confirmation Rules

- Runs require both stdin and stdout to be TTYs to prompt interactively.
- Non-interactive runs require `--yes`.
- `--yes` skips only the prompt; it does not skip plan output or guardrail
  validation.

## Error Conditions

The command fails before provider calls when:

- no model is selected for live mode;
- `--limit-samples` is missing, zero, or negative;
- planned samples exceed `--limit-samples`;
- a run-wide token, cost, or time limit is requested;
- `--concurrency` is set to a value other than `1`;
- fixture/suite validation fails;
- a non-interactive run omits `--yes`.

When optional Inspect-backed reuse is requested, entries with missing, corrupt,
or incompatible provenance are ineligible for reuse. Fresh generation follows
the normal plan limits and confirmation.

## Out of Scope

- Custom provider-call ledgers.
- Custom JSONL resume accounting.
- Judge scoring configuration, which belongs to spec 012.
- Baseline or comparison behavior, which belongs to spec 013.
