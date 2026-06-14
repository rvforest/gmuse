# Tool Contract: Eval Runner

**Feature**: 010-eval-runner
**Date**: 2026-06-11

The runner is maintainer-facing repository tooling. It is invoked through the
module entrypoint shared with the fixture/suite foundation and must remain
separate from normal commit-message generation. It is not a public `gmuse`
console command.

**Framework Alignment Update (2026-06-14)**: The command builds and runs an
Inspect AI task. Inspect logs are the canonical run artifacts. Options below
describe the gmuse wrapper around Inspect rather than a bespoke JSONL runner.

## Command: `run`

### Signature

```text
python -m tools.evals.gmuse_evals run [OPTIONS]
```

### Required inputs

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--mode` | `check` or `live` | required | Execution mode |
| `--suite` | str | required | One suite ID from spec 009, such as `smoke`, `core`, or `safety` |

### Mode-specific inputs

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--model` | str, repeatable | required in `live`, forbidden in `check` | Candidate model identifier |
| `--limit-samples` | int | optional | Maximum Inspect samples to execute |
| `--limit-tokens` | int | optional | Token guardrail when supported by Inspect/provider path |
| `--limit-cost` | str | optional | Cost guardrail when supported by Inspect/provider path |
| `--log-dir` | path | Inspect default or `.gmuse-evals/inspect/` | Directory for local Inspect logs |
| `--yes` | bool | false | Non-interactive acknowledgement of the displayed live plan and configured guardrails |
| `--preserve-debug` | bool | false | Preserve temporary repositories and raw prompt debug artifacts when supported by gmuse/Inspect debug settings |

### Generation overrides

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | str | suite/case default | Commit message format |
| `--history-depth` | int | suite/case default | Number of recent commits used for style context |
| `--include-branch` | bool | suite/case default | Include sanitized branch context |
| `--hint` | str | suite/case default | Additional generation guidance |
| `--repository-instructions` | path | suite/case default | Repository instruction text to apply during generation |
| `--max-chars` | int | suite/case default | Production message length constraint |
| `--temperature` | float | model/config default | Sampling override for live mode |
| `--max-tokens` | int | model/config default | Response token cap |

## Check Mode

When `--mode check` is selected, the command must:

1. Resolve the selected suite and cases through spec 009.
2. Validate selected fixtures through spec 009 validation.
3. Resolve effective generation settings for each case.
4. Print the run plan, selected case IDs, effective generation overrides, and
   Inspect log paths.
5. Create an independent Inspect run/log identity unless `--log-dir` is provided.
6. Reconstruct each selected fixture in an isolated temporary repository.
7. Invoke the production generation path with deterministic local output instead
   of a provider call.
8. Write Inspect log entries with required gmuse metadata.
9. Make zero provider calls.

Check mode must not accept `--model`.

Example:

```bash
uv run python -m tools.evals.gmuse_evals run --mode check --suite smoke
```

Expected outcome:

```text
Run mode: check
Suite: smoke
Candidate kind: deterministic_check
Planned entries: 2
Provider calls: 0
Inspect log: .gmuse-evals/inspect/20260611T120000Z-smoke-check.eval
```

Check outputs are implementation test artifacts. They are not model evaluation
evidence and later judge scoring should skip them by default.

## Live Mode

When `--mode live` is selected, the command must:

1. Require at least one `--model`.
2. Display the planned case/model count and configured spend guardrails.
3. Resolve and validate the selected suite before provider calls.
4. Fail before provider calls if no meaningful runaway-spend guardrail is
   configured for a non-trivial live run.
5. Require interactive confirmation or `--yes` after displaying the live plan.
6. Print the run plan, selected cases, selected models, effective generation
   overrides, configured limits, and Inspect log paths.
7. For each entry, create an isolated temporary repository from the validated
   fixture.
8. Stage fixture changes and verify the staged diff digest from spec 009.
9. Invoke gmuse production generation behavior with the effective config.
10. Preserve raw generated messages even when deterministic validation fails.
11. Write one Inspect sample result per executed case/model/config entry.
12. Rely on Inspect logs/summaries as canonical run evidence.
13. Clean up temporary repositories unless `--preserve-debug` is selected.

Provider/setup failures after execution begins must be recorded in the relevant
Inspect sample result and the command should continue to later entries when possible.
Suite or fixture validation failures must stop the run before provider calls.

Example:

```bash
uv run python -m tools.evals.gmuse_evals run \
  --mode live \
  --suite smoke \
  --model gpt-4.1-mini \
  --model claude-3-5-haiku-latest \
  --limit-samples 4 \
  --yes
```

Expected outcome:

```text
Run mode: live
Suite: smoke
Models: gpt-4.1-mini, claude-3-5-haiku-latest
Planned samples: 4
Configured limits: samples=4
Inspect log: .gmuse-evals/inspect/20260611T120045Z-smoke-live.eval
Completed entries: 4
Validation passed: 3
Validation failed: 1
Operational errors: 0
```

## Inspect Log Behavior

- If `--log-dir` is omitted, the command uses the configured Inspect log
  location, with `.gmuse-evals/inspect/` as the gmuse-local default when needed.
- If `--log-dir` is provided and does not exist, the command creates it.
- The runner must not infer a live log location from a prior check run.
- The runner must not create a `latest` symlink or pointer file.

## Error Behavior

### Missing mode

```text
Error: Missing option '--mode'. Choose one of: check, live.
```

### Check mode with model

```text
Error: --model is only valid with --mode live.
```

### Live mode without model

```text
Error: --model is required with --mode live.
```

### Live mode without guardrails

```text
Error: live evals require an explicit limit such as --limit-samples, --limit-tokens, or --limit-cost.
```

### Sample limit exceeded

```text
Error: planned samples 4 exceed --limit-samples 2.
No provider calls were made.
```

### Invalid suite

```text
Error: Unknown eval suite 'benchmark'.

Use a suite defined by the fixture/suite foundation.
```

### Invalid fixture

```text
Error: Fixture validation failed for case 'core-docs-001'.

<validation details from spec 009>
```

### Existing artifacts

```text
Error: Inspect log location already contains a conflicting run identity.
Choose a new --log-dir or run id.
```

## Out-of-Scope Command Behavior

The runner CLI must not expose:

- judge model or scoring flags;
- resume flags;
- baseline promotion flags;
- fixture importer flags;
- public benchmark recommendation flags.
