# Quickstart: Eval Fixtures And Suites

This quickstart validates the maintainer-only fixture foundation. It does not
make model calls and does not require provider credentials.

## Prerequisites

- Python 3.10+
- Git
- `uv sync`

## Validate The Smoke Suite

```bash
uv run python -m tools.evals.gmuse_evals validate --suite smoke
```

Expected outcome:

- fixture, rubric, case, and suite schemas are valid
- temporary repositories are reconstructed
- evaluated changes are staged
- staged diff digests match expected metadata
- coverage dimensions are reported
- no LLM provider credentials are required

The command is maintainer-only and intentionally does not register a new
`gmuse` product command. Fixture, rubric, case, and suite files are one TOML
record per file under `evals/`; validation discovers them in deterministic
order and uses the IDs inside the documents as references.

Machine-readable `--json` output is intentionally deferred for the first
foundation implementation.

## Check A Provenance Failure

Create or edit a real OSS fixture so that required attribution metadata is
missing, then run:

```bash
uv run python -m tools.evals.gmuse_evals validate --suite smoke
```

Expected outcome:

- validation exits non-zero
- output identifies the fixture and missing provenance field
- no model or judge calls are made

The validator checks provenance metadata without claiming legal approval. Real
and adapted fixtures need source license evidence and a separate
`redistribution_review` value; synthetic fixtures need `synthetic_notes`.

## Check A Digest Failure

Edit fixture patch data without updating the expected staged diff digest, then
run:

```bash
uv run python -m tools.evals.gmuse_evals validate --suite smoke
```

Expected outcome:

- validation exits non-zero
- output identifies the fixture with the digest mismatch
- the report includes expected and observed digest values

The digest is the SHA-256 of the exact `git diff --cached` text returned by
gmuse's production staged-diff helper. Do not normalize, truncate, or manually
rewrite the patch to make a mismatch disappear; update the fixture digest only
after reviewing the intentional patch change.

## Suite policy and safety checks

Validate the curated core suite and promote advisory coverage gaps when needed:

```bash
uv run python -m tools.evals.gmuse_evals validate --suite core
uv run python -m tools.evals.gmuse_evals validate --suite core --strict-balance
```

The checked-in smoke suite must remain a subset of `core`. Injection fixtures
must identify both the injection pattern and its location, such as
`direct-instruction` in a `code-comment`. Secret-like values in safety cases
must be explicitly marked fake or nonfunctional test data.

This foundation stops at offline fixture validation. It does not clone source
repositories, call candidate or judge models, import fixtures over the
network, compare baselines, or make benchmark recommendations.
