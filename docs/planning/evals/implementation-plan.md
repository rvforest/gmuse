# Maintainer Evals Implementation Plan

Status: planning guide for converting `requirements.md` into formal Speckit
specifications.

The formal eval specs live under `specs/draft/` because they describe proposed
maintainer-only eval tooling, not current gmuse behavior.

The eval system is maintainer-only tooling. It should not become part of the
ordinary `gmuse msg` user workflow, should not require provider credentials in
default CI, and should avoid adding runtime dependencies for normal package use.

## Purpose

The requirements notes describe a complete eval program: fixtures, runner,
live calls, judging, baselines, importer, and eventually reference benchmarks.
That is too broad for one implementation spec. This plan splits the work into
small Speckit specs that can be implemented and validated independently.

## Spec Sequence

### 1. Eval Fixture And Suite Foundation

Formal spec: `specs/draft/009-eval-fixtures-and-suites/`

Goal: Define the offline data model and prove fixtures can reproduce staged
diffs.

Includes:

- Fixture schema and versioning.
- Suite schema and versioning.
- Stable case IDs and fixture revisions.
- Suite membership for `smoke`, `core`, and `safety`.
- Required source/provenance metadata for real OSS fixtures.
- Source license evidence and maintainer redistribution-review status.
- Synthetic and adapted fixture metadata.
- Rubric schema enough to describe required concepts, forbidden concepts,
  allowed formats, allowed conventional types, and notes.
- Temporary git repository reconstruction.
- Staged diff digest verification.
- Manual suite validation command.
- Validation coverage reporting by ecosystem, source repo, change type, format,
  safety tag, history usage, branch usage, hint usage, and `max_chars` usage.

Does not include:

- Live model calls.
- LLM-as-judge scoring.
- Baseline comparison.
- Fixture importing from GitHub.
- Public benchmark recommendations.

Acceptance focus:

- A tiny checked-in `smoke` suite can be validated offline.
- Reconstructed staged diffs match expected digests.
- Missing required attribution fails validation for real OSS fixtures.

### 2. Production-Path Eval Runner

Formal spec: `specs/draft/010-eval-runner/`

Goal: Run gmuse against validated fixtures using production generation behavior.

Includes:

- Applying fixtures into temporary git repositories.
- Staging changes and using gmuse's existing git/context/prompt machinery.
- Config overrides for format, history depth, branch context, hints,
  repository instructions, `max_chars`, model, temperature, and token limits.
- Dry-run/planning mode that makes no provider calls.
- Capturing rendered prompt hashes, prompt size, estimated tokens, context
  metadata, validation outcomes, raw generated message, and operational errors.
- JSONL per-output records.
- JSON run summaries.
- Artifact schema versioning.

Does not include:

- LLM-as-judge scoring beyond deterministic checks.
- Resume behavior.
- Baseline promotion.
- Fixture importer.

Acceptance focus:

- The runner uses the same behavior as `generate_message` except for
  instrumentation.
- Invalid model outputs and production validation failures are preserved.
- Deterministic checks classify format and `max_chars` failures consistently
  with gmuse validation.

### 3. Live Run Budgeting And Resume

Formal spec: `specs/draft/011-eval-live-budgeting-resume/`

Goal: Make live maintainer eval runs explicit, resumable, and cost-controlled.

Includes:

- Required call budgets for live candidate and judge calls.
- Run plan display before calls.
- Interactive confirmation.
- Non-interactive `--yes` mode that still requires budgets.
- Incremental result writing.
- Resume by skipping completed records.
- Resume compatibility checks for suite, config, model list, prompt version,
  judge config, and artifact schema.
- Candidate call, judge call, budgeted call, and actual call accounting.

Does not include:

- Default CI automation.
- Automatic retries or repair loops.

Acceptance focus:

- Dry-run never makes calls.
- Interrupted runs preserve completed records.
- Resume rejects incompatible run settings.

### 4. Judge And Scoring

Formal spec: `specs/draft/012-eval-judge-scoring/`

Goal: Add rubric-based scoring for maintainer review and regression analysis.

Includes:

