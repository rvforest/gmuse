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
  --limit-samples 5 \
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

Use the same model identifiers as `gmuse msg`. For example, pass
`--model openrouter/openai/gpt-4.1-mini` to route this model through OpenRouter
using your OpenRouter credential.

The smoke suite has five entries per model. A live sample cap smaller than the
selected matrix fails before provider calls. Execution is serial; token, cost,
and time run limits are unsupported and rejected. Inspect cannot account for
gmuse's direct provider calls. `--max-tokens` still caps each production response.

## 4. Choose an explicit log directory when needed

```bash
uv run python -m tools.evals.gmuse_evals run \
  --mode live \
  --suite smoke \
  --model gpt-4.1-mini \
  --limit-samples 5 \
  --log-dir .gmuse-evals/inspect/smoke-gpt-4.1-mini \
  --yes
```

Expected:

- missing log directories are created;
- conflicting run identities fail before execution;
- live runs do not infer state from prior check runs.

## 5. Inspect result logs

Start the viewer with `uv run inspect view --log-dir <log-directory>`. Open
a sample and select **Info → Metadata**. The `generated_message` field holds
the returned commit message, and `production_validation` shows its validation
outcome and any failure reason. The **Scoring** tab is empty for these runs.

Expected metadata:

- generated message when available;
- production validation outcome;
- operational errors separated from validation failures;
- prompt hash, prompt size, token estimates, prompt version, and context
  metadata;
- suite, case, fixture, and rubric identity, including integer revisions
  (`suite_version` is `str(suite.revision)`; sample metadata uses the key
  `rubric_version` for the integer rubric revision) and generation-config
  identity;
- raw prompt text absent by default.

For a run with checked-in assets from a clean checkout, `gmuse_project_revision`
identifies the source commit. Reconstruct the fixture from that revision and
compare the expected `fixture_digest` with the observed `staged_diff_digest`.
The runner warns about local changes in the eval asset tree or runner files,
and about assets outside the checkout. These runs can still proceed, but you
may need to retain the local inputs to reproduce them. A live rerun can return
a different message even with identical inputs.

Rubric digests, scoring-profile identity, and an assessment-evidence reference
are not recorded yet; they are deferred to judge/scoring (spec 012) and
Inspect-log comparison (spec 013).

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
