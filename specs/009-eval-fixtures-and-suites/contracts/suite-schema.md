# Contract: Suite and Composition Schema

**Feature**: 009-eval-fixtures-and-suites
**Schema version**: 2.0

## Case contract

Cases bind fixture reconstruction, case assessment guidance, and generation
context.

```toml
schema_version = "2.0"
id = "docs-history"
revision = 1
fixture_id = "synthetic-docs-history"
assessment_guidance_id = "docs-history"
formats = ["freeform", "conventional"]
history_depth = 1
include_branch = true
user_hint = "Prefer the documentation purpose."
max_chars = 72
tags = ["docs", "smoke"]
```

## Suite contract

Suites select case IDs and optionally state the specific scenarios they need.

```toml
schema_version = "2.0"
id = "core"
version = "2.0"
suite_kind = "core"
case_ids = ["docs-history", "injection-comment"]

[[composition_goals]]
selector = "case.format"
value = "conventional"
minimum_cases = 2
severity = "advisory"
```

## Composition-goal rules

- Goals name one supported selector, one allowed value, and a positive minimum
  number of cases.
- A goal counts matching cases, not metadata values. A case is counted once per
  goal.
- Required shortfalls fail validation. Advisory shortfalls warn and become
  failures when strict composition is requested.
- Goals for the same selector and value may not conflict or repeat.
- `not-used`, `none`, and `not-applicable` are not goal values. Use the
  explicit enabled/disabled or ordinary/injection value instead.
- Smoke is a subset of core and uses only minimal required scenario goals.
- Core composition goals are expanded as curation grows; they do not imply
  model-quality thresholds.
