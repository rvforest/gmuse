# Data Model: eval baselines and comparison

## Entity: `BaselinePromotionRequest`

Represents the maintainer's explicit request to convert a completed scored eval
run into a promoted baseline artifact.

**Fields**:

- `source_result_artifact: str`
  - Path or artifact reference for the spec 010 run result.
- `source_scored_artifact: str`
  - Path or artifact reference for the spec 012 scored output.
- `baseline_id: str`
  - Stable maintainer-selected identifier for the promoted baseline.
- `label: str`
  - Human-readable baseline label.
- `description: str | None`
  - Optional maintainer note explaining why this result was promoted.
- `promoted_at: str`
  - ISO-8601 timestamp for promotion.
- `promoted_by: str | None`
  - Optional local maintainer identity.
- `retain_debug_fields: bool`
  - Whether debug-only fields should be copied into the baseline.
- `output_path: str`
  - Destination path for the baseline artifact.

**Validation Rules**:

- `source_result_artifact` must include required result metadata from spec 010.
- `source_scored_artifact` must include required scoring metadata from spec 012.
- The source artifacts must describe the same eval run or have a recorded join
  relationship that proves the scored artifact was produced from the result
  artifact.
- Promotion must fail when required suite, case, model, config, prompt, judge,
  score, or schema metadata is missing.
- `retain_debug_fields` defaults to `false`.

## Entity: `BaselineArtifact`

Represents the durable comparison reference created by baseline promotion.

**Fields**:

- `schema_version: str`
  - Baseline artifact schema version.
- `baseline_id: str`
  - Stable identifier selected during promotion.
- `label: str`
  - Human-readable baseline label.
- `description: str | None`
  - Maintainer note.
- `created_at: str`
  - Promotion timestamp.
- `source_artifacts: SourceArtifactSet`
  - References to source result and scored artifacts.
- `suite: SuiteSnapshot`
  - Suite metadata and membership used by the promoted run.
- `model: ModelSnapshot`
  - Candidate model identity and resolved metadata.
- `generation_config: GenerationConfigSnapshot`
  - Prompt-affecting and output-affecting generation settings.
- `judge: JudgeSnapshot`
  - Judge model, prompt, rubric, and scoring metadata from spec 012.
- `judge_calibration: JudgeCalibrationSnapshot | None`
  - Judge calibration metadata from spec 012 when available.
- `cases: list[BaselineCaseRecord]`
  - Per-case promoted outputs and scores.
- `debug_fields_retained: bool`
  - Whether optional debug fields were retained.

**Rules**:

- Baselines are immutable after promotion; a new promotion creates a new
  baseline artifact.
- `cases` must include one record per promoted case.
- Debug-only and transient fields are absent unless `debug_fields_retained` is
  true.
- Generated messages and comparison-critical metadata are preserved even when a
  case has a hard failure or operational error.

## Entity: `SourceArtifactSet`

Represents provenance for promoted or compared artifacts.

**Fields**:

- `result_artifact_uri: str`
- `result_artifact_schema_version: str`
- `scored_artifact_uri: str`
- `scored_artifact_schema_version: str`
- `run_id: str`
- `scoring_run_id: str | None`
- `created_at: str | None`

**Rules**:

- `run_id` must match, or the scored artifact must explicitly reference the
  result run it scored.
- Schema versions are preserved for compatibility warnings.

## Entity: `SuiteSnapshot`

Represents suite and case-set metadata at the time of a run.

**Fields**:

- `suite_id: str`
- `suite_version: str`
- `suite_revision: str | None`
- `case_ids: list[str]`
- `case_revisions: dict[str, str]`
- `fixture_revisions: dict[str, str]`

**Rules**:

- Case identity is matched by stable `case_id`.
- Case and fixture revisions are used to warn about non-identical evidence.

## Entity: `ModelSnapshot`

Represents candidate model identity for comparison.

**Fields**:

- `provider: str`
- `requested_model: str`
- `resolved_model: str | None`
- `model_revision: str | None`
- `endpoint_profile: str | None`
- `self_judged: bool | None`

**Rules**:

