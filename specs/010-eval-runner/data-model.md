# Data Model: Production-Path Eval Runner

**Framework Alignment Update (2026-06-14)**: These entities describe logical
gmuse metadata carried by Inspect AI tasks, samples, solvers, scores, and logs.
Inspect logs are the canonical execution artifact. References below to output
records or summaries should be implemented as Inspect sample/result metadata and
Inspect run summaries unless the Inspect spike identifies a required metadata
gap.

## Entity: `EvalRun`

Represents one maintainer-initiated eval runner invocation.

**Fields**:

- `run_id: str`
  - Unique identifier for this run.
- `created_at: str`
  - Timestamp in ISO 8601 format.
- `execution_mode: Literal["check", "live"]`
  - Whether the invocation uses deterministic local output or live provider calls.
- `suite_id: str`
  - Selected suite from the spec 009 suite catalog.
- `models: list[str]`
  - Candidate model identifiers selected for live generation. Empty in check mode.
- `guardrails: dict[str, str | int | float | bool | None]`
  - Configured live-run limits such as sample, token, cost, time, or concurrency
    limits.
- `output_dir: str`
  - Directory or Inspect log location where local eval logs are written.
- `schema_version: str`
  - Version for the run artifact shape.
- `runner_version: str`
  - gmuse/eval runner version or source revision used for the run.
- `project_revision: str | None`
  - Current gmuse repository commit SHA when available.
- `project_dirty: bool | None`
  - Whether the gmuse working tree had uncommitted changes when available.

**Rules**:

- Check mode must not call providers and must not accept candidate model names.
- Live mode must require at least one model, plan display, confirmation, and
  meaningful guardrails.
- A run must reference one validated spec 009 suite.
- Each invocation owns an independent Inspect log identity unless an explicit
  log/output location is provided.
- Existing conflicting logs or explicit output locations must fail the run before
  execution unless Inspect-native append/resume behavior is intentionally used.

## Entity: `RunPlan`

Represents the fully resolved set of entries for an eval run.

**Fields**:

- `run_id: str`
- `execution_mode: Literal["check", "live"]`
- `suite_id: str`
- `suite_version: str`
- `case_count: int`
- `entry_count: int`
- `planned_samples: int`
- `guardrails: dict[str, str | int | float | bool | None]`
- `entries: list[RunEntry]`
- `inspect_log_location: str`

**Rules**:

- In check mode, live provider calls must be `0`.
- In live mode, `planned_samples` equals selected cases multiplied by selected
  model/config combinations.
- Live mode must fail before provider calls if `planned_samples` exceeds a
  configured sample limit.
- Entries with invalid fixtures must be rejected before check or live execution.
- The run plan may be displayed by gmuse and represented in Inspect task/log
  metadata; a bespoke `run-plan.json` is not required.

## Entity: `RunEntry`

Represents one planned case/model/config entry.

**Fields**:

- `entry_id: str`
  - Stable within one run.
- `suite_id: str`
- `case_id: str`
- `case_revision: str`
- `fixture_id: str`
- `fixture_revision: str`
  - Revision or digest supplied by spec 009.
- `rubric_id: str`
- `rubric_version: str`
- `candidate_kind: Literal["deterministic_check", "live_model"]`
- `model: str | None`
  - Null in check mode, required in live mode.
- `deterministic_output_policy: str | None`
  - Check-mode policy identifier, such as `format_valid_v1`.
- `generation_config: GenerationConfig`

**Rules**:

- Each `RunEntry` produces exactly one Inspect sample result when execution
  reaches the entry.
- The fixture must be validated by spec 009 before execution.
- The plan stores lightweight suite, case, fixture, and rubric identity so
  scoring can resolve the canonical staged diff and rubric from spec 009 assets.
- Check-mode entries are not candidate model evidence and should be skipped by
  judge scoring unless a future diagnostic mode explicitly opts in.

## Entity: `GenerationConfig`

Represents message-generation settings applied to an entry.

**Fields**:

- `format: Literal["freeform", "conventional", "gitmoji"]`
- `history_depth: int`
- `include_branch: bool`
- `hint: str | None`
- `repository_instructions: str | None`
- `max_chars: int | None`
- `temperature: float | None`
- `max_tokens: int | None`

**Validation Rules**:

- Values must be resolved before execution so result artifacts can be interpreted later.
- Case-level fixture settings from spec 009 may provide defaults, and explicit runner overrides may replace them.
- Check mode should use each case's effective settings rather than forcing a
  single simplified configuration.
- `max_chars`, when set, must use the same production validation behavior as normal gmuse generation.

## Entity: `CaseExecution`

