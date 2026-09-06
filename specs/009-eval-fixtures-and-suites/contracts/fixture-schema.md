# Contract: Fixture Schema

**Feature**: 009-eval-fixtures-and-suites
**Schema version**: 1.0

Fixtures are versioned, offline evidence for reconstructing a repository and
staging one evaluated change.

## Required top-level fields

| Field | Description |
|---|---|
| `id`, `revision`, `schema_version` | Stable fixture identity |
| `origin`, `provenance` | Source and attribution record |
| `ecosystem`, `change_type` | Composition-relevant classification |
| `safety_tags`, `injection_tags` | Safety scenario classification |
| `base_files`, `patch` | Offline repository reconstruction data |
| `expected_staged_diff_sha256`, `expected_files_changed` | Canonical staged-change evidence |
| `history`, `branch_name`, `repository_instructions` | Optional case context evidence |
| `selection_rationale` | Maintainer rationale |

Real fixtures require source repository/commit evidence, a full commit SHA,
license evidence, redistribution review, original commit message, and import
time. Adapted fixtures add adaptation notes. Synthetic fixtures require
synthetic notes and cannot pretend to have a source commit.

Injection fixtures require an explicit injection safety tag plus at least one
pattern and one location tag. Secret-like test values must be explicitly fake
or nonfunctional.

Validation reconstructs a temporary repository, applies and stages the complete
patch, verifies original changed paths, and compares the canonical staged-change
digest. It validates metadata; it does not certify redistribution permission.