- Same-model regression mode treats differences in these fields as high-severity
  incompatibilities unless the field is explicitly documented as unavailable in
  both artifacts.
- Benchmark mode allows differences but records them in report metadata.

## Entity: `GenerationConfigSnapshot`

Represents prompt-affecting and output-affecting settings.

**Fields**:

- `format: str`
- `history_depth: int`
- `include_branch: bool`
- `branch_max_length: int | None`
- `max_chars: int | None`
- `temperature: float | None`
- `max_tokens: int | None`
- `prompt_version: str`
- `runner_config_hash: str | None`

**Rules**:

- Same-model regression mode treats differences as high-severity compatibility
  warnings because output changes may be caused by config changes rather than
  code or prompt changes.

## Entity: `JudgeSnapshot`

Represents scoring context from spec 012.

**Fields**:

- `judge_model: str`
- `judge_prompt_version: str`
- `rubric_version: str`
- `scoring_schema_version: str`
- `judge_parameters_hash: str | None`
- `self_judged: bool`

**Rules**:

- Differences do not necessarily invalidate report generation, but score deltas
  must be warned as potentially scoring-driven.
- `self_judged = true` should be visible in comparison reports.

## Entity: `JudgeCalibrationSnapshot`

Represents judge calibration evidence from spec 012.

**Fields**:

- `calibration_report_id: str | None`
- `calibration_schema_version: str | None`
- `expected_label_version: str | None`
- `calibration_case_count: int | None`
- `agreement_by_dimension: dict[str, float]`
- `parse_failure_count: int | None`
- `candidate_identity_hidden: bool | None`

**Rules**:

- Missing calibration metadata does not prevent comparison, but it must produce a
  warning when the other artifact includes calibration metadata.
- Differences in calibration report ID, expected label version, or agreement
  values must warn that score deltas may reflect judge calibration changes.

## Entity: `BaselineCaseRecord`

Represents one promoted case result.

**Fields**:

- `case_id: str`
- `case_revision: str`
- `fixture_revision: str`
- `generated_message: str | None`
- `output_record_id: str | None`
- `prompt_hash: str | None`
- `prompt_size_bytes: int | None`
- `estimated_prompt_tokens: int | None`
- `first_shot_success: bool`
- `production_validation_passed: bool`
- `scores: DimensionScoreSet`
- `usability: str | None`
- `hard_failures: HardFailureSet`
- `error_categories: list[str]`
- `operational_errors: list[str]`
- `judge_rationales: dict[str, str]`
- `manual_overrides: list[ManualOverride]`

**Validation Rules**:

- `case_id` must be unique within a baseline artifact.
- Hard failures are preserved even when score values are missing because of
  operational or judge failures.
- Operational errors are stored separately from quality/compliance error
  categories.

## Entity: `DimensionScoreSet`

Represents scored dimensions for a case.

**Fields**:

- `accuracy: float | None`
- `quality: float | None`
- `format_compliance: float | bool | None`
- `privacy: float | bool | None`
- `injection_resistance: float | bool | None`
- `style_fit: float | None`
- `aggregate: float | None`
- `additional_dimensions: dict[str, float | bool | str | None]`

**Rules**:

- Per-dimension scores are the source of truth; aggregate scores are secondary.
- Aggregate deltas are reported only when both artifacts use compatible scoring
  schema and aggregate weighting metadata.

## Entity: `HardFailureSet`

Represents zero-tolerance failure gates.

**Fields**:

- `privacy_leak: bool`
- `severe_injection_obedience: bool`
- `production_validation_failure: bool`
- `other: list[str]`

**Rules**:

- Any new hard failure is flagged independently of score movement.
- Removed hard failures are reported as improvements but do not hide unrelated
  regressions.

## Entity: `ComparisonRequest`

Represents a maintainer comparison invocation.

**Fields**:

- `baseline_artifact: str`
- `candidate_result_artifact: str`
- `candidate_scored_artifact: str`
- `mode: Literal["regression", "benchmark"]`
- `output_path: str | None`
- `include_messages: bool`
- `fail_on_new_hard_failure: bool`

**Rules**:

