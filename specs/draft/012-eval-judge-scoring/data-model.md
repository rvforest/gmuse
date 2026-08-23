# Data Model: Eval Judge And Scoring

**Date**: 2026-06-11
**Feature**: `012-eval-judge-scoring`

**Framework Alignment Update (2026-06-14)**: These entities describe scoring
metadata attached to Inspect sample results by gmuse deterministic scorers and
LLM-as-judge scorers. Inspect logs are the canonical scored evidence.

## Entity Relationships

```text
InspectSampleResult (from specs 010/011)
  └── ScoredSampleMetadata
        ├── DeterministicCheckResult[*]
        ├── HardFailureGate[*]
        ├── JudgeResult? / JudgeOperationalError?
        └── EffectiveScore
```

## InspectSampleResult

Represents the candidate generation sample result produced by the Inspect-backed
runner.

Required fields consumed by scoring:

- run/sample identity
- suite, case, fixture, and rubric identity
- model and generation config metadata
- generated message when available
- production validation outcome
- operational error when generation failed before output
- prompt/context metadata

## ScoredSampleMetadata

Represents scoring metadata attached to an Inspect sample result.

Fields:

- `scoring_schema_version`
- `scoring_status`: `scored` or `unscored`
- `unscored_reason`
- `deterministic_checks`
- `hard_failure_gates`
- `judge_configuration`
- `judge_result`
- `judge_operational_error`
- `quality_errors`
- `operational_errors`
- `self_judged`
- `judge_input_controls`
- `effective_score`
- `calibration_report_id`

Rules:

- Candidate operational errors without generated messages are unscored.
- Deterministic hard failures are not judge-eligible by default.
- `judge_result` and `judge_operational_error` are mutually exclusive for a
  single judge attempt.
- Hard failures force effective usability to `unusable`.

## DeterministicCheckResult

Fields:

- `check_id`
- `status`: `pass`, `fail`, or `not_applicable`
- `severity`: `info`, `warning`, or `hard_failure`
- `evidence`
- `quality_errors`

Rules:

- Failing hard-failure checks create matching hard failure gates.
- `not_applicable` checks explain why the check did not apply.

## HardFailureGate

Fields:

- `gate`: `privacy_leak`, `severe_injection_followed`,
  `production_validation_failed`, `max_chars_exceeded`, or `other`
- `source`: `deterministic_check`, `judge_result`, or `manual_override`
- `evidence`

Rules:

- Any gate forces effective usability to `unusable`.
- Gates remain visible even when manual review changes another score.

## JudgeConfiguration

Fields:

- `judge_provider`
- `judge_model`
- `judge_prompt_version`
- `rubric_version`
- `parameters`
- `calibration_report_id`
- `guardrails`

Rules:

- Comparable outputs in one scoring run use the same judge setup.
- Live judge calls use spec 011 guardrails and confirmation.

## JudgeInputControls

Fields:

- `candidate_identity_hidden`
- `candidate_identity_inclusion_reason`
- `pairwise_order`
- `order_swap_group_id`

Rules:

- Candidate identity should be hidden for ordinary scoring.
- If identity is included, a diagnostic reason is recorded.

## JudgeResult

Fields:

- `judge_output_schema_version`
- `scores`
- `usability`
- `hard_failure_findings`
- `quality_errors`
- `rationales`
- `raw_response_metadata`

Rules:

- Scores must match the active rubric scale.
- Usability must be `usable`, `minor_edit`, `major_edit`, or `unusable`.
- Categories must come from the active taxonomy version.

## EffectiveScore

Fields:

- `accuracy`
- `quality`
- `style_history_fit`
- `aggregate`
- `usability`
- `hard_failed`
- `derived_from`

Rules:

- Aggregates are secondary review aids.
- Hard failure gates take precedence over aggregate score.

## JudgeCalibrationReport

Fields:

- `calibration_report_id`
- `created_at`
- `judge_configuration`
- `calibration_case_count`
- `expected_label_version`
- `agreement_by_dimension`
- `parse_failure_count`
- `hard_failure_agreement`
- `usability_agreement`
- `bias_controls`
- `notes`

Rules:

- Calibration preserves expected labels and judge outputs separately.
- Calibration is useful evidence but not required for every maintainer scoring
  run.
