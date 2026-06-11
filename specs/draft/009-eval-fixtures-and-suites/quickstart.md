# Quickstart: Eval Fixtures And Suites

This quickstart validates the maintainer-only fixture foundation. It does not
make model calls and does not require provider credentials.

## Prerequisites

- Python 3.10+
- Git
- `uv sync`

## Validate The Smoke Suite

```bash
uv run gmuse eval validate --suite smoke
```

Expected outcome:

- fixture, rubric, case, and suite schemas are valid
- temporary repositories are reconstructed
- evaluated changes are staged
- staged diff digests match expected metadata
- coverage dimensions are reported
- no LLM provider credentials are required

## Inspect Machine-Readable Output

```bash
uv run gmuse eval validate --suite smoke --json
```

Expected outcome:

- output includes `schema_version`, `suite_id`, `suite_version`, `status`,
  `errors`, `warnings`, and `coverage`
- `status` is `passed` for a valid smoke suite

## Check A Provenance Failure

Create or edit a real OSS fixture so that required attribution metadata is
missing, then run:

```bash
uv run gmuse eval validate --suite smoke
```

Expected outcome:

- validation exits non-zero
- output identifies the fixture and missing provenance field
- no model or judge calls are made

## Check A Digest Failure

Edit fixture patch data without updating the expected staged diff digest, then
run:

```bash
uv run gmuse eval validate --suite smoke
```

Expected outcome:

- validation exits non-zero
- output identifies the fixture with the digest mismatch
- the report includes expected and observed digest values
