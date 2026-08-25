# Quickstart: Production-Path Eval Runner

The eval runner is maintainer-only tooling for running gmuse against validated
eval fixtures through an Inspect AI task. It is invoked through the repository
module entrypoint, not a public `gmuse eval` command.

## 1. Validate fixture and suite prerequisites

```bash
uv run python -m tools.evals.gmuse_evals validate --suite smoke
```

Expected:

- suite membership resolves;
- fixture schemas and required provenance pass validation;
- reconstructed staged diffs match expected digests.

## 2. Run a local check with no provider calls

```bash
uv run python -m tools.evals.gmuse_evals run --mode check --suite smoke
```

Expected:

- selected case IDs and effective settings are printed;
- temporary repositories are reconstructed;
- gmuse uses the production git/context/prompt/validation path;
- deterministic local output replaces only the provider response;
- Inspect logs are written with gmuse run/sample metadata;
- provider call count is zero.

Check logs are runner-integration evidence. They are not candidate model quality
evidence and are skipped by judge scoring by default.

## 3. Run live candidate generation with guardrails

```bash
uv run python -m tools.evals.gmuse_evals run \
  --mode live \
  --suite smoke \
  --model gpt-4.1-mini \
  --limit-samples 2 \
  --yes
```

Expected:

- the suite validates before provider calls;
- planned samples and configured limits are displayed;
- live execution starts only after confirmation or `--yes`;
- each fixture is applied to an isolated temporary git repository;
- fixture changes are staged and verified;
- gmuse uses normal production generation and validation behavior;
- one Inspect sample result is recorded for each executed case/model/config
  entry.

Multiple live models are allowed, and `--limit-samples` applies to the full
selected case/model/config matrix.

## 4. Choose an explicit log directory when needed

```bash
uv run python -m tools.evals.gmuse_evals run \
  --mode live \
  --suite smoke \
  --model gpt-4.1-mini \
  --limit-samples 2 \
  --log-dir .gmuse-evals/inspect/smoke-gpt-4.1-mini \
  --yes
```

Expected:

- missing log directories are created;
- conflicting run identities fail before execution;
- live runs do not infer state from prior check runs.

## 5. Inspect result logs

Use Inspect-native log viewing or gmuse log helpers.

Expected metadata:

- generated message when available;
- production validation outcome;
- operational errors separated from validation failures;
- prompt hash, prompt size, token estimates, prompt version, and context
  metadata;
- suite, case, fixture, rubric, model, and generation config identity;
- raw prompt text absent by default.

## 6. Troubleshoot a failing case

```bash
uv run python -m tools.evals.gmuse_evals run \
  --mode check \
  --suite smoke \
  --log-dir .gmuse-evals/inspect/debug-check \
  --preserve-debug
```

Expected:

- debug preservation is explicit;
- temporary repositories or prompts are available only in debug locations;
- ordinary Inspect logs still carry the required metadata.
