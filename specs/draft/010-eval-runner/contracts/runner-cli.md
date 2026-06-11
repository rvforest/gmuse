# CLI Contract: eval runner

**Feature**: 010-eval-runner
**Date**: 2026-06-11

The runner is maintainer-facing tooling. The exact command group may be hidden or documented under development docs, but it must remain explicit and separate from normal commit-message generation.

## Command: `gmuse eval run`

### Signature

```text
gmuse eval run [OPTIONS]
```

### Required inputs

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--suite` | str, repeatable | required | Suite ID from spec 009, such as `smoke`, `core`, or `safety` |
| `--model` | str, repeatable | required for execution | Candidate model identifier |
| `--output-dir` | path | required | Directory for run artifacts |

### Mode options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--plan` | bool | false | Resolve and display the run plan without provider calls |
| `--execute` | bool | false | Execute planned attempts and write result artifacts |
| `--preserve-debug` | bool | false | Preserve temporary repositories and debug-only prompt artifacts |

Exactly one of `--plan` or `--execute` must be selected.

### Generation overrides

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | str | suite/case default | Commit message format |
| `--history-depth` | int | suite/case default | Number of recent commits used for style context |
| `--include-branch` | bool | suite/case default | Include sanitized branch context |
| `--hint` | str | suite/case default | Additional generation guidance |
| `--repository-instructions` | path | suite/case default | Repository instruction text to apply during generation |
| `--max-chars` | int | suite/case default | Production message length constraint |
| `--temperature` | float | model/config default | Sampling override |
| `--max-tokens` | int | model/config default | Response token cap |

### Planning behavior

When `--plan` is selected, the command must:

1. Resolve suites and cases through spec 009.
2. Validate selected fixtures through spec 009 validation.
3. Resolve selected model/config combinations.
4. Display planned attempt counts, selected case IDs, selected models, effective generation overrides, output paths, and fixture validation status.
5. Make zero provider calls.
6. Write no JSONL records that look like completed generation attempts.

Example:

```bash
gmuse eval run --suite smoke --model gpt-4.1-mini --output-dir .gmuse-evals/runs/smoke --plan
```

Expected outcome:

```text
Run mode: plan
Suites: smoke
Models: gpt-4.1-mini
Planned attempts: 3
Provider calls: 0
Output records: .gmuse-evals/runs/smoke/outputs.jsonl
Summary: .gmuse-evals/runs/smoke/summary.json
```

### Execution behavior

When `--execute` is selected, the command must:

1. Resolve and validate the same run plan used by planning mode.
2. For each attempt, create an isolated temporary repository from the validated fixture.
3. Stage fixture changes and verify the staged diff digest from spec 009.
4. Invoke gmuse production generation behavior with the effective config.
5. Preserve raw generated messages even when deterministic validation fails.
6. Write one JSONL record per attempted case/model/config combination.
7. Write a JSON summary for the run.
8. Clean up temporary repositories unless `--preserve-debug` is selected.

Example:

```bash
gmuse eval run --suite smoke --model gpt-4.1-mini --output-dir .gmuse-evals/runs/smoke --execute
```

Expected outcome:

```text
Run mode: execute
Planned attempts: 3
Completed attempts: 3
Validation passed: 2
Validation failed: 1
Operational errors: 0
Output records: .gmuse-evals/runs/smoke/outputs.jsonl
Summary: .gmuse-evals/runs/smoke/summary.json
```

## Error behavior

### Missing mode

```text
Error: Choose exactly one run mode: --plan or --execute.
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

### Provider/setup failure

Provider/setup failures must be recorded in the relevant output record when execution has reached an attempt. The command may continue to later attempts unless the failure prevents all remaining attempts from running.

## Out-of-scope command behavior

The runner CLI must not expose:

- judge model or scoring flags;
- resume flags or call budgets;
- baseline promotion flags;
- fixture importer flags;
- public benchmark recommendation flags.
