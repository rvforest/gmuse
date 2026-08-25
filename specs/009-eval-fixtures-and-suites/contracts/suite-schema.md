# Contract: Suite And Case Schema

**Feature**: 009-eval-fixtures-and-suites
**Date**: 2026-06-11

## Case contract

An eval case binds one fixture to one rubric and declares which generation
formats and context options later runner specs may use.

### Required case fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Stable case identifier |
| `revision` | yes | Positive integer case revision |
| `fixture_id` | yes | Referenced fixture |
| `rubric_id` | yes | Referenced rubric |
| `formats` | yes | One or more of `freeform`, `conventional`, `gitmoji` |
| `history_depth` | yes | Integer or null for default |
| `include_branch` | yes | Whether branch context should be enabled |
| `user_hint` | yes | Hint string or null |
| `max_chars` | yes | Character limit or null |
| `tags` | yes | Classification and safety tags |

## Suite contract

Suites are named, versioned sets of case IDs.

### Required suite fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Suite identifier |
| `version` | yes | Suite version |
| `suite_kind` | yes | `smoke`, `core`, `safety`, or `custom` |
| `case_ids` | yes | Ordered case IDs |
| `coverage_policy` | yes | Required and advisory coverage rules |

## Suite rules

- `smoke` must be a subset of `core`.
- `smoke` must not be used for user-facing model recommendations.
- `safety` may include safety-tagged core cases and additional safety cases.
- Missing case IDs fail validation.
- Duplicate case IDs fail validation.
- Advisory balance gaps warn by default.
- Required coverage policy violations fail validation.

## Coverage dimensions

Validation reports must include coverage for:

- ecosystem
- source repo
- origin kind
- source license evidence status
- change type
- format
- safety tag
- injection sub-tag
- history usage
- branch usage
- hint usage
- `max_chars` usage
