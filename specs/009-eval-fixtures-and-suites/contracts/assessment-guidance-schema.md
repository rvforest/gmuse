# Contract: Case Assessment Guidance Schema

**Feature**: 009-eval-fixtures-and-suites
**Schema version**: 2.0

Case assessment guidance applies a shared scoring profile to one evaluation
case. It is stored under `evals/rubrics/` for continuity, but the canonical
meaning is assessment guidance.

## Required shape

```toml
schema_version = "2.0"
id = "docs-history"
revision = 1
scoring_profile_id = "commit-message-v1"

[[criteria]]
id = "documentation-purpose"
dimension = "accuracy"
importance = "major"
description = "Identifies that the change documents offline validation."

[[failure_conditions]]
id = "claims-runtime-feature"
error_category = "hallucination"
severity = "major"
description = "Claims a runtime feature or provider integration absent from the change."

[[deterministic_gates]]
id = "message-valid"
gate = "production_validation"
evidence = "Use the production validation result."

[[examples]]
message = "docs(evals): explain offline validation"
ratings = { accuracy = 4, message_quality = 4, style_context_fit = 3 }
usability = "usable"
expected_gate_ids = []
expected_failure_ids = []
rationale = "Names the documentation purpose without unsupported claims."
```

## Rules

- Guidance references one existing scoring profile.
- Each criterion references a profile dimension and has an independently
  assessable description and `major` or `minor` importance.
- Each failure condition has an error category, observable description, and
  `major` or `minor` severity.
- Deterministic gates are restricted to objective gates:
  `production_validation`, `max_chars`, `fake_secret_leak`, or
  `literal_injection_marker`. The evidence must identify the observable
  source. Semantic instruction obedience is invalid here.
- Every checked-in guidance document has exactly two examples: one `usable`
  example and one example with an important failure or failed deterministic
  gate.
- Example ratings use only profile dimensions and anchors 1 through 4; omitted
  dimensions are not applicable.
- Examples include a rationale and reference only local criterion, failure, and
  gate IDs.
- Example messages illustrate behavior and are not exact-match targets.
