# Contract: Scored Artifact Schema

**Date**: 2026-06-11
**Feature**: `012-eval-judge-scoring`

This contract defines the maintainer-facing scored JSONL record and summary JSON
shape. Field names are intentionally explicit so records remain useful for later
baseline and comparison specs.

## Scored JSONL Record

Each line represents one scored or explicitly unscored runner output. The
`source` object supports both spec 010 `outputs.jsonl` records and spec 011
resumable candidate records.

```json
{
  "scoring_schema_version": 1,
  "scoring_run_id": "score-20260611-000001",
  "source": {
    "source_kind": "spec010_output",
    "runner_run_id": "run-20260611-000001",
    "attempt_id": "0001",
    "candidate_record_id": null,
    "work_item_id": null,
    "runner_schema_version": "eval-output-record.v1",
    "suite_id": "core",
    "case_id": "case-001",
    "fixture_id": "fixture-001",
    "fixture_revision": "1"
  },
  "candidate": {
    "model": "example-model",
    "generation_config": {},
    "context_metadata": {
      "prompt_hash": "sha256:..."
    },
    "generated_message": "fix parser edge case",
    "validation": {
      "status": "passed",
      "error_categories": [],
      "details": null
    },
    "operational_error": null
  },
  "judge_configuration": {
    "judge_provider": "example",
    "judge_model": "judge-model",
    "judge_prompt_version": "1",
    "rubric_version": "1",
    "parameters": {
      "temperature": 0,
      "max_tokens": 1200
    }
  },
  "deterministic_checks": [],
  "hard_failure_gates": [],
  "judge_result": null,
  "judge_operational_error": null,
  "quality_errors": [],
  "operational_errors": [],
  "self_judged": false,
  "judge_input_controls": {
    "candidate_identity_hidden": true,
    "candidate_identity_inclusion_reason": null,
    "pairwise_order": "not_applicable",
    "order_swap_group_id": null
  },
  "effective_score": {
    "accuracy": null,
    "quality": null,
    "style_history_fit": null,
    "aggregate": null,
    "usability": null,
    "hard_failed": false,
    "derived_from": "automated"
  },
  "manual_annotations": [],
  "manual_overrides": [],
  "scored_at": "2026-06-11T00:00:00Z"
}
```

## Required Record Rules

- `scoring_schema_version` must be present on every record.
- `source.source_kind` must be `spec010_output` or `spec011_candidate_record`.
- For `spec010_output`, `source.runner_run_id` and `source.attempt_id` must
  point to exactly one spec 010 `outputs.jsonl` record.
- For `spec011_candidate_record`, `source.runner_run_id`,
  `source.candidate_record_id`, and `source.work_item_id` must point to exactly
  one spec 011 `candidate-records.jsonl` record.
- `candidate.generated_message` must preserve the raw generated message when one
  exists, including invalid output.
- `candidate.operational_error` and successful candidate scoring are mutually
  exclusive.
- `judge_configuration` must be present even when a record is unscored because
  of budget, compatibility, or candidate operational state.
- `hard_failure_gates` must be visible and must not be hidden inside aggregate
  scores.
- `effective_score.hard_failed` must equal whether any hard failure gate is
  active after manual overrides.
- `manual_overrides` must not remove or rewrite `judge_result` or
  `deterministic_checks`.
- `judge_input_controls.candidate_identity_hidden` should be true for ordinary
  scoring. If false, `candidate_identity_inclusion_reason` is required.
- Pairwise ordering fields must be `not_applicable` unless pairwise judge
  scoring is explicitly enabled by a future extension.

## Deterministic Check Object

```json
{
  "check_id": "max_chars",
  "status": "fail",
  "severity": "hard_failure",
  "evidence": "Generated message length 83 exceeded max_chars 72.",
  "quality_errors": ["validation_error"]
}
```

Allowed `status` values: `pass`, `fail`, `not_applicable`.

Allowed `severity` values: `info`, `warning`, `hard_failure`.

## Judge Operational Error Object

```json
{
  "category": "timeout",
  "message": "Judge call exceeded configured timeout.",
  "retryable": true,
  "occurred_at": "2026-06-11T00:00:00Z"
}
```

Allowed `category` values:

- `auth_error`
- `rate_limit`
- `timeout`
- `network_error`
- `context_length`
- `empty_response`
- `judge_parse_error`
- `unknown_error`

## Manual Annotation Object

```json
{
  "annotation_id": "ann-001",
  "reviewer": "maintainer",
  "created_at": "2026-06-11T00:00:00Z",
  "note": "Judge was harsh but directionally correct."
}
```

## Manual Override Object

```json
{
  "override_id": "ovr-001",
  "reviewer": "maintainer",
  "created_at": "2026-06-11T00:00:00Z",
  "target_fields": ["effective_score.quality"],
  "replacement_values": {
    "effective_score.quality": 4
  },
  "rationale": "Judge penalized an allowed conventional type."
}
```

## Summary JSON

```json
{
  "scoring_schema_version": 1,
  "scoring_run_id": "score-20260611-000001",
  "source_runner_run_id": "run-20260611-000001",
  "created_at": "2026-06-11T00:00:00Z",
  "completed_at": "2026-06-11T00:10:00Z",
  "judge_configuration": {},
  "calibration_report_ref": null,
  "budget_accounting": {
    "planned_judge_calls": 0,
    "budgeted_judge_calls": 0,
    "actual_judge_calls": 0,
    "skipped_completed": 0,
    "remaining_budget": 0
  },
  "counts": {
    "records_total": 0,
    "records_scored": 0,
    "records_unscored": 0,
    "hard_failed": 0,
    "self_judged": 0,
    "judge_operational_errors": 0
  },
  "schema_versions": {
    "runner_schema_version": "eval-output-record.v1",
    "live_run_artifact_schema_version": null,
    "scoring_schema_version": 1,
    "judge_output_schema_version": 1,
    "quality_taxonomy_version": 1,
    "operational_taxonomy_version": 1,
    "rubric_version": "1",
    "judge_prompt_version": "1"
  }
}
```

Summary counts must match the scored JSONL records for the same
`scoring_run_id`.

## Calibration Report JSON

```json
{
  "calibration_schema_version": 1,
  "calibration_report_id": "judge-cal-20260611-000001",
  "created_at": "2026-06-11T00:00:00Z",
  "judge_configuration": {},
  "calibration_case_count": 12,
  "expected_label_version": "judge-calibration-labels.v1",
  "agreement_by_dimension": {
    "accuracy": 0.83,
    "quality": 0.75,
    "usability": 0.92
  },
  "parse_failure_count": 0,
  "hard_failure_agreement": 1.0,
  "usability_agreement": 0.92,
  "bias_controls": {
    "candidate_identity_hidden": true,
    "candidate_identity_inclusion_reason": null,
    "pairwise_order": "not_applicable",
    "order_swap_group_id": null
  },
  "notes": null
}
```

Calibration reports compare judge outputs with manually annotated labels. They
do not replace per-output scoring records and must not be treated as proof that
the judge is correct for all future cases.
