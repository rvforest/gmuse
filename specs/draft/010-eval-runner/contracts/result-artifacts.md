# Contract: result artifacts

**Feature**: 010-eval-runner
**Date**: 2026-06-11

The runner writes durable artifacts for maintainer inspection and later eval phases. Artifacts are local files, versioned, and intentionally limited to production generation outcomes plus deterministic validation.

## Artifact layout

```text
<output-dir>/
├── run-plan.json
├── outputs.jsonl
└── summary.json
```

`outputs.jsonl` is omitted or empty for planning mode. Planning mode may still write `run-plan.json` and `summary.json` if they are clearly marked as `mode: "plan"`.

## `run-plan.json`

### Required fields

```json
{
  "schema_version": "eval-run-plan.v1",
  "run_id": "20260611T120000Z-smoke",
  "mode": "plan",
  "suite_ids": ["smoke"],
  "models": ["gpt-4.1-mini"],
  "planned_attempts": 3,
  "attempts": [
    {
      "attempt_id": "0001",
      "suite_id": "smoke",
      "case_id": "smoke-docs-001",
      "fixture_id": "fixture-docs-001",
      "fixture_revision": "sha256:...",
      "model": "gpt-4.1-mini",
      "generation_config": {
        "format": "conventional",
        "history_depth": 5,
        "include_branch": false,
        "hint": null,
        "repository_instructions": null,
        "max_chars": 72,
        "temperature": 0.2,
        "max_tokens": 120
      }
    }
  ],
  "output_records_path": "outputs.jsonl",
  "summary_path": "summary.json"
}
```

### Rules

- `schema_version` must change when required fields or semantics change.
- `attempts` must include enough information to understand what execution would do without reading output records.
- Planning mode must not include generated messages.

## `outputs.jsonl`

Each line is one JSON object for one attempted case/model/config combination.

### Required fields

```json
{
  "schema_version": "eval-output-record.v1",
  "run_id": "20260611T120000Z-smoke",
  "attempt_id": "0001",
  "suite_id": "smoke",
  "case_id": "smoke-docs-001",
  "fixture_id": "fixture-docs-001",
  "fixture_revision": "sha256:...",
  "model": "gpt-4.1-mini",
  "generation_config": {
    "format": "conventional",
    "history_depth": 5,
    "include_branch": false,
    "hint": null,
    "repository_instructions": null,
    "max_chars": 72,
    "temperature": 0.2,
    "max_tokens": 120
  },
  "context_metadata": {
    "prompt_hash": "sha256:...",
    "prompt_size_bytes": 4096,
    "estimated_input_tokens": 950,
    "estimated_output_tokens": 12,
    "diff_truncated": false,
    "history_commit_count": 5,
    "branch_context_included": false,
    "repository_instructions_included": false,
    "max_chars": 72
  },
  "generated_message": "docs: clarify configuration defaults",
  "validation": {
    "status": "passed",
    "error_categories": [],
    "details": null
  },
  "operational_error": null,
  "timing": {
    "started_at": "2026-06-11T12:00:00Z",
    "completed_at": "2026-06-11T12:00:03Z",
    "duration_ms": 3120
  }
}
```

### Validation-failure record

```json
{
  "schema_version": "eval-output-record.v1",
  "run_id": "20260611T120000Z-smoke",
  "attempt_id": "0002",
  "suite_id": "smoke",
  "case_id": "smoke-fix-001",
  "fixture_id": "fixture-fix-001",
  "fixture_revision": "sha256:...",
  "model": "gpt-4.1-mini",
  "generation_config": {
    "format": "conventional",
    "history_depth": 5,
    "include_branch": true,
    "hint": null,
    "repository_instructions": null,
    "max_chars": 50,
    "temperature": 0.2,
    "max_tokens": 120
  },
  "context_metadata": {
    "prompt_hash": "sha256:...",
    "prompt_size_bytes": 6120,
    "estimated_input_tokens": 1400,
    "estimated_output_tokens": 20,
    "diff_truncated": false,
    "history_commit_count": 5,
    "branch_context_included": true,
    "repository_instructions_included": false,
    "max_chars": 50
  },
  "generated_message": "fix: update parser to reject invalid nested configuration values",
  "validation": {
    "status": "failed",
    "error_categories": ["max_chars"],
    "details": "Generated message exceeded configured max_chars."
  },
  "operational_error": null,
  "timing": {
    "started_at": "2026-06-11T12:00:05Z",
    "completed_at": "2026-06-11T12:00:08Z",
    "duration_ms": 3010
  }
}
```

### Operational-error record

```json
{
  "schema_version": "eval-output-record.v1",
  "run_id": "20260611T120000Z-smoke",
  "attempt_id": "0003",
  "suite_id": "smoke",
  "case_id": "smoke-safety-001",
  "fixture_id": "fixture-safety-001",
  "fixture_revision": "sha256:...",
  "model": "gpt-4.1-mini",
  "generation_config": {
    "format": "freeform",
    "history_depth": 0,
    "include_branch": false,
    "hint": null,
    "repository_instructions": null,
    "max_chars": null,
    "temperature": 0.2,
    "max_tokens": 120
  },
  "context_metadata": {
    "prompt_hash": "sha256:...",
    "prompt_size_bytes": 3800,
    "estimated_input_tokens": 850,
    "estimated_output_tokens": null,
    "diff_truncated": false,
    "history_commit_count": 0,
    "branch_context_included": false,
    "repository_instructions_included": false,
    "max_chars": null
  },
  "generated_message": null,
  "validation": {
    "status": "not_run",
    "error_categories": [],
    "details": null
  },
  "operational_error": {
    "category": "timeout",
    "message": "Provider request timed out.",
    "provider_status": null,
    "retryable": true
  },
  "timing": {
    "started_at": "2026-06-11T12:00:10Z",
    "completed_at": "2026-06-11T12:00:40Z",
    "duration_ms": 30000
  }
}
```

### Rules

- There must be exactly one output record for every attempted execution-mode attempt.
- `generated_message` must be preserved for validation failures.
- `operational_error` and `validation.status = "passed"` must not both be present.
- Judge scores, aggregate scores, baseline IDs, pairwise comparisons, and recommendation fields are not allowed in `eval-output-record.v1`.
- Raw prompt text is not included by default.

## `summary.json`

### Required fields

```json
{
  "schema_version": "eval-run-summary.v1",
  "run_id": "20260611T120000Z-smoke",
  "mode": "execute",
  "suite_ids": ["smoke"],
  "models": ["gpt-4.1-mini"],
  "artifact_paths": {
    "run_plan": "run-plan.json",
    "outputs": "outputs.jsonl",
    "summary": "summary.json"
  },
  "planned_attempts": 3,
  "completed_attempts": 3,
  "validation_passed": 1,
  "validation_failed": 1,
  "operational_errors": {
    "timeout": 1
  },
  "started_at": "2026-06-11T12:00:00Z",
  "completed_at": "2026-06-11T12:00:40Z"
}
```

### Rules

- `completed_attempts` counts written output records, not quality successes.
- `validation_failed` counts deterministic production validation failures only.
- `operational_errors` groups setup/provider failures by category.
- The summary must not rank models or recommend model choices.
