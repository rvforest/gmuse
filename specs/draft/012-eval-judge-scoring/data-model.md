# Data Model: Eval Judge And Scoring

**Date**: 2026-06-11
**Feature**: `012-eval-judge-scoring`

## Entity Relationships

```text
RunnerOutputRecord (from spec 010 outputs.jsonl or spec 011 candidate-records.jsonl)
  └── ScoredOutputRecord
        ├── DeterministicCheckResult[*]
        ├── HardFailureGate[*]
        ├── JudgeResult? / JudgeOperationalError?
        ├── EffectiveScore
        ├── ManualAnnotation[*]
        └── ManualOverride[*]

ScoringRunSummary
  ├── JudgeConfiguration
  ├── JudgeCalibrationReport?
  ├── BudgetAccounting (from spec 011)
  └── ScoredOutputRecord[*]
```

## RunnerOutputRecord

Represents an input record produced by the production-path eval runner from spec
010 or a resumable candidate record from spec 011.

Required fields consumed by this feature:

- `source_kind`: `spec010_output` or `spec011_candidate_record`.
- `run_id`: Source runner run identifier.
- `attempt_id`: Spec 010 attempt identifier when consuming `outputs.jsonl`.
- `record_id`: Spec 011 candidate record identifier when consuming
  `candidate-records.jsonl`.
- `work_item_id`: Spec 011 work item identifier when available.
- `suite_id`, `suite_version`: Suite identity.
- `case_id`, `case_revision`: Case identity.
- `fixture_id`, `fixture_revision`: Fixture identity where available.
- `schema_version` or `artifact_schema_version`: Runner artifact schema version.
- `candidate_model`: Provider/model metadata for the generated output.
- `generation_config`: Format, history, branch, hint, token, temperature, and
  `max_chars` settings used by the runner.
- `context_metadata`: Prompt hash, prompt size, estimated tokens, and context
  metadata captured by spec 010.
- `staged_diff`: Raw staged diff or reference to the local artifact containing
  it.
- `case_rubric`: Rubric fields needed for scoring.
- `generated_message`: Raw model output when generation reached message output.
- `validation`: Production validation result and error details.
- `operational_error`: Candidate provider/runtime error, if no usable generated
  message exists.

Validation rules:

- Records with `operational_error` and no `generated_message` are not
  judge-eligible.
- Records must include enough suite/case/model/config identity to make scored
  artifacts traceable.
- Records with incompatible or unsupported schema versions must be rejected or
  marked unscored with a compatibility error.

## ScoredOutputRecord

Represents the complete scoring result for one runner output.

Fields:

- `scoring_schema_version`: Version of the scored artifact schema.
- `source`: Source identity containing either spec 010 `run_id` + `attempt_id`
  or spec 011 `run_id` + `record_id` + `work_item_id`.
- `scoring_run_id`: Identifier for the scoring run.
- `scored_at`: Timestamp for automated scoring.
- `deterministic_checks`: List of deterministic check results.
- `hard_failure_gates`: List of hard failure gates that fired.
- `judge_configuration`: Fixed judge configuration used or planned.
- `judge_result`: Structured judge output when a judge call succeeds.
- `judge_operational_error`: Operational scoring failure when a judge call fails.
- `quality_errors`: Versioned quality/compliance categories.
- `operational_errors`: Versioned judge/provider operational categories.
- `self_judged`: Boolean self-judge flag.
- `judge_input_controls`: JudgeInputControls used for the judge request.
- `effective_score`: Final effective score after hard gates and overrides.
- `manual_annotations`: Reviewer notes.
- `manual_overrides`: Reviewer override records.

Validation rules:

- `hard_failed=true` whenever `hard_failure_gates` is non-empty.
- A hard-failed record must have effective usability `unusable`.
- `judge_result` and `judge_operational_error` are mutually exclusive for a
  single judge attempt.
- Per-dimension scores must remain available when `judge_result` exists, even if
  `hard_failed=true`.
- Manual overrides must reference fields that are allowed to affect effective
  scores or gates.

## DeterministicCheckResult

Represents one objective check performed before judge scoring.

Fields:

- `check_id`: Stable check identifier, such as `production_validation`,
  `max_chars`, `privacy_patterns`, `extra_output`, or `injection_markers`.
- `status`: `pass`, `fail`, or `not_applicable`.
- `severity`: `info`, `warning`, or `hard_failure`.
- `evidence`: Concise evidence string or structured detail.
- `quality_errors`: Error categories caused by the check.

Validation rules:

- Checks that fail with severity `hard_failure` must create a corresponding
  hard failure gate.
- `not_applicable` checks must explain why they did not apply, such as no
  `max_chars` configured.

## HardFailureGate

Represents a zero-tolerance failure.

Fields:

- `gate`: One of `privacy_leak`, `severe_injection_followed`,
  `production_validation_failed`, or `max_chars_exceeded`.
- `source`: `deterministic_check`, `judge_result`, or `manual_override`.
- `evidence`: Concise evidence suitable for maintainer review.