- `mode = "regression"` is the default and expects same-model evidence.
- `mode = "benchmark"` must be explicit when model metadata differs.
- Report generation must not make live candidate or judge calls.
- `fail_on_new_hard_failure` may affect command exit status, but the report must
  still avoid hardcoded accept/reject decisions.

## Entity: `CompatibilityWarning`

Represents a structured comparability concern.

**Fields**:

- `code: str`
- `severity: Literal["info", "warning", "high", "blocking"]`
- `scope: Literal["report", "suite", "case", "model", "config", "prompt", "judge", "schema"]`
- `affected_cases: list[str]`
- `baseline_value: str | int | float | bool | None`
- `candidate_value: str | int | float | bool | None`
- `message: str`
- `evidence_classification: Literal["clean_regression", "degraded_regression", "benchmark", "invalid"]`

**Rules**:

- Warnings must be machine-readable and human-readable.
- Same-model regression model/config mismatches are at least `high` severity.
- Blocking warnings prevent a clean regression classification.

## Entity: `PairwiseCaseDelta`

Represents one baseline-versus-candidate case comparison.

**Fields**:

- `case_id: str`
- `baseline_case_revision: str | None`
- `candidate_case_revision: str | None`
- `baseline_fixture_revision: str | None`
- `candidate_fixture_revision: str | None`
- `baseline_output_ref: str | None`
- `candidate_output_ref: str | None`
- `score_deltas: dict[str, float | int | bool | str | None]`
- `hard_failure_delta: HardFailureDelta`
- `prompt_hash_changed: bool | None`
- `prompt_size_delta_bytes: int | None`
- `estimated_prompt_token_delta: int | None`
- `first_shot_success_delta: Literal["unchanged_success", "unchanged_failure", "gained", "lost", "unknown"]`
- `error_category_delta: CategoryDelta`
- `operational_error_delta: CategoryDelta`
- `warnings: list[CompatibilityWarning]`

**Rules**:

- Records are created for every shared case ID.
- Missing baseline-only or candidate-only cases are recorded separately in the
  report rather than silently omitted.

## Entity: `HardFailureDelta`

Represents hard-failure movement for one case.

**Fields**:

- `new_failures: list[str]`
- `removed_failures: list[str]`
- `unchanged_failures: list[str]`
- `unchanged_passes: list[str]`

**Rules**:

- `new_failures` must be highlighted in summaries.
- New privacy, severe injection, or production validation failures are always
  report-level hard-failure flags.

## Entity: `CategoryDelta`

Represents category movement for quality/compliance or operational errors.

**Fields**:

- `added: list[str]`
- `removed: list[str]`
- `unchanged: list[str]`

## Entity: `ComparisonReport`

Represents the durable output of comparison.

**Fields**:

- `schema_version: str`
- `created_at: str`
- `mode: Literal["regression", "benchmark"]`
- `evidence_classification: Literal["clean_regression", "degraded_regression", "benchmark", "invalid"]`
- `baseline: SourceArtifactSet`
- `candidate: SourceArtifactSet`
- `warnings: list[CompatibilityWarning]`
- `summary: ComparisonSummary`
- `pairwise_cases: list[PairwiseCaseDelta]`
- `baseline_only_cases: list[str]`
- `candidate_only_cases: list[str]`

**Rules**:

- The report must be reproducible from saved baseline and candidate artifacts.
- The report must not include public recommendations or provider preference
  claims.
- Summary data must not replace per-case evidence.

## Entity: `ComparisonSummary`

Represents report-level aggregate evidence.

**Fields**:

- `shared_case_count: int`
- `baseline_only_case_count: int`
- `candidate_only_case_count: int`
- `new_hard_failure_count: int`
- `removed_hard_failure_count: int`
- `first_shot_success_gained_count: int`
- `first_shot_success_lost_count: int`
- `score_delta_summary: dict[str, float | int | None]`
- `prompt_size_delta_summary: dict[str, float | int | None]`
- `error_category_delta_summary: CategoryDelta`
- `operational_error_delta_summary: CategoryDelta`

**Rules**:

- Summary fields are derived from `pairwise_cases`.
- Aggregate score movement must be labeled secondary to per-dimension and
  hard-failure evidence.
