# Contract: baseline artifact

This contract defines the promoted baseline artifact created from a completed
spec 010 result artifact and matching spec 012 scored output artifact.

## Artifact type

- **Name**: eval baseline artifact
- **Audience**: gmuse maintainers
- **Purpose**: Durable comparison reference for future eval regression and
  benchmark reports
- **Creation path**: Intentional baseline promotion only
- **Live calls**: None

## Required top-level fields

```text
schema_version
baseline_id
label
description
created_at
source_artifacts
suite
model
generation_config
judge
judge_calibration
cases
debug_fields_retained
```

## Field contract

### `schema_version`

Baseline artifact schema version.

Rules:

- Required.
- Must change when the baseline artifact shape changes incompatibly.
- Must be preserved in comparison reports.

### `baseline_id`

Maintainer-selected stable identifier.

Rules:

- Required.
- Must be unique within the maintainer's baseline store.
- Should be safe for filenames and report references.

### `label`

Human-readable baseline label.

Rules:

- Required.
- Should describe suite and intended use, such as same-model core regression.

### `description`

Optional maintainer note.

Rules:

- Optional.
- May explain why the source run was promoted.

### `created_at`

Promotion timestamp.

Rules:

- Required.
- Must use an unambiguous timestamp format.

### `source_artifacts`

References to source result and scored artifacts.

Required fields:

```text
result_artifact_uri
result_artifact_schema_version
scored_artifact_uri
scored_artifact_schema_version
run_id
scoring_run_id
created_at
```

Rules:

- The scored artifact must reference the result artifact run or otherwise prove
  it scored that run.
- Source schema versions are required for compatibility warnings.

### `suite`

Suite snapshot used by the promoted run.

Required fields:

```text
suite_id
suite_version
suite_revision
case_ids
case_revisions
fixture_revisions
```

Rules:

- `case_ids` must list all promoted cases.
- `case_revisions` and `fixture_revisions` must be keyed by case ID.
- Missing revisions must cause promotion rejection unless upstream artifacts
  explicitly mark revisions as unavailable.

### `model`

Candidate model snapshot.

Required fields:

```text
provider
requested_model
resolved_model
model_revision
endpoint_profile
self_judged
```

Rules:

- Same-model regression compatibility uses these fields.
- Unknown optional fields may be null but must be present.

### `generation_config`

Prompt-affecting and output-affecting configuration snapshot.

Required fields:

```text
format
history_depth
include_branch
branch_max_length
max_chars
temperature
max_tokens
prompt_version
runner_config_hash
```

Rules:

- Comparison must warn when these fields differ in regression mode.
- `prompt_version` is required.

### `judge`

Scoring context from spec 012.

Required fields:

```text
judge_model
judge_prompt_version
rubric_version
scoring_schema_version
judge_parameters_hash
self_judged
```

Rules:

- Differences in these fields must produce score-comparability warnings.
- `self_judged` must be visible to comparison consumers.

### `judge_calibration`

Judge calibration context from spec 012, or null when unavailable.

Required fields when present:

```text
calibration_report_id
calibration_schema_version
expected_label_version
calibration_case_count
agreement_by_dimension
parse_failure_count
candidate_identity_hidden
```

Rules:

- Calibration metadata should be preserved when present in scored artifacts.
- Absence of calibration metadata must remain visible to comparison consumers.
- Calibration metadata is evidence about judge setup, not a replacement for
  per-case scores or human review.

### `cases`

Per-case baseline records.

Each case record requires:

```text
case_id
case_revision
fixture_revision
generated_message
output_record_id
prompt_hash
prompt_size_bytes
estimated_prompt_tokens
first_shot_success
production_validation_passed
scores
usability
hard_failures
error_categories
operational_errors
judge_rationales
manual_overrides
```

Rules:

- `case_id` must be unique.
- Generated messages must be preserved unless the upstream result legitimately
  has no message because of an operational failure.
- Operational errors must remain separate from quality and compliance error
  categories.
- Manual overrides must preserve the original judge output reference or
  rationale when upstream scoring provides it.

### `scores`

Per-dimension scores.

Required fields:

```text
accuracy
quality
format_compliance
privacy
injection_resistance
style_fit
aggregate
additional_dimensions
```

Rules:

- Per-dimension scores are required when produced by spec 012.
- Null values are allowed only when the upstream scored artifact records why a
  dimension could not be scored.
- Aggregate scores are secondary and must not be the only preserved score data.

### `hard_failures`

Zero-tolerance failure flags.

Required fields:

```text
privacy_leak
severe_injection_obedience
production_validation_failure
other
```

Rules:

- Hard failures must be preserved even when score values are missing.
- Privacy, injection, and production validation failures must remain distinct.

### `debug_fields_retained`

Whether optional debug-only fields are present.

Rules:

- Required.
- Defaults to false for promotion.
- When false, transient execution/debug fields must not appear in the baseline.

## Promotion rejection conditions

Promotion must reject:

- missing scored output metadata from spec 012;
- missing result metadata from spec 010;
- mismatched result/scored artifact run identity;
- incomplete required case records;
- missing suite or case revision metadata without an explicit unavailable marker;
- missing model, generation config, prompt, judge, scoring, or schema metadata;
- partial artifacts that do not identify incomplete cases clearly.

## Explicitly excluded fields

Promoted baselines should exclude by default:

- raw debug logs;
- transient retry traces;
- local temporary paths;
- unneeded rendered prompt bodies when prompt hash and prompt size/token metadata
  are sufficient;
- provider credentials or secret-bearing environment details;
- unrelated process environment values.

## Non-goals

- Creating baselines automatically from every eval run.
- Importing fixtures.
- Producing public model recommendations.
- Re-scoring outputs during promotion.
