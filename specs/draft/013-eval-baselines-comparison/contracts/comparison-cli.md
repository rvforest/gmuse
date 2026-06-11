# Contract: baseline promotion and comparison CLI

This contract defines the maintainer-facing command behavior for promoting eval
baselines and comparing candidate scored results against promoted baselines.

Command names are design targets and may be adjusted during implementation if
the eval command namespace changes, but the behavior and inputs remain required.

## Command: `gmuse eval baseline promote`

Promotes a completed scored eval run into a versioned baseline artifact.

### Required options

```text
--result-artifact PATH
--scored-artifact PATH
--baseline-id TEXT
--label TEXT
--output PATH
```

### Optional options

```text
--description TEXT
--retain-debug-fields
--dry-run
```

### Behavior

- Validates that the result artifact satisfies required spec 010 metadata.
- Validates that the scored artifact satisfies required spec 012 metadata.
- Validates that the scored artifact corresponds to the result artifact.
- Rejects unscored, incomplete, or schema-incompatible sources.
- Writes a baseline artifact only when promotion validation succeeds.
- Strips debug-only fields by default.
- Retains debug fields only when `--retain-debug-fields` is explicit.
- `--dry-run` validates and reports what would be promoted without writing the
  baseline artifact.

### Success output

Success output must include:

```text
baseline_id
output_path
case_count
suite_id
suite_version
model
schema_version
debug_fields_retained
```

### Failure output

Failure output must:

- explain why promotion was rejected;
- name missing or incompatible metadata where possible;
- avoid writing a partial baseline artifact;
- avoid suggesting fixture importing or public recommendation workflows.

## Command: `gmuse eval baseline compare`

Compares a promoted baseline against candidate result and scored artifacts.

### Required options

```text
--baseline PATH
--candidate-result PATH
--candidate-scored PATH
```

### Optional options

```text
--mode regression|benchmark
--output PATH
--include-messages
--fail-on-new-hard-failure
```

### Defaults

- `--mode regression`
- `--include-messages` disabled if reports can use output references instead
- `--fail-on-new-hard-failure` disabled unless maintainers opt in for automation

### Regression mode behavior

- Treats same-model comparison as the default.
- Emits high-severity warnings when model metadata differs.
- Emits high-severity warnings when generation config differs.
- Emits structured warnings for suite, case, prompt, judge, scoring, or schema
  mismatches.
- Labels evidence as clean regression, degraded regression, or invalid depending
  on warning severity.

### Benchmark mode behavior

- Must be explicit.
- Allows model metadata differences.
- Still warns on suite, case, config, prompt, judge, scoring, or schema
  mismatches.
- Labels evidence as benchmark evidence.
- Must not produce public recommendations, provider preference claims, or
  hardcoded accept/reject decisions.

### Comparison output

The command must produce a structured report containing:

```text
schema_version
created_at
mode
evidence_classification
baseline
candidate
warnings
summary
pairwise_cases
baseline_only_cases
candidate_only_cases
```

Each pairwise case record must include:

```text
case_id
baseline_case_revision
candidate_case_revision
baseline_fixture_revision
candidate_fixture_revision
baseline_output_ref
candidate_output_ref
score_deltas
hard_failure_delta
prompt_hash_changed
prompt_size_delta_bytes
estimated_prompt_token_delta
first_shot_success_delta
error_category_delta
operational_error_delta
warnings
```

### Hard-failure flags

The report must flag:

- new privacy leaks;
- new severe injection obedience;
- new production validation failures;
- removed hard failures;
- unchanged hard failures.

New hard failures must be visible regardless of aggregate score movement.

### Compatibility warning categories

Comparison must warn about differences in:

- baseline artifact schema version;
- result artifact schema version;
- scored artifact schema version;
- suite ID or version;
- suite membership;
- case IDs;
- case revisions;
- fixture revisions;
- model provider, requested model, resolved model, model revision, or endpoint
  profile;
- generation config;
- prompt version;
- judge model;
- judge prompt version;
- judge calibration report or expected label version;
- rubric version;
- scoring schema version;
- judge parameters.

Each warning must include:

```text
code
severity
scope
affected_cases
baseline_value
candidate_value
message
evidence_classification
```

### Exit behavior

- Report generation success should exit successfully even when warnings are
  present, unless a blocking parse/schema error prevents report creation.
- `--fail-on-new-hard-failure` may make the command exit non-zero when new hard
  failures are present after writing the report.
- Compatibility warnings alone should not delete or suppress the report.
- The command must never make live candidate or judge calls.

## Non-goals

- Fixture importing.
- Live eval execution.
- Live judge scoring.
- Public recommendation page generation.
- Provider preference claims.
- Automatic accept/reject decisions beyond hard-failure flags and optional exit
  status for automation.
