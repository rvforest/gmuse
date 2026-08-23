# Contract: Inspect Log Metadata

**Feature**: 010-eval-runner
**Date**: 2026-06-11
**Framework Alignment Update**: 2026-06-14

The runner uses Inspect AI logs as the canonical local execution artifact.
gmuse does not define a parallel `run-plan.json`/`outputs.jsonl`/`summary.json`
contract in this revised design. Instead, every Inspect run and sample result
must carry enough gmuse metadata for maintainer review, judge scoring, and
strict safety comparison.

## Log Location

Inspect logs are written to the configured Inspect log directory. gmuse may use
`.gmuse-evals/inspect/` as a repo-local default when no Inspect default is
configured.

Generated log directories must be ignored by git unless a maintainer explicitly
chooses to check in sanitized sample logs for tests.

## Run-Level Metadata

Each Inspect run must expose:

- `gmuse_eval_schema_version`
- `execution_mode`: `check` or `live`
- `suite_id`
- `suite_version`
- selected case IDs
- selected model IDs for live runs
- deterministic output policy for check runs
- effective generation defaults and overrides
- prompt version
- gmuse project revision when available
- configured guardrails, such as sample, token, cost, time, or concurrency limits
- fixture foundation schema version

## Sample-Level Metadata

Each Inspect sample result must expose:

- stable `entry_id`
- `case_id` and `case_revision`
- `fixture_id` and `fixture_revision` or digest
- `rubric_id` and `rubric_version`
- `candidate_kind`: `deterministic_check` or `live_model`
- candidate model metadata when applicable
- effective generation config:
  - format
  - history depth
  - branch inclusion
  - hint presence
  - repository instruction presence
  - `max_chars`
  - temperature
  - token cap
- staged diff digest observed after reconstruction
- generated message when generation reaches message output
- production validation status and error categories
- operational error category and message when setup/provider execution fails
- prompt hash
- prompt size in bytes
- estimated input/output token counts when available
- timing metadata when available

## Privacy Rules

- Raw prompt text must not be recorded by default.
- Raw prompts and preserved temporary repositories are allowed only behind an
  explicit debug option and must be stored separately from ordinary Inspect run
  metadata where practical.
- Generated messages remain part of normal logs because they are the eval output
  under review, including invalid messages.

## Check Mode Rules

- Check mode must make zero provider calls.
- Check mode sample results must be marked `candidate_kind =
  deterministic_check`.
- Check mode logs are implementation evidence, not candidate model quality
  evidence, and judge scoring must skip them by default.

## Live Mode Rules

- Live mode must display the planned case/model/sample count and configured
  guardrails before provider calls.
- Live mode must require interactive confirmation or `--yes`.
- Live mode sample results must be marked `candidate_kind = live_model`.
- Provider/setup failures must be represented separately from deterministic
  production validation failures.

## Downstream Consumer Rules

- Scoring specs consume Inspect logs and sample metadata directly.
- Strict safety comparison consumes two Inspect logs and compares stable case
  identities, hard failure gates, production validation outcomes, and selected
  compatibility metadata.
- If the Inspect spike identifies metadata that cannot be represented in logs,
  gmuse may add a compact sidecar metadata file, but Inspect logs remain the
  primary execution evidence.
