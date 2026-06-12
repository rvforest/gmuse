# Tool Contract: Eval Suite Validation

**Feature**: 009-eval-fixtures-and-suites
**Date**: 2026-06-11

## Command purpose

The maintainer validation command checks fixture, rubric, case, and suite TOML
data without making model, judge, network, or importer calls. It is a repository
tool, not a public `gmuse` CLI command.

## Command signature

```text
python -m tools.evals.gmuse_evals validate [OPTIONS]
```

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--suite` | str | `smoke` | Suite identifier to validate |
| `--evals-dir` | path | `evals` | Fixture/rubric/case/suite root |
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

The first implementation emits human-readable output only. It may use a
structured internal validation report, but `--json` is deferred until automation
needs a stable machine-readable contract.

## Success output

```text
Validated suite: smoke
Status: passed
Cases: 2
Fixtures: 2
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
- The command must not be exposed through the public `gmuse` console script in
  the first foundation implementation.
