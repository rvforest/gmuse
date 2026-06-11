# Quickstart: production-path eval runner

The eval runner is maintainer-only tooling for running gmuse against validated eval fixtures and preserving raw production-path outputs.

## 1. Validate fixture and suite prerequisites

Use the fixture/suite foundation from spec 009 to validate the suite before running generation.

Expected behavior:

- suite membership resolves;
- fixture schemas and required provenance pass validation;
- reconstructed staged diffs match expected digests.

If fixture validation fails, fix the spec 009 fixture or suite before using the runner.

## 2. Preview a smoke run with no provider calls

```bash
gmuse eval run --suite smoke --model gpt-4.1-mini --output-dir .gmuse-evals/runs/smoke --plan
```

Expected behavior:

- selected suites and case IDs are shown;
- selected model/config combinations are shown;
- planned attempt count is shown;
- output artifact paths are shown;
- provider call count is zero;
- no generated-message JSONL records are written.

Use planning mode before any live run.

## 3. Execute a smoke run with production generation behavior

```bash
gmuse eval run --suite smoke --model gpt-4.1-mini --output-dir .gmuse-evals/runs/smoke --execute
```

Expected behavior:

- each fixture is applied to an isolated temporary git repository;
- fixture changes are staged and verified;
- gmuse uses the normal production git/context/prompt/generation/validation behavior;
- one `outputs.jsonl` record is written for each attempted case/model/config combination;
- `summary.json` reports counts and artifact locations.

## 4. Inspect result artifacts

```bash
head -n 1 .gmuse-evals/runs/smoke/outputs.jsonl
cat .gmuse-evals/runs/smoke/summary.json
```

Expected behavior:

- output records include generated messages when available;
- production validation failures preserve the raw generated message;
- provider/setup failures are listed as operational errors;
- prompt hashes, prompt size, token estimates, and context metadata are present;
- raw prompt text is absent by default.

## 5. Troubleshoot a failing case

```bash
gmuse eval run --suite smoke --model gpt-4.1-mini --output-dir .gmuse-evals/runs/debug --execute --preserve-debug
```

Expected behavior:

- temporary repository or prompt debug material may be preserved for inspection;
- preserved paths are reported clearly;
- this behavior happens only when explicitly requested.

## 6. Confirm scope boundaries

This runner does not:

- score outputs with an LLM judge;
- resume interrupted runs;
- enforce live-call budgets;
- promote baselines;
- import fixtures;
- publish model recommendations.

Those behaviors belong to later eval specs.
