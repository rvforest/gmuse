# CLI Contract: Eval Suite Validation

**Feature**: 009-eval-fixtures-and-suites
**Date**: 2026-06-11

## Command purpose

The maintainer validation command checks fixture, rubric, case, and suite data
without making model, judge, network, or importer calls.

## Command signature

```text
gmuse eval validate [OPTIONS]
```

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--suite` | str | `smoke` | Suite identifier to validate |
| `--fixtures-dir` | path | project default | Fixture/case/rubric root |
| `--json` | bool | false | Emit machine-readable validation report |
| `--strict-balance` | bool | false | Treat advisory balance warnings as failures |
| `--help` | bool | false | Show help and exit |

## Behavior contract

1. Load the requested suite and all referenced cases, fixtures, and rubrics.
2. Validate schemas and references.
3. Validate provenance requirements based on fixture origin.
4. Reconstruct each fixture in a temporary git repository.
5. Apply and stage the evaluated change.
6. Extract the staged diff through git.
7. Verify staged diff digest and changed paths.
8. Validate rubric conventional type compatibility.
9. Report coverage dimensions.
10. Exit non-zero on validation errors.

## Success output

```text
Validated suite: smoke
Status: passed
Cases: 3
Fixtures: 3
Warnings: 0
```

## Failure output

```text
Validated suite: smoke
Status: failed

Errors:
- fixture real-docs-update: missing provenance.source_license
- fixture real-docs-update: missing provenance.redistribution_review
- fixture injection-comment: staged diff digest mismatch
```

## Non-goals

- The command must not call candidate models.
- The command must not call judge models.
- The command must not clone source repositories.
- The command must not promote baselines.
