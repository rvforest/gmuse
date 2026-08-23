# Contract: Fixture And Rubric Schema

**Feature**: 009-eval-fixtures-and-suites
**Date**: 2026-06-11

## Fixture document contract

Fixture documents must be versioned and reviewable. A fixture represents the
data needed to reconstruct a temporary git repository and stage one evaluated
change.

All fixture, rubric, case, and suite documents must declare schema version
`1.0`; future or unknown schema versions are rejected. Rubric, case, and suite
documents may omit the field and receive the current `1.0` default.

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
- source evidence metadata is incomplete for real fixtures
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
- repository and commit provenance URLs are not absolute HTTP(S) URLs
- `source_license_url` is neither an absolute HTTP(S) URL nor a safe
  repository-relative POSIX path
- an injection fixture does not include at least one pattern tag and one
  location tag
- injection sub-tags are present without the explicit `injection` safety tag

Injection tags are deliberately split into two non-overlapping categories. A
pattern describes the attack shape (`direct-instruction`,
`indirect-external-content`, `obfuscated-encoded`, or `deleted-instruction`,
plus their supported short aliases); a location describes where the content is
found (`code-comment`, `markdown`, `docs`, `string-literal`, `test-fixture`, or
`config-example`).

License expressions are checked against the complete SPDX catalog supplied by
`license-expression`; `LicenseRef-*` expressions remain supported. A
`source_license_url` may still use the documented repository-path form. Empty,
whitespace-only, absolute filesystem, parent-traversal, and non-HTTP(S) URL
values are rejected.

Validation does not certify that a fixture may be redistributed; it only enforces
that source license evidence and maintainer review status are recorded.
