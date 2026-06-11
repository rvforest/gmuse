# Data Model: production-path eval runner

## Entity: `EvalRun`

Represents one maintainer-initiated eval runner invocation.

**Fields**:

- `run_id: str`
  - Unique identifier for this run.
- `created_at: str`
  - Timestamp in ISO 8601 format.
- `mode: Literal["plan", "execute"]`
  - Whether the invocation previews or performs generation attempts.
- `suite_ids: list[str]`
  - Selected suites from the spec 009 suite catalog.
- `models: list[str]`
  - Candidate model identifiers selected for generation.
- `output_dir: str`
  - Directory where run artifacts are written.
- `artifact_schema_version: str`
  - Version for output records and summaries.
- `runner_version: str`
  - gmuse/eval runner version or source revision used for the run.

**Rules**:

- `mode = "plan"` must not produce generation output records or call providers.
- `mode = "execute"` may call providers only for the resolved attempts in the run plan.
- A run must reference validated spec 009 suites/cases.

## Entity: `RunPlan`

Represents the fully resolved set of attempts for an eval run.

**Fields**:

- `run_id: str`
- `suite_ids: list[str]`
- `case_count: int`
- `attempt_count: int`
- `attempts: list[RunAttempt]`
- `output_records_path: str`
- `summary_path: str`

**Rules**:

- `attempt_count` equals selected cases multiplied by selected model/config combinations.
- A run plan may be displayed in planning mode without creating output records.
- Attempts with invalid fixtures must be rejected before execution.

## Entity: `RunAttempt`

Represents one planned case/model/config combination.

**Fields**:

- `attempt_id: str`
  - Stable within one run.
- `suite_id: str`
- `case_id: str`
- `fixture_id: str`
- `fixture_revision: str`
  - Revision or digest supplied by spec 009.
- `model: str`
- `generation_config: GenerationConfig`

**Rules**:

- Each `RunAttempt` can produce at most one `OutputRecord`.
- The fixture must be validated by spec 009 before execution.

## Entity: `GenerationConfig`

Represents message-generation settings applied to an attempt.

**Fields**:

- `format: Literal["freeform", "conventional", "gitmoji"]`
- `history_depth: int`
- `include_branch: bool`
- `hint: str | None`
- `repository_instructions: str | None`
- `max_chars: int | None`
- `temperature: float | None`
- `max_tokens: int | None`
- `model: str`

**Validation Rules**:

- Values must be resolved before execution so result artifacts can be interpreted later.
- Case-level fixture settings from spec 009 may provide defaults, and explicit runner overrides may replace them.
- `max_chars`, when set, must use the same production validation behavior as normal gmuse generation.

## Entity: `CaseExecution`

Represents runtime state for executing one attempt.

**Fields**:

- `attempt: RunAttempt`
- `temporary_repository_path: str`
- `staged_diff_digest: str`
- `context_metadata: ContextMetadata`
- `started_at: str`
- `completed_at: str | None`
- `duration_ms: int | None`
- `preserved_debug_artifacts: bool`

**State Transitions**:

1. Resolve validated fixture and suite membership from spec 009.
2. Create isolated temporary repository.
3. Apply fixture history and staged changes.
4. Verify staged diff digest from spec 009.
5. Invoke production generation path.
6. Run production validation.
7. Write exactly one output record for the attempt.
8. Clean up temporary repository unless debug preservation is explicitly enabled.

## Entity: `ContextMetadata`

Represents prompt/context observations captured without storing raw prompt text by default.

**Fields**:

- `prompt_hash: str`
- `prompt_size_bytes: int`
- `estimated_input_tokens: int | None`
- `estimated_output_tokens: int | None`
- `diff_truncated: bool`
- `history_commit_count: int`
- `branch_context_included: bool`
- `repository_instructions_included: bool`
- `max_chars: int | None`

**Rules**:

- `prompt_hash` must be derived from the rendered production prompt.
- Raw prompt text is omitted unless explicit debug mode is selected.
- Metadata must be sufficient to compare prompt-size changes in later baseline work.

## Entity: `OutputRecord`

Represents one JSONL record for one attempted case/model/config combination.

**Fields**:

- `schema_version: str`
- `run_id: str`
- `attempt_id: str`
- `suite_id: str`
- `case_id: str`
- `fixture_id: str`
- `fixture_revision: str`
- `model: str`
- `generation_config: GenerationConfig`
- `context_metadata: ContextMetadata`
- `generated_message: str | None`
- `validation: ValidationOutcome`
- `operational_error: OperationalError | None`
- `timing: Timing`

**Rules**:

- A successful provider response with invalid gmuse output still records `generated_message`.
- `operational_error` is set for setup/provider failures that prevent a normal generated message.
- Judge scores, aggregate scores, baseline identifiers, and recommendation fields are not allowed in this schema version.

## Entity: `ValidationOutcome`

Represents deterministic production validation for a generated message.

**Fields**:

- `status: Literal["passed", "failed", "not_run"]`
- `error_categories: list[str]`
- `details: str | None`

**Rules**:

- `status = "not_run"` only when an operational error prevents validation.
- Format and `max_chars` failures are deterministic validation failures.
- Accuracy, quality, hallucination, and usability scoring are not part of this entity.

## Entity: `OperationalError`

Represents setup or provider failure separately from deterministic validation.

**Fields**:

- `category: Literal["auth_error", "rate_limit", "timeout", "network_error", "context_length", "empty_response", "fixture_setup_error", "unknown_error"]`
- `message: str`
- `provider_status: str | None`
- `retryable: bool`

**Rules**:

- Provider authentication, rate limit, network, timeout, context length, and empty response failures are operational errors.
- Fixture reconstruction and staged diff verification failures are `fixture_setup_error`.
- Validation failures from a received model response are not operational errors.

## Entity: `RunSummary`

Represents the JSON summary artifact for one run.

**Fields**:

- `schema_version: str`
- `run_id: str`
- `mode: Literal["plan", "execute"]`
- `suite_ids: list[str]`
- `models: list[str]`
- `artifact_paths: dict[str, str]`
- `planned_attempts: int`
- `completed_attempts: int`
- `validation_passed: int`
- `validation_failed: int`
- `operational_errors: dict[str, int]`
- `started_at: str`
- `completed_at: str`

**Rules**:

- The summary must not hide per-case records; it points to them.
- The summary may include counts for planning mode but must not imply model quality results.
- Baseline, judge, and recommendation summaries are out of scope.

## Relationships

- An `EvalRun` owns one `RunPlan`.
- A `RunPlan` contains one or more `RunAttempt` entities.
- A `RunAttempt` produces zero records in planning mode and exactly one `OutputRecord` in execution mode.
- A `CaseExecution` is the runtime realization of a `RunAttempt`.
- A `RunSummary` aggregates counts and artifact paths for one `EvalRun`.
