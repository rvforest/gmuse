# Contract: Resume State And Artifacts

This contract defines the artifact files and compatibility checks required for a
live eval run to resume safely.

## Artifact Layout

```text
<output-dir>/
├── run.json
├── candidate-records.jsonl
├── judge-records.jsonl
└── summary.json
```

`judge-records.jsonl` may be absent when judge work is not enabled.

## `run.json`

Required fields:

- `run_id`
- `created_at`
- `artifact_schema_version`
- `suite_id`
- `suite_revision`
- `fixture_revision_digest`
- `case_selection_digest`
- `candidate_models_digest`
- `generation_config_digest`
- `prompt_version`
- `candidate_output_schema_version`
- `judge_config_digest`
- `rubric_version`
- `judge_output_schema_version`

Fields for judge identity may be null when judge work is disabled.

## `candidate-records.jsonl`

Each line is one candidate output record.

Required fields:

- `record_id`
- `work_item_id`
- `run_id`
- `case_id`
- `fixture_revision`
- `candidate_model`
- `generation_config_digest`
- `prompt_version`
- `candidate_output_schema_version`
- `status`
- `attempt_counted`
- `created_at`

Status values:

- `completed`
- `validation_failed`
- `operational_error`

Resume rules:

- A terminal candidate record with a matching `work_item_id` is skipped.
- Duplicate active records for the same `work_item_id` fail resume before calls.
- Corrupt JSONL fails resume before calls.
- Completed record content must not be overwritten by resume.

## `judge-records.jsonl`

Each line is one judge record.

Required fields:

- `record_id`
- `work_item_id`
- `run_id`
- `candidate_record_id`
- `judge_config_digest`
- `rubric_version`
- `judge_output_schema_version`
- `status`
- `attempt_counted`
- `created_at`

Status values:

- `completed`
- `operational_error`

Resume rules:

- A terminal judge record with a matching `work_item_id` and judge identity is
  skipped.
- Duplicate active judge records for the same `work_item_id` fail resume before
  calls.
- Corrupt JSONL fails resume before calls.
- Judge scoring fields are opaque to this feature and are validated by the judge
  feature that owns rubric design.

## `summary.json`

Required fields:

- `run_id`
- `status`
- `started_at`
- `updated_at`
- `completed_at`
- `candidate_counts`
- `judge_counts`
- `resume_counts`
- `failure_reasons`

Allowed status values:

- `planned`
- `running`
- `interrupted`
- `failed`
- `complete`

Count groups must include:

- `planned`
- `budgeted`
- `attempted`
- `completed`
- `skipped`
- `failed`
- `remaining`

## Compatibility Checks

Resume must compare the requested run to `run.json` and reject before provider
calls when any required compatibility field differs:

- `artifact_schema_version`
- `suite_id`
- `suite_revision`
- `fixture_revision_digest`
- `case_selection_digest`
- `candidate_models_digest`
- `generation_config_digest`
- `prompt_version`
- `candidate_output_schema_version`
- `judge_config_digest`
- `rubric_version`
- `judge_output_schema_version`

The rejection message must name each mismatched field detected before stopping.

## Compatibility Outcomes

- **Compatible with missing work**: Skip completed matching records, plan missing
  work, and validate budgets for missing work only.
- **Compatible with no missing work**: Make zero provider calls and report that
  the run is already complete for the requested settings.
- **Incompatible**: Make zero provider calls, preserve artifacts unchanged, and
  report mismatch reasons.
- **Corrupt or duplicate artifacts**: Make zero provider calls, preserve
  artifacts unchanged, and require the maintainer to start a new run or repair
  artifacts manually.
