# Contract: Fixture And Rubric Schema

**Feature**: 009-eval-fixtures-and-suites
**Date**: 2026-06-11

## Fixture document contract

Fixture documents must be versioned and reviewable. A fixture represents the
data needed to reconstruct a temporary git repository and stage one evaluated
change.

### Required top-level fields

| Field | Required | Description |
|-------|----------|-------------|
| `schema_version` | yes | Fixture schema version |
| `id` | yes | Stable fixture identifier |
| `revision` | yes | Positive integer revision |
| `origin` | yes | `real`, `adapted`, or `synthetic` |
| `provenance` | yes | Source and attribution metadata |
| `ecosystem` | yes | Primary ecosystem represented |
| `change_type` | yes | Maintainer change category |
| `safety_tags` | yes | Empty list or safety tags |
| `injection_tags` | yes | Empty list or injection pattern tags |
| `base_files` | yes | Minimal pre-change files |
| `patch` | yes | Patch applied to create staged change |
| `expected_staged_diff_sha256` | yes | Digest after reconstruction |
| `expected_files_changed` | yes | Expected changed paths |
| `history` | yes | Recent commit subjects, possibly empty |
| `branch_name` | yes | Branch name or null |
| `repository_instructions` | yes | `.gmuse` content or null |
| `selection_rationale` | yes | Maintainer rationale |

### Provenance requirements

Real fixtures require:

- `source_repository_url`
- `source_owner_repo`
- full `source_commit_sha`
- `source_commit_url`
- `source_license`
- `source_license_expression` or `source_license_url`
- `redistribution_review`
- full `original_commit_message`
- `imported_at`

Adapted fixtures require:

- all real fixture metadata when derived from a real source
- non-empty `adaptation_notes`

Synthetic fixtures require:

- non-empty `synthetic_notes`
- no required external source repository metadata

## Rubric document contract

Rubrics define acceptable and unacceptable message content. They must not require
an exact match to the original source commit message.

### Required rubric fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Stable rubric identifier |
| `version` | yes | Rubric version |
| `required_concepts` | yes | Concepts a good message should include |
| `forbidden_concepts` | yes | Unsupported claims or details |
| `allowed_conventional_types` | yes | Supported conventional types for conventional runs |
| `allowed_scopes` | yes | Optional accepted scopes |
| `example_good` | yes | Good example messages, possibly empty |
| `example_bad` | yes | Bad example messages, possibly empty |
| `quality_notes` | yes | Notes or null |
| `safety_notes` | yes | Required for safety cases, otherwise notes or null |

## Validation outcomes

The foundation should keep stable top-level fields explicit. Future-facing
fields may be present as `null` or empty lists, while deeper semantic checks may
be limited to fixture origins and feature paths that are supported or actively
used by checked-in suites.

Validation must fail when:

- required fields are absent
- source metadata is incomplete for real fixtures
- a real or adapted fixture has neither `source_license_expression` nor
  `source_license_url`
- `redistribution_review` is missing for a real or adapted fixture
- adapted fixtures omit adaptation notes
- synthetic fixtures are not marked synthetic
- patch application fails
- reconstructed staged diff digest differs from expected metadata
- changed paths differ from expected metadata
- allowed conventional types are incompatible with gmuse validation
- `safety_tags` includes `injection` but `injection_tags` is empty

Validation does not certify that a fixture may be redistributed; it only enforces
that source license evidence and maintainer review status are recorded.
