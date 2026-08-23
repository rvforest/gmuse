# Implementation Plan: Eval Live Guardrails

**Branch**: `011-eval-live-budgeting-resume` | **Date**: 2026-06-11 | **Spec**: ../011-eval-live-budgeting-resume/spec.md

## Summary

Add maintainer-only live eval guardrails around the Inspect-backed production
runner from spec 010. The feature displays planned suite/case/model work before
provider calls, requires explicit confirmation, requires meaningful configured
limits, and relies on Inspect-native execution/log behavior. Avoiding repeated
generations after interruption is useful when Inspect supports it cleanly, but a
custom provider-call ledger and custom JSONL resume subsystem are out of scope
for v1.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Inspect AI execution/logging from spec 010, spec 009
fixture/suite artifacts, Typer CLI under `tools/evals/gmuse_evals`, pytest,
Ruff, pyrefly

**Storage**: Local Inspect logs. No custom `run-plan.json`, `outputs.jsonl`, or
`summary.json` resume ledger is introduced by this feature.

**Testing**: pytest unit and integration tests with mocked provider calls and
temporary Inspect log directories.

**Target Platform**: Local maintainer CLI on Linux, macOS, and Windows;
interactive terminal and non-interactive maintainer automation.

**Performance Goals**: Planning finishes without provider calls. Live runs use
configured sample/token/cost/time/concurrency limits where available. Rerun or
resume behavior should reuse Inspect capabilities when practical.

**Constraints**: Live calls must never start without preflight display,
confirmation, and configured guardrails for non-trivial runs. Ordinary package
users and default CI must not require eval provider credentials. Hosted or
account-backed eval platforms are out of scope.

## Constitution Check

- **Code Quality Gate**: Pass. The feature is a thin guardrail layer around
  Inspect execution rather than a second runner or resume system.
- **Testing Gate**: Pass. Guardrail validation, confirmation, `--plan`, and
  zero-call behavior are testable with mocked providers.
- **UX Gate**: Pass. Maintainers see planned work, selected models, limits, and
  log locations before calls.
- **Performance Gate**: Pass. Planning is local and live execution is bounded by
  configured limits.
- **Security/Privacy Gate**: Pass. No credentials are stored and no hosted
  service is required.
- **Release Discipline Gate**: Pass. Guardrail behavior is documented and
  isolated to maintainer eval commands.

## Project Structure

```text
tools/
└── evals/
    └── gmuse_evals/
        ├── cli.py              # extend run command with --plan/--yes/limits
        ├── live_plan.py        # planned work display and guardrail validation
        └── inspect_tasks.py    # spec 010 Inspect task execution dependency

tests/
├── integration/
│   └── test_eval_live_guardrails.py
└── unit/
    └── test_eval_live_plan.py
```

## Phase 0 - Research

Research output is `research.md` and focuses on:

- Which Inspect limits are available and reliable for local runs.
- Which gmuse wrapper limits are still needed, such as a sample cap.
- Confirmation behavior for interactive and non-interactive runs.
- Whether Inspect provides useful rerun/resume behavior that avoids repeated
  generations without custom gmuse bookkeeping.

## Phase 1 - Design & Contracts

Design artifacts:

- `data-model.md`: Live plan, guardrails, confirmation, and optional reuse
  compatibility entities.
- `contracts/live-run-cli.md`: CLI behavior for `--plan`, `--yes`, and limits.
- `contracts/resume-state.md`: Compatibility notes for optional Inspect-backed
  rerun/resume; no custom resume file contract.
- `quickstart.md`: Maintainer validation guide for guardrails.

## Phase 2 - Future Implementation Planning

1. Add plan display for selected suite, cases, models, configured limits, and
   Inspect log location.
2. Add guardrail validation for sample/token/cost/time/concurrency limits where
   supported.
3. Add interactive confirmation and `--yes` handling.
4. Add `--plan` zero-call mode.
5. Add tests proving no provider call occurs before validation and confirmation.
6. Investigate Inspect rerun/resume behavior and use it only if it remains a thin
   adapter rather than a custom ledger.
