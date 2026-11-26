# Data Model: Eval Live Guardrails

## Live Run Plan

Represents the pre-call plan for an Inspect-backed live eval.

Fields:

- `suite_id`
- `suite_revision`
- `case_selection`
- `candidate_models`
- `planned_samples`
- `generation_config_digest`
- `prompt_version`
- `inspect_task_name`
- `inspect_log_location`
- `guardrails`
- `confirmation_mode`: `interactive`, `yes`, or `plan_only`

Rules:

- The plan must be displayed before any provider call.
- `planned_samples` must be computed before live execution.
- `plan_only` mode makes zero provider calls and writes no live sample results.

## Guardrail Configuration

Represents limits that prevent runaway spend.

Fields:

- `limit_samples: int | None`
- `limit_tokens: int | None`
- `limit_cost: str | None`
- `limit_time_seconds: int | None`
- `limit_concurrency: int | None`
- `inspect_native_limits: dict[str, str | int | float | bool | None]`

Rules:

- Non-trivial live runs require at least one meaningful guardrail.
- If `limit_samples` is set, `planned_samples` must not exceed it.
- Token, cost, time, and concurrency limits should be delegated to Inspect when
  supported by the selected provider path.
- Guardrail failures happen before provider calls when the failure can be
  determined from the plan.

## Confirmation

Represents the maintainer's explicit authorization to start live calls.

Fields:

- `required: bool`
- `mode: interactive | yes`
- `confirmed_at: str | None`
- `displayed_plan_digest: str`

Rules:

- Interactive terminals require an affirmative response after displaying the
  plan.
- Non-interactive runs require `--yes`.
- `--yes` does not waive guardrail requirements and does not suppress plan
  output.

## Inspect Log Reference

Represents the local evidence created by Inspect execution.

Fields:

- `log_dir`
- `run_id`
- `task_name`
- `execution_mode`
- `sample_count`

Rules:

- Inspect logs are the canonical execution artifacts.
- gmuse must not introduce a custom JSONL resume ledger in v1.
- Logs must preserve the metadata required by spec 010.

## Optional Reuse Compatibility

Inspect-backed reuse checks both the run metadata and the inputs to each entry.

Fields:

- `suite_id: str`
- `suite_revision: str`
- `case_selection_digest: str`
- `candidate_models_digest: str`
- `case_id: str`
- `fixture_id: str`
- `fixture_revision_digest: str`
- `model: str`
- `generation_config_digest: str` (effective settings for the entry)
- `prompt_version: str`
- `inspect_log_schema: str`
- `gmuse_eval_schema_version: str`
- `staged_diff_digest: str` (observed staged diff)
- `prompt_hash: str` (rendered generation prompt)

Verify both hashes and compare them against the planned entry before provider
calls. An incompatible, missing, or unverifiable required field makes the entry
ineligible. Any fresh generation must pass the normal limits and confirmation.

[Spec 012's scoring model](../012-eval-judge-scoring/data-model.md) records the
rubric, scoring profile, and judge-evidence reference used for scoring.
