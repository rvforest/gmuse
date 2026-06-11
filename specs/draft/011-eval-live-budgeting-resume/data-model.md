# Data Model: Eval Live Run Budgeting And Resume

## Live Run Plan

Represents the work gmuse intends to perform before any live provider calls.

Fields:

- `run_id`: Stable identifier for this run attempt.
- `suite_id`: Suite identifier from spec 009.
- `suite_revision`: Suite revision or digest from spec 009.
- `case_selection`: Ordered case IDs included in the run.
- `candidate_models`: Ordered candidate model identifiers.
- `generation_config_digest`: Digest of prompt-affecting generation options from
  spec 010.
- `prompt_version`: Production prompt version from spec 010.
- `judge_config_digest`: Optional digest of judge model, parameters, prompt
  version, and rubric version when judge work is enabled.
- `artifact_schema_version`: Version of live-run artifact schemas.
- `planned_candidate_calls`: Count of candidate work items not already completed.
- `planned_judge_calls`: Count of judge work items not already completed.
- `candidate_call_budget`: Maintainer-supplied candidate attempt limit.
- `judge_call_budget`: Maintainer-supplied judge attempt limit when judge work is
  enabled.
- `resume`: Whether the plan was created from prior artifacts.
- `output_dir`: Directory for run artifacts.

Validation rules:

- `candidate_call_budget` is required for live candidate calls.
- `judge_call_budget` is required when `planned_judge_calls` is greater than 0.
- Planned new calls must not exceed the matching budget.
- Dry-run plans must not create candidate or judge output records.

## Planned Work Item

Represents one candidate generation or judge scoring item in a run plan.

Fields:

- `work_item_id`: Stable identity for this planned item.
- `work_type`: `candidate` or `judge`.
- `case_id`: Case identifier from the selected suite.
- `fixture_revision`: Fixture revision from spec 009.
- `candidate_model`: Candidate model for generation or judged output.
- `generation_config_digest`: Generation configuration digest.
- `candidate_record_id`: Required for judge work; identifies the output being
  judged.
- `judge_config_digest`: Required for judge work.

Validation rules:

- Candidate work item identity must be stable across compatible resume attempts.
- Judge work item identity must include the candidate output identity and judge
  identity.
- A completed active record with the same work item identity causes the item to
  be skipped during resume.

## Call Budget

Represents the maintainer's explicit permission to spend live provider attempts.

Fields:

- `budget_type`: `candidate` or `judge`.
- `limit`: Maximum provider attempts allowed for this run attempt.
- `planned_new_calls`: New calls scheduled after resume skips are applied.
- `attempted_calls`: Provider attempts made during this run attempt.
- `remaining_calls`: `limit - attempted_calls`.

Validation rules:

- `limit` must be a non-negative integer.
- `planned_new_calls` must be less than or equal to `limit`.
- Every provider attempt consumes one budget unit, including operational errors.

## Run Artifact Set

Represents the files that make a live run durable and resumable.

Files:

- `run.json`: Run metadata and compatibility fields.
- `candidate-records.jsonl`: Append-only candidate output records.
- `judge-records.jsonl`: Append-only judge records when judge work is enabled.
- `summary.json`: Mutable run summary derived from metadata and records.

Validation rules:

- Existing artifacts must be readable before resume.
- Corrupt JSON or JSONL fails resume before provider calls.
- Duplicate active records for the same work item fail resume before provider
  calls.

## Candidate Output Record

Represents one durable result from the production-path eval runner.

Fields:

- `record_id`: Stable record identifier.
- `work_item_id`: Planned candidate work item identity.
- `run_id`: Run that first wrote the record.
- `case_id`: Evaluated case.
- `candidate_model`: Candidate model used.
- `generation_config_digest`: Prompt-affecting config digest.
- `prompt_version`: Prompt version.
- `artifact_schema_version`: Output schema version from spec 010.
- `status`: `completed`, `validation_failed`, or `operational_error`.
- `generated_message`: Generated message when available.
- `validation_outcome`: Production validation result from spec 010.
- `operational_error`: Operational error category and message when applicable.
- `attempt_counted`: Whether the provider attempt consumed budget.
- `created_at`: Timestamp when the record was written.

Validation rules:

- Resume must preserve the record content exactly.
- Records with status `completed`, `validation_failed`, or `operational_error`
  are terminal for the matching work item in this feature.

## Judge Record

Represents one durable judge call result associated with a candidate output.

Fields:

- `record_id`: Stable judge record identifier.
- `work_item_id`: Planned judge work item identity.
- `candidate_record_id`: Candidate output being judged.
- `judge_config_digest`: Judge identity and configuration digest.
- `judge_output_schema_version`: Judge output schema version.
- `status`: `completed` or `operational_error`.
- `judge_output`: Structured judge output when available.
- `operational_error`: Operational error category and message when applicable.
- `attempt_counted`: Whether the provider attempt consumed budget.
- `created_at`: Timestamp when the record was written.

Validation rules:

- Judge rubric and scoring field design are out of scope for this feature.
- Resume must skip completed judge records only when the judge identity matches.

## Resume Identity

Represents the compatibility fingerprint for safe resume.

Fields:

- `suite_id`
- `suite_revision`
- `fixture_revision_digest`
- `case_selection_digest`
- `candidate_models_digest`
- `generation_config_digest`
- `prompt_version`
- `judge_config_digest`
- `rubric_version`
- `artifact_schema_version`
- `candidate_output_schema_version`
- `judge_output_schema_version`

Validation rules:

- Any mismatch in required fields rejects resume before provider calls.
- Mismatch errors must name the incompatible field.
- Unsupported schema versions reject resume before provider calls.

## Run Summary

Represents current aggregate status for maintainers.

Fields:

- `run_id`
- `status`: `planned`, `running`, `interrupted`, `failed`, or `complete`.
- `started_at`
- `updated_at`
- `completed_at`
- `candidate_counts`: Planned, budgeted, attempted, completed, skipped, failed,
  and remaining candidate counts.
- `judge_counts`: Planned, budgeted, attempted, completed, skipped, failed, and
  remaining judge counts.
- `resume_counts`: Prior records reused and new records written.
- `failure_reasons`: Non-empty when status is `interrupted` or `failed`.

State transitions:

- `planned` -> `running` after confirmation and before the first live call.
- `running` -> `interrupted` when user cancellation or process interruption is
  handled after at least one item may have been attempted.
- `running` -> `failed` when an unrecoverable planning or artifact error occurs
  after run start.
- `running` -> `complete` when all planned work items are terminal or skipped.
