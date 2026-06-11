# Quickstart: Eval Live Run Budgeting And Resume

This guide describes validation scenarios for the maintainer-only live eval
budgeting and resume feature. It assumes spec 009 fixture/suite validation and
spec 010 production-path eval runner outputs are already available.

## Prerequisites

- Development environment installed with `uv sync`.
- A validated eval suite from spec 009, including at least a `smoke` suite.
- Production-path eval runner artifacts and mocked provider hooks from spec 010.
- Provider calls mocked for automated tests unless a maintainer intentionally
  performs a manual live run.

## Run Contract Tests

```bash
uv run pytest tests/contract/test_eval_live_contracts.py
```

Expected outcomes:

- Missing candidate budgets fail before calls.
- Missing judge budgets fail before judge calls when judge work is enabled.
- Over-budget candidate and judge plans fail before calls.
- Planning mode reports planned calls and performs zero provider calls.
- Resume compatibility mismatches fail before calls.

## Validate Planning Mode

Example command shape:

```bash
uv run gmuse eval run --suite smoke --model example-model --candidate-call-budget 3 --plan
```

Expected outcomes:

- The command displays suite identity, selected cases, model list, planned
  candidate calls, planned judge calls, budgets, resume status, and output paths.
- No provider calls are made.
- No candidate or judge live output records are written.

## Validate Interactive Confirmation

Example command shape:

```bash
uv run gmuse eval run --suite smoke --model example-model --candidate-call-budget 3
```

Expected outcomes:

- The run plan is displayed first.
- The command waits for maintainer confirmation in an interactive terminal.
- Declining confirmation exits before provider calls.
- Accepting confirmation starts the live run and updates the summary.

## Validate Non-Interactive Confirmation

Example command shape:

```bash
uv run gmuse eval run --suite smoke --model example-model --candidate-call-budget 3 --yes
```

Expected outcomes:

- The run plan is still printed.
- The command does not prompt.
- Calls begin only after budget validation passes.
- Omitting `--candidate-call-budget` still fails before calls.

## Validate Incremental Writes

Run with mocked provider behavior that completes one item, then simulates
interruption.

Expected outcomes:

- `candidate-records.jsonl` contains the completed candidate record.
- `summary.json` reports an interrupted or partial state.
- Previously written records are readable and are not removed.

## Validate Compatible Resume

Example command shape:

```bash
uv run gmuse eval run --suite smoke --model example-model --candidate-call-budget 2 --resume --output-dir path/to/prior-run
```

Expected outcomes:

- Completed matching candidate records are skipped.
- Completed matching judge records are skipped when judge work is enabled.
- Newly planned calls are counted against the new budgets.
- The final summary reports skipped prior records and newly written records.

## Validate Incompatible Resume

Repeat a resume command while changing one compatibility field, such as suite,
candidate model list, generation config, prompt version, judge config, or schema
version.

Expected outcomes:

- The command fails before provider calls.
- The error names the mismatched field.
- Existing records remain unchanged.

## Out Of Scope For This Quickstart

- Designing judge rubrics or scoring dimensions.
- Promoting baselines or comparing runs against baselines.
- Importing fixtures from public repositories.
- Producing public benchmark recommendations.
