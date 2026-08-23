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

1. Parse the asset catalog and index stable IDs, then model-validate only the
   requested suite's transitive cases, fixtures, rubrics, and the core suite
   record needed for smoke subset checks.
2. Validate schemas and references.
3. Validate provenance requirements based on fixture origin.
4. Reconstruct each fixture in a temporary git repository.
5. Apply and stage the evaluated change.
6. Extract the staged diff through git.
7. Verify staged diff digest and changed paths.
8. Validate rubric conventional type compatibility.
9. Report coverage dimensions.
10. Exit non-zero on validation errors.

Raw TOML discovery remains global so malformed documents and duplicate IDs are
reported consistently. A parseable but schema-invalid asset that is not in the
selected suite graph is not validated until a selected suite references it.
Structural and missing-reference issues within the selected transitive graph
are aggregated into the same validation report rather than stopping at the
first broken asset.

The first implementation emits human-readable output only. It may use a
structured internal validation report, but `--json` is deferred until automation
needs a stable machine-readable contract.

The CLI must be a thin presentation layer over structured in-process helpers so
later eval tooling can reuse suite loading, validation results, and repository
reconstruction without parsing CLI output.

## Success output

```text
Validated suite: smoke
Status: passed
Cases: 2
Fixtures: 2
Warnings: 0
Coverage:
- ecosystem: python
- source_repo: synthetic
- origin: synthetic
- source_license: not-applicable
- change_type: docs, test
- format: conventional, freeform, gitmoji
- safety_tag: injection, none, safety
- injection_tag: code-comment, direct-instruction, none
- history: not-used, used
- branch: not-used, used
- hint: not-used, used
- max_chars: used
```

Coverage values are sorted within the fixed `COVERAGE_DIMENSIONS` order. The
history dimension reports `used` for a positive `history_depth` or for null
when it resolves to gmuse's current default; validation fails before Git
reconstruction if the resolved depth exceeds the fixture's declared history.
Temporary Git commands discard inherited `GIT_*` behavior, disable global and
system configuration, and use bounded subprocess timeouts before extracting the
diff through gmuse's production helper.

## Failure output

```text
Validated suite: smoke
Status: failed

Errors:
- fixture real-docs-update: missing provenance.source_license_expression or provenance.source_license_url
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