- LLM-as-judge integration.
- Judge calibration against manually annotated examples.
- Judge input controls that hide candidate model identity by default.
- Fixed judge model, judge prompt version, rubric version, and parameters per
  comparison.
- Judge structured output.
- Deterministic checks before judge scoring.
- Hard failure gates for privacy leaks, severe injection obedience, and
  production validation failures.
- Accuracy and quality rubric scores.
- Usability categories.
- Versioned error taxonomy.
- Separate operational error categories.
- Concise judge rationales.
- Self-judging flags.
- Pairwise judge order controls if pairwise judge scoring is added later.
- Optional manual annotations and overrides while preserving original judge
  output.

Does not include:

- Strong user-facing model recommendations.
- Broad benchmark reports.

Acceptance focus:

- Hard failures gate aggregate usability.
- Per-dimension scores are preserved even when an aggregate score is computed.
- Judge metadata is sufficient to compare runs later.

### 5. Baselines And Comparison

Formal spec: `specs/draft/013-eval-baselines-comparison/`

Goal: Support maintainer regression review against promoted results.

Includes:

- Baseline promotion command.
- Validation before promotion.
- Stripping debug-only fields by default.
- Preserving generated messages, score metadata, prompt hashes, model metadata,
  config metadata, and suite metadata.
- Same-model regression comparison.
- Optional different-model benchmark comparison.
- Pairwise candidate-versus-baseline reporting.
- Per-dimension deltas.
- New hard failure reporting.
- Prompt size/token deltas.
- First-shot success deltas.
- Error category deltas.
- Warnings when suite, case, model, config, prompt version, judge version, or
  schema versions differ.

Does not include:

- Hardcoded accept/reject decisions beyond hard-failure flags.
- Public recommendation pages.

Acceptance focus:

- Baselines are intentionally promoted, not accidentally created from raw runs.
- Comparison reports evidence and deltas without hiding per-case results.

### 6. Fixture Importer

Formal spec: deferred.

Goal: Make curated real-commit fixtures practical after the fixture schema has
settled.

Includes:

- Public GitHub repository import by canonical HTTPS URL.
- Exact full commit SHA pinning.
- Local clone caching.
- Original commit message capture.
- Required attribution metadata capture.
- Prior commit message capture.
- Excluding the evaluated commit from fixture history.
- Initial `example_good` from original commit subject.
- Real, adapted, and synthetic fixture marking.
- Reviewable/editable fixture output.
- Reconstructed staged diff digest validation.

May reject:

- SSH URLs.
- Private repositories.
- Non-GitHub remotes.
- Arbitrary git URLs.

Acceptance focus:

- Imported fixtures validate with the same foundation validator.
- Import output is reviewable before being committed.

### 7. Reference Benchmarks

Formal spec: deferred.

Goal: Publish evidence-backed model guidance only after regression evals are
stable and real results exist.

Includes:

- Model candidate metadata.
- Model class/profile labels.
- Raw per-model results.
- Benchmark summaries by model class/profile.
- Caveats for cost, latency, complex diffs, local/private model preferences,
  model availability changes, and judge limitations.

Does not include:

- Provider preference claims.
- Recommendations based only on aggregate scores.
- Large public benchmark suites in the initial version.

Acceptance focus:

- Recommendations are light, caveated, and backed by inspectable raw results.
- Models with privacy or severe injection hard failures are not softly
  recommended.

## Suggested First Slice

Start with Spec 1 and keep it small:

- One synthetic fixture.
- One adapted safety fixture.
- One real OSS fixture only if attribution requirements are clear.
- A `smoke` suite that is a subset of `core`.
- Manual validation only.

This proves the data model and reconstruction approach before live model calls,
judging, or baseline tooling add complexity.

## Cross-Cutting Constraints

- Evals are maintainer-only.
- Live calls are manual and budgeted.
- Default CI must not require provider credentials.
- Normal package users should not pay for eval-only dependencies.
- Eval runs should use production gmuse behavior wherever practical.
- Eval-only instrumentation may observe prompts, context, validation errors,
  and outputs, but must not alter generation behavior.
- Prompt-affecting changes should update `PROMPT_VERSION`.
