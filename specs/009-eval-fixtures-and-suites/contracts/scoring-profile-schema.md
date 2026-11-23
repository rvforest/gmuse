# Contract: Scoring Profile Schema

**Feature**: 009-eval-fixtures-and-suites
**Schema version**: 1.0

A scoring profile is a shared, reviewable explanation of future subjective
assessment. It does not execute a scorer or define a weighted aggregate.

## Required shape

```toml
schema_version = "1.0"
id = "commit-message-v1"
revision = 1

[[dimensions]]
id = "accuracy"
label = "Accuracy"
description = "How faithfully the message describes the staged change."

[dimensions.anchors]
"1" = "Mostly incorrect or makes a major unsupported claim."
"2" = "Materially incomplete, misleading, or poorly prioritized."
"3" = "Accurate with a minor omission or imprecision."
"4" = "Accurate, specific, and centered on the primary change."

[usability_labels]
usable = "Ready to use without editing."
minor_edit = "Accurate but needs a small edit."
major_edit = "Needs substantial editing before use."
unusable = "Cannot be used as a commit message."

[[usability_examples]]
message = "docs(evals): explain offline validation"
usability = "usable"
rationale = "Specific, accurate, and concise."
```

## Rules

- A profile has a stable ID and positive integer revision.
- It declares one or more dimensions in display order.
- Every dimension has exactly the four integer anchors 1, 2, 3, and 4.
- Anchor text is non-empty and distinguishes adjacent levels.
- It declares exactly the four canonical usability labels:
  `usable`, `minor_edit`, `major_edit`, and `unusable`.
- It includes at least one annotated usability illustration for each intermediate
  label, `minor_edit` and `major_edit`.
- It does not define weights, thresholds for an aggregate, or an aggregate
  field.