Validation rules:

- Any gate forces `effective_score.usability` to `unusable`.
- Gates must remain visible even when a manual override changes another score.

## JudgeConfiguration

Represents the fixed judge setup for a scoring run.

Fields:

- `judge_provider`: Provider identifier.
- `judge_model`: Model identifier.
- `judge_prompt_version`: Version of the judge prompt.
- `rubric_version`: Version of the scoring rubric contract.
- `parameters`: Temperature, max tokens, response format, timeout, and other
  judge-call parameters.
- `calibration_report_id: str | None`
  - Calibration report used to validate this judge configuration, when available.
- `budget`: Planned and remaining judge-call budget from spec 011.

Validation rules:

- Comparable outputs in one scoring run must use the same configuration.
- Configuration changes during resume must be rejected unless the maintainer
  starts a new scoring run.

## JudgeInputControls

Represents bias-control metadata for the prompt sent to the judge.

Fields:

- `candidate_identity_hidden: bool`
- `candidate_identity_inclusion_reason: str | None`
- `pairwise_order: Literal["not_applicable", "baseline_first", "candidate_first", "randomized", "order_swapped"]`
- `order_swap_group_id: str | None`

Validation rules:

- `candidate_identity_hidden` should be true for ordinary scoring.
- If candidate identity is included, a diagnostic reason must be recorded.
- Pairwise ordering fields are required only when pairwise judge scoring is
  supported by a future extension.

## JudgeResult

Represents parsed LLM-as-judge output.

Fields:

- `judge_output_schema_version`: Structured judge response version.
- `scores`: Numeric dimension scores.
- `usability`: Categorical usability.
- `hard_failure_findings`: Judge-identified hard failures.
- `quality_errors`: Quality/compliance taxonomy categories.
- `rationales`: Concise rationale per scored dimension.
- `raw_response_metadata`: Provider response id, token usage if available, and
  finish reason.

Validation rules:

- Numeric scores must be integers from 1 through 5.
- `usability` must be one of `usable`, `minor_edit`, `major_edit`, or
  `unusable`.
- Categories must come from the active taxonomy version.

## EffectiveScore

Represents final reviewer-facing scoring after gates and overrides.

Fields:

- `accuracy`: Numeric score or null.
- `quality`: Numeric score or null.
- `style_history_fit`: Numeric score or null when not applicable.
- `aggregate`: Secondary numeric aggregate or null.
- `usability`: Effective usability category.
- `hard_failed`: Boolean.
- `derived_from`: `automated`, `manual_override`, or `mixed`.

Validation rules:

- Aggregates are not computed when required numeric dimensions are missing.
- Hard failure gates take precedence over aggregate score.

## ManualAnnotation

Represents reviewer context that does not change effective scoring.

Fields:

- `annotation_id`: Stable annotation identifier.
- `reviewer`: Reviewer identity or label.
- `created_at`: Timestamp.
- `note`: Reviewer note.

Validation rules:

- Notes must not alter effective score fields.

## ManualOverride

Represents reviewer correction to effective scoring.

Fields:

- `override_id`: Stable override identifier.
- `reviewer`: Reviewer identity or label.
- `created_at`: Timestamp.
- `target_fields`: Fields being overridden.
- `replacement_values`: New effective values.
- `rationale`: Required reason.

Validation rules:

- Overrides must preserve original deterministic checks and judge output.
- Overrides must include a rationale and reviewer label.
- Overrides may change effective categories and scores but must not delete source
  evidence.

## ScoringRunSummary

Represents aggregate metadata and counts for a scoring run.

Fields:

- `scoring_run_id`: Stable scoring run identifier.
- `created_at`, `completed_at`: Timestamps.
- `source_run_id`: Runner or live-run identifier.
- `judge_configuration`: Fixed judge setup.
- `calibration_report_ref`: Calibration report identifier or null.
- `budget_accounting`: Planned, budgeted, completed, skipped, and failed judge
  call counts from spec 011.
- `counts`: Totals by scored, unscored, hard failed, self-judged, operational
  error, usability category, and error category.
- `schema_versions`: Runner, scoring, judge output, taxonomy, rubric, and judge
  prompt versions.

Validation rules:

- Summary counts must match the scored JSONL records.
- Resume summaries must distinguish skipped compatible records from newly scored
  records.

## JudgeCalibrationReport

Represents an offline or live calibration result for one judge prompt, rubric,
and model configuration.

Fields:

- `calibration_report_id: str`
- `created_at: str`
- `judge_configuration: JudgeConfiguration`
- `calibration_case_count: int`
- `expected_label_version: str`
- `agreement_by_dimension: dict[str, float]`
- `parse_failure_count: int`
- `hard_failure_agreement: float | None`
- `usability_agreement: float | None`
- `bias_controls: JudgeInputControls`
- `notes: str | None`

Validation rules:

- Calibration examples must be manually annotated.
- Calibration must preserve expected labels and judge outputs separately.
- Calibration does not prove judge correctness, but it must be recorded when it
  is used to justify promoted regression evidence.
