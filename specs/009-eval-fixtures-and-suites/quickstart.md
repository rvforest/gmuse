# Quickstart: Validate Understandable Eval Assets

This guide checks the maintainer-only fixture foundation. It makes no provider,
candidate-model, judge-model, or network calls.

## Prerequisites

- Python 3.10+
- Git
- `uv sync`

## 1. Validate the smoke suite

```bash
uv run python -m tools.evals.gmuse_evals validate --suite smoke
```

Expected outcome:

- versioned fixture, scoring-profile, assessment-guidance, case, and suite
  assets are valid;
- temporary repositories reconstruct and stage the evaluated changes;
- staged-change paths and digests match;
- a `Suite composition` report explains what the two cases exercise;
- no credentials are needed.

Read the report as a description of the suite, not of model performance:

```text
Suite composition

Changes
- Documentation: 1 case
- Tests: 1 case

Context variations
- Commit history enabled: 1 case
- Commit history disabled: 1 case

Safety scenarios
- Ordinary change: 1 case
- Direct instruction in code comment: 1 case
```

A count may appear in more than one group because one case has several
attributes. For example, a case that supports freeform and conventional formats
contributes one case to each format entry. This is not a contradiction.

## 2. Read one assessment as a maintainer

Follow these documents:

1. [commit-message-v1 profile](contracts/scoring-profile-schema.md)
2. [docs-history guidance](../../evals/rubrics/docs-history.toml) after migration
3. [docs-history case](../../evals/cases/docs-history.toml) after migration
4. [docs-history fixture](../../evals/fixtures/synthetic-docs-history.toml)

The profile defines the common meaning of ratings 1–4 and usability labels. The
case guidance explains which observable evidence matters for this particular
change. Its two annotated examples demonstrate one usable output and one
important failure; they are calibration examples, not strings a generated
message must duplicate.

## 3. Check composition-goal behavior safely

Copy the assets to a temporary directory and make a goal impossible:

```bash
review_dir="$(mktemp -d)"
cp -R evals "$review_dir/evals"
$EDITOR "$review_dir/evals/suites/core.toml"

uv run python -m tools.evals.gmuse_evals validate \
  --suite core \
  --evals-dir "$review_dir/evals"
```

For example, make an advisory goal require two `gitmoji` cases when only one
exists. Validation succeeds with a warning that names the selector, value,
observed case count, and required count.

Promote that warning deliberately:

```bash
uv run python -m tools.evals.gmuse_evals validate \
  --suite core \
  --evals-dir "$review_dir/evals" \
  --strict-composition
```

The command exits non-zero. This demonstrates a suite-content policy, not a
model-quality failure.

## 4. Check an assessment-guidance failure safely

In a fresh copied asset directory, change a criterion's `dimension` to an
unknown value or make an example reference a nonexistent failure condition.
Validation must exit non-zero and identify the guidance asset, field, and
invalid reference.

## 5. Check a staged-change failure safely

In a fresh copied asset directory, change a fixture patch without changing its
expected digest. Validation must exit non-zero and identify the fixture with
the expected and observed staged-change digests.

## Boundaries

This feature validates source assets and communicates their intended scenario
composition. It does not generate commit messages, judge their semantics,
calculate ratings, determine semantic instruction obedience, or recommend
models. Those behaviors belong to later runner and scoring work.
