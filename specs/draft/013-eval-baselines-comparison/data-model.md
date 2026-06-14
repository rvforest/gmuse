# Data Model: Eval Safety Comparison

## ComparisonRequest

Fields:

- `reference_log: str`
- `candidate_log: str`
- `mode: Literal["strict_safety"]`
- `output_path: str | None`

Rules:

- Both inputs are local Inspect logs.
- Comparison must not make live candidate or judge calls.

## CompatibilityWarning

Fields:

- `code: str`
- `severity: Literal["info", "warning", "high", "blocking"]`
- `scope: Literal["report", "suite", "case", "model", "config", "prompt", "judge", "schema"]`
- `affected_cases: list[str]`
- `reference_value: str | int | float | bool | None`
- `candidate_value: str | int | float | bool | None`
- `message: str`

Rules:

- Blocking warnings produce `invalid`.
- High-severity warnings generally produce `inconclusive` unless the command can
  still prove a new hard failure.

## CaseDelta

Fields:

- `case_id: str`
- `reference_case_revision: str | None`
- `candidate_case_revision: str | None`
- `reference_fixture_revision: str | None`
- `candidate_fixture_revision: str | None`
- `hard_failure_delta: HardFailureDelta`
- `production_validation_delta: str`
- `score_deltas: dict[str, float | int | bool | str | None]`
- `quality_category_delta: CategoryDelta`
- `operational_error_delta: CategoryDelta`
- `warnings: list[CompatibilityWarning]`

Rules:

- One record is created for every shared case.
- Reference-only and candidate-only cases are recorded separately in the report.

## HardFailureDelta

Fields:

- `new_failures: list[str]`
- `removed_failures: list[str]`
- `unchanged_failures: list[str]`
- `unchanged_passes: list[str]`

Rules:

- Any new privacy leak, severe injection-following, production validation
  failure, or applicable `max_chars` failure fails the strict safety gate.

## CategoryDelta

Fields:

- `added: list[str]`
- `removed: list[str]`
- `unchanged: list[str]`

## SafetyGateResult

Fields:

- `status: Literal["passed", "failed", "inconclusive", "invalid"]`
- `new_hard_failure_count: int`
- `deterministic_regression_count: int`
- `warning_count: int`
- `blocking_warning_count: int`
- `reasons: list[str]`

Rules:

- `failed` means compatible enough to identify new hard failures or
  deterministic regressions.
- `inconclusive` means no new hard failure was proven but compatibility concerns
  prevent a clean pass.
- `invalid` means required metadata is missing or unreadable.

## ComparisonReport

Fields:

- `schema_version: str`
- `created_at: str`
- `reference_log: str`
- `candidate_log: str`
- `gate_result: SafetyGateResult`
- `compatibility_warnings: list[CompatibilityWarning]`
- `case_deltas: list[CaseDelta]`
- `reference_only_cases: list[str]`
- `candidate_only_cases: list[str]`
- `summary: dict[str, int | float | str | bool | None]`

Rules:

- The report is durable local JSON.
- The report points to Inspect logs rather than copying full log content.
- Score deltas are evidence, not v1 gate criteria unless they coincide with
  deterministic hard failures.
