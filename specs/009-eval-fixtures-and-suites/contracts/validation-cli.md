# Tool Contract: Eval Suite Validation

**Feature**: 009-eval-fixtures-and-suites
**Schema version**: 1.0

## Command

```text
python -m tools.evals.gmuse_evals validate [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--suite` | `smoke` | Suite identifier to validate |
| `--evals-dir` | `evals` | Root containing maintainer assets |
| `--strict-composition` | false | Promote advisory composition-goal shortfalls to failures |

The command remains maintainer-only and makes no model, judge, or network calls.

## Behavior

1. Discover asset IDs deterministically and validate the selected suite graph.
2. Validate schema 1.0, references, provenance, fixture reconstruction, staged
   change evidence, scoring-profile references, rubrics, and
   composition goals.
3. Build composition from successfully resolved cases.
4. Render status, aggregated errors and warnings, counts, and grouped suite
   composition.
5. Exit non-zero for validation errors or strict-composition promotion.

## Success output

```text
Validated suite: smoke
Status: passed
Cases: 2
Fixtures: 2
Warnings: 0

Suite composition

Changes
- Documentation: 1 case
- Tests: 1 case

Output formats
- Freeform: 2 cases
- Conventional: 2 cases
- Gitmoji: 1 case

Context variations
- Commit history enabled: 1 case
- Commit history disabled: 1 case
- Branch context enabled: 1 case
- Branch context disabled: 1 case

Safety scenarios
- Ordinary change: 1 case
- Direct instruction in code comment: 1 case

Fixture sources
- Synthetic: 2 cases
```

Composition headings or empty groups may be omitted when no resolved cases
contribute to them. A failed run retains errors and any truthful composition; it
never presents composition as a passing score.

## Failure output

```text
Validated suite: core
Status: failed

Errors:
- suite core: composition goal case.format=gitmoji has 1 case; requires 2
- guidance docs-history: example bad-runtime-claim references unknown failure condition
```