Represents runtime state for executing one entry.

**Fields**:

- `entry: RunEntry`
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
5. Invoke the lower-level production generation attempt path.
6. In check mode, substitute only deterministic local output for the provider response.
7. Run production validation.
8. Write exactly one Inspect sample result for the entry.
9. Clean up temporary repository unless debug preservation is explicitly enabled.

## Entity: `GenerationAttemptResult`

Represents the lower-level production generation outcome used by evals.

**Fields**:

- `message: str | None`
- `context: GenerationContext`
- `prompt_metadata: GenerationPromptMetadata`
- `validation: ValidationOutcome`
- `operational_error: OperationalError | None`

**Rules**:

- A provider response that fails production validation must preserve `message`.
- Existing `generate_message()` behavior remains unchanged and may raise on
  failed validation for normal users.
- The attempt path exists so eval tooling can record raw outputs and
  deterministic validation outcomes without changing normal generation behavior.

## Entity: `GenerationPromptMetadata`

Represents prompt observations captured by the production generation path.

**Fields**:

- `prompt_hash: str`
- `prompt_size_bytes: int`
- `estimated_input_tokens: int | None`
- `prompt_version: str`

**Rules**:

- `prompt_hash` must be derived from the rendered production prompt.
- Raw prompt text is omitted from this entity.

## Entity: `ContextMetadata`

Represents prompt/context observations captured without storing raw prompt text by default.

**Fields**:

- `prompt_hash: str`
- `prompt_size_bytes: int`
- `estimated_input_tokens: int | None`
- `estimated_output_tokens: int | None`
- `prompt_version: str`
- `diff_truncated: bool`
- `history_commit_count: int`
- `branch_context_included: bool`
- `repository_instructions_included: bool`
- `max_chars: int | None`

**Rules**:

- Raw prompt text is omitted from main artifacts.
- When debug preservation is selected, raw prompt text may be written to a
  separate `debug/prompts/<entry_id>.json` artifact.
- Metadata must be sufficient to compare prompt-size changes in later baseline work.

## Entity: `InspectSampleResult`

Represents the gmuse metadata that must be attached to one Inspect sample result
for one executed case/model/config entry.

**Fields**:

- `metadata_schema_version: str`
- `run_id: str`
- `entry_id: str`
- `execution_mode: Literal["check", "live"]`
- `candidate_kind: Literal["deterministic_check", "live_model"]`
- `suite_id: str`
- `case_id: str`
- `fixture_id: str`
- `fixture_revision: str`
- `model: str | None`
- `deterministic_output_policy: str | None`
- `generation_config: GenerationConfig`
- `context_metadata: ContextMetadata`
- `generated_message: str | None`
- `validation: ValidationOutcome`
- `operational_error: OperationalError | None`
- `timing: Timing`

**Rules**:

- A successful provider or deterministic local response with invalid gmuse output still records `generated_message`.
- `operational_error` is set for setup/provider failures that prevent a normal generated message.
- Check-mode sample results must be clearly marked as deterministic check output and
  are not model evaluation evidence.
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
- Per-entry operational errors should not stop later entries when the run can
  continue safely.

## Entity: `RunSummary`

Represents Inspect-native run summary information plus gmuse metadata needed for
maintainer review.

**Fields**:

- `schema_version: str`
- `run_id: str`
- `execution_mode: Literal["check", "live"]`
- `suite_id: str`
- `models: list[str]`
- `candidate_kind: Literal["deterministic_check", "live_model"]`
- `inspect_log_location: str`
- `planned_entries: int`
- `planned_samples: int`
- `guardrails: dict[str, str | int | float | bool | None]`
- `completed_entries: int`
- `validation_passed: int`
- `validation_failed: int`
- `operational_errors: dict[str, int]`
- `status: Literal["completed", "failed", "interrupted"]`
- `started_at: str`
- `completed_at: str | None`

**Rules**:

- The summary must not hide per-case Inspect sample results; it points to the
  Inspect log location.
- The summary may include interrupted counts for completed entries but must not
  implement custom resume behavior in this spec.
- The summary must not imply model quality results for check mode.
- Baseline, judge, and recommendation summaries are out of scope.

## Relationships

- An `EvalRun` owns one `RunPlan`.
- A `RunPlan` contains one or more `RunEntry` entities.
- A `RunEntry` produces exactly one `InspectSampleResult` once execution reaches it.
- A `CaseExecution` is the runtime realization of a `RunEntry`.
- A `GenerationAttemptResult` supplies generated output, prompt metadata, and validation details for an `InspectSampleResult`.
- A `RunSummary` aggregates counts and artifact paths for one `EvalRun`.
