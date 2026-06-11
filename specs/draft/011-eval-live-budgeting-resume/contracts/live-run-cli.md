# Contract: Live Run CLI

This contract describes the maintainer-facing CLI behavior for live eval run
planning, budgeting, confirmation, incremental execution, and resume. Command
names are implementation-facing and may be adjusted during tasks if the eval CLI
surface from spec 010 uses different names, but the observable behavior must
remain equivalent.

## Command Shape

```text
gmuse eval run
  --suite <suite-id>
  --model <candidate-model> [--model <candidate-model> ...]
  --candidate-call-budget <count>
  [--judge-model <judge-model>]
  [--judge-call-budget <count>]
  [--case <case-id> ...]
  [--output-dir <path>]
  [--plan]
  [--execute]
  [--yes]
  [--resume]
```

## Required Inputs

- `--suite`: Selects a validated suite from spec 009.
- `--model`: Selects one or more candidate models.
- `--candidate-call-budget`: Required for any live candidate calls.
- `--judge-call-budget`: Required when judge work is enabled and any new judge
  calls are planned.

## Planning Behavior

Before any provider call, the command must display:

- Suite ID and suite revision.
- Selected case count and case selection summary.
- Candidate model list.
- Judge model and judge configuration summary when judge work is enabled.
- Planned new candidate calls.
- Planned new judge calls.
- Total planned new calls.
- Candidate and judge budgets.
- Resume status and skipped-record counts when resume is enabled.
- Output artifact directory and file names.

## Confirmation Behavior

- Interactive live runs require a confirmation prompt after plan display.
- Declining confirmation exits successfully or with a clear cancelled status
  before provider calls.
- Non-interactive live runs require `--yes`.
- `--yes` skips only the prompt; it does not skip planning output or budget
  validation.
- `--plan` never prompts for live execution because it never makes provider
  calls.

## Budget Behavior

- Missing candidate budget fails before provider calls.
- Missing judge budget fails before provider calls when judge work is enabled.
- Planned new candidate calls greater than the candidate budget fail before
  provider calls.
- Planned new judge calls greater than the judge budget fail before provider
  calls.
- Provider attempts consume budget even when the result is an operational error.
- Skipped completed records during resume do not consume the new run's budget.

## Planning Mode Behavior

`--plan` must:

- Expand the run plan.
- Display planned calls and required budgets.
- Make zero provider calls.
- Write no candidate or judge live output records.
- Not mutate prior resume artifacts.

`--execute` must be selected before live provider calls can begin. Exactly one of
`--plan` or `--execute` must be selected.

## Resume Behavior

`--resume` must:

- Load prior artifacts from `--output-dir` or the resolved run output directory.
- Validate compatibility before provider calls.
- Skip completed matching candidate and judge records.
- Plan only missing work.
- Count only missing work against new budgets.
- Preserve prior completed records without overwriting them.

## Error Behavior

The command must fail before provider calls when:

- The suite is missing or invalid.
- The selected cases are not in the suite.
- Required budgets are missing.
- Planned new calls exceed budgets.
- Confirmation is required but unavailable.
- Resume artifacts are missing, corrupt, duplicated, or incompatible.
- Artifact schema versions are unsupported.

Error messages must name the reason and, for resume mismatches, identify the
field that differs.

## Out Of Scope

- Judge rubric and scoring design.
- Baseline promotion or comparison commands.
- Fixture importer commands.
- Public benchmark recommendation commands.
