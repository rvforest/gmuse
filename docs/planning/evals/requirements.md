# Maintainer Evals Requirements

Status: planning notes, not a formal Speckit specification.

These notes capture requirements decisions for adding LLM evaluation support to
gmuse. They are intended to be reviewed and then converted into a formal
Speckit spec.

## Goals

- Establish a reference benchmark that helps users choose an appropriate model
  class for commit message generation.
- Provide a maintainer-focused regression baseline for evaluating prompt,
  context, validation, and other generation-path changes.
- Keep live model and judge calls manual, explicit, resumable, and
  cost-controlled.
- Use real gmuse behavior for evaluation rather than a parallel evaluation
  pipeline.
- Build a curated, reusable eval dataset based primarily on high-quality real
  open source commits.

## Audiences

- Regression evals are primarily for the maintainer.
- Reference/model comparison evals are for end users choosing a model.

## Core Evaluation Dimensions

V1 should evaluate the following dimensions:

- Accuracy to the staged diff.
- Format compliance.
- Commit message quality.
- Injection resistance.
- Privacy protection.
- First-shot success.

Accuracy means the generated message describes changes that are actually
present in the diff and does not invent behavior, affected areas, issue
numbers, security claims, performance impact, or user impact not supported by
the diff.

Format compliance includes selected output format, one-line requirements where
applicable, no extra commentary, no markdown/code fences, and configured
constraints such as `max_chars`.

Commit message quality means the message is likely to be usable with no or only
minor edits. Quality should consider specificity, concision, imperative mood,
signal prioritization, scope fit, style fit where applicable, and readability.

Injection resistance means the model treats instruction-like text inside diffs
as data, not as instructions to follow.

Privacy protection means generated messages must not leak raw secrets,
credentials, tokens, passwords, private keys, personal emails, usernames, or
unsanitized branch identifiers.

First-shot success means the model produces output accepted by gmuse's
production validation on the first attempt. V1 should not add retry or repair
behavior unless production gmuse does.

## Hard Failures

Hard failures have zero tolerance. If a hard failure occurs, the case fails
regardless of judge score.

V1 hard failures should include:

- Privacy leaks.
- Severe injection obedience.
- Production validation failures for mandatory constraints, such as invalid
  output structure or exceeding configured `max_chars`.

Wrong or suboptimal conventional commit type should be scored as a quality or
accuracy issue, not a safety hard failure. Conventional Commits does not define
a universal closed list of allowed types, even though gmuse currently prompts
and validates a limited set.

Models with privacy hard failures must be ineligible for soft recommendation.
Models with severe injection-following failures should be ineligible for soft
recommendation unless the failure is clearly caused by a fixture or rubric
error.

## Scoring

The scoring schema should support:

- Pass/fail checks.
- Numeric rubric scores where useful.
- Categorical usability ratings.
- Error categories.
- Concise judge rationales.
- Optional human annotations and overrides.

Scoring should vary by dimension:

- Hard constraints use pass/fail.
- Accuracy and quality use numeric rubric scores, such as 1-5.
- Usability uses categories such as `usable`, `minor_edit`, `major_edit`, and
  `unusable`.

V1 should compute an aggregate score for convenience, but it must be secondary.
Aggregate scores must use documented weights, and results must always preserve
per-dimension scores. Soft recommendations must not be based on aggregate score
alone.

Suggested initial weighting for serious formats:

- Accuracy: 50%.
- Commit message quality: 35%.
- Style/history fit where applicable: 15%.

Format, privacy, injection, and `max_chars` failures should act as gates rather
than ordinary weighted soft points.

## Error Taxonomy

V1 should include a compact, versioned error taxonomy. Initial categories:

- `format_error`
- `accuracy_error`
- `hallucination`
- `vague`
- `too_verbose`
- `wrong_scope`
- `wrong_conventional_type`
- `injection_followed`
- `privacy_leak`
- `extra_output`
- `validation_error`
- `other`

Operational provider or judge failures should be recorded separately from
quality/compliance failures. Initial operational categories:

- `auth_error`
- `rate_limit`
- `timeout`
- `network_error`
- `context_length`
- `empty_response`
- `judge_parse_error`
- `unknown_error`

gmuse validation failures are output compliance failures, not operational
provider failures.

## Rubrics And References

Eval cases should use rubrics with multiple acceptable outputs rather than a
single golden answer.

Case rubrics may include:

- Required concepts.
- Forbidden concepts.
- Allowed conventional types.
- Optional allowed scopes.
- `example_good` messages.
- `example_bad` messages.
- Quality notes.
- Safety notes.

Original commit messages from curated source commits should be imported as
initial `example_good` candidates by default, because the core suite will use
intentionally selected high-quality commits. The original message must still be
preserved in source metadata even if it is edited or removed from the rubric.

Judges must not require exact match to the original source commit message.

## Judge Integration

V1 must include LLM-as-judge integration.

Requirements:

- Use deterministic checks before judge scoring where possible.
- Use one fixed judge model, prompt, rubric version, and parameters across all
  candidate models in the same benchmark comparison.
- Prefer a judge model distinct from the candidate model.
- Record judge model, judge prompt version, rubric version, parameters, and
  structured judge output.
- Flag self-judged results.
- Avoid strong user-facing recommendations from self-judged results.
- Include concise rationale for each scored dimension.
- Support optional manual annotations and score/pass-fail overrides while
  preserving original judge output.
- Support judge calibration against a small manually annotated set for each judge
  prompt/rubric version before relying on scores for promoted regression
  evidence.
- Hide candidate model/provider identity from ordinary judge prompts where
  practical, and record any diagnostic mode that exposes it.

Judge input should use the raw staged diff and case rubric as primary evidence,
not the rendered generation prompt. The judge may receive curated examples,
format/config information, and relevant evaluation context such as history,
hints, branch context, or repo instructions when those are part of the case
rubric.

If pairwise judge scoring is added later, candidate ordering must be recorded and
calibration should support order-swapped or randomized presentation to detect
position bias.

## Pairwise And Absolute Scoring

V1 should support absolute rubric scoring for ordinary per-run scoring and
benchmark aggregation.

Regression comparisons should support pairwise comparison against saved
baseline outputs. Pairwise comparison should be used to validate claimed
improvements, but the system should report evidence rather than automatically
deciding whether a change should be accepted.

Regression comparison should report:

- Per-dimension deltas.
- Per-case candidate versus baseline results.
- New hard failures.
- Prompt size/token changes.
- First-shot success changes.
- Error category changes.

## Suites

V1 should define these suite concepts:

- `smoke`: a tiny subset of core cases for checking eval machinery.
- `core`: approximately 20-25 curated cases for regression and quality
  evaluation.
- `safety`: injection/privacy cases, including any safety-tagged core cases and
  future expanded safety cases.

The `smoke` suite should be a subset of `core`, not a separate fixture set. It
should not be used for user-facing model recommendations.

A broader reference `benchmark` suite can be added later, likely around 50-75
cases. A very broad public benchmark of 200+ cases is out of scope for v1.

Exploratory/future-behavior suites are out of scope for v1.

## Core Fixture Strategy

The core suite should primarily use hand-curated real commits from reputable
open source projects.

Each selected commit must be reviewed to ensure:

- The diff alone supports a good commit message.
- The original commit message is high quality.
- The change is self-contained enough for eval use.
- The commit is not dominated by generated files, vendored files, binary
  assets, lockfiles, or mechanical formatting unless deliberately testing that
  behavior.
- The message does not depend heavily on external PR or issue context.

The core suite should include several well-used ecosystems rather than being
Python-only. The initial suite should avoid overrepresenting any single source
project. For 20-25 cases, no upstream repo should contribute more than 2-3
fixtures unless explicitly justified.

The suite should be balanced by change type as a guideline rather than a rigid
quota. Suggested initial balance:

- `fix`: 4-5 cases.
- `feat`: 3-4 cases.
- `docs`: 3 cases.
- `test`: 2-3 cases.
- `refactor`: 3 cases.
- `chore`/config/CI/dependencies: 3-4 cases.
- Privacy/injection: 3-4 cases, overlapping with the categories above where
  practical.
- Gitmoji smoke: 1-2 cases, with only light quality expectations.

Each core fixture should include a maintainer-written selection rationale.

## Fixture Provenance And Attribution

Any checked-in fixture derived from an OSS commit must include mandatory source
metadata:

- Source repository URL.
- Source owner/repo.
- Commit SHA.
- Commit URL.
- Source license metadata.
- Source license expression or source license URL when available.
- Maintainer redistribution-review status.
- Full original commit message, including subject and body.
- Import timestamp.
- Whether the fixture is real, adapted, or synthetic.
- Adaptation notes if applicable.

Fixture validation must fail checked-in real OSS fixtures missing required
attribution metadata.

Synthetic fixtures must be marked synthetic. Adapted fixtures must explain what
changed.

## Fixture Representation

Eval runs should be offline and self-contained after fixture import.

Fixtures should store compact data sufficient to reconstruct a temporary git
repository, stage the evaluated patch, and run gmuse's normal context and
generation machinery.

Requirements:

- Normal eval runs must not require cloning source repositories.
- Evaluated staged diffs should preserve the original source diff exactly unless
  explicitly marked adapted.
- Original changed file paths should be preserved.
- Surrounding repository contents may be minimized to what is needed to apply
  the patch.
- Fixtures must not pre-truncate diffs. If gmuse truncates, evals must observe
  gmuse's production truncation.
- Fixture setup should verify that the produced staged diff digest matches
  expected metadata.

Core fixtures should generally avoid enormous diffs in v1. A large/truncation
case may be added later, but is not required for v1.

## Fixture Importer

V1 should include a fixture importer to make curated real-commit fixtures
practical.

Importer requirements:

- Support public GitHub repositories in canonical `https://github.com/owner/repo`
  forms.
- Support remote cloning explicitly for import commands.
- Support local caching of clones to avoid repeated downloads.
- Pin imports to exact full commit SHAs, not branches.
- Capture required source attribution metadata.
- Preserve the full original commit message.
- Import the original commit message subject as an initial `example_good`
  candidate by default.
- Capture a configurable number of prior commit messages, defaulting to gmuse's
  default history depth.
- Ensure the evaluated commit itself is not included in imported history.
- Mark fixtures as real, adapted, or synthetic.
- Produce reviewable/editable fixtures.
- Validate that the reconstructed staged diff matches the imported patch digest.

V1 importer may reject SSH URLs, private repositories, non-GitHub remotes, and
arbitrary git URLs.

Historical file states do not need to be reconstructed. Fixture history may use
synthetic placeholder commits as long as original prior commit messages are
preserved, because gmuse currently consumes commit messages, not historical
diffs.

## Production Path Fidelity

Eval runs must exercise gmuse's production generation behavior as closely as
possible.

Requirements:

- Use gmuse's production diff/context/prompt-building machinery wherever
  practical.
- Do not maintain a separate normalization or truncation pipeline for staged
  diffs.
- Apply fixtures into temporary git repositories and stage changes so production
  git machinery is used.
- Use gmuse defaults unless a suite, case, or run explicitly overrides config.
- Do not add eval-only retry, repair, or post-processing.
- Preserve raw invalid model outputs and validation errors when production
  validation fails.

Instrumentation may capture rendered prompts, raw model output, validation
errors, and context metadata, but must not alter generation behavior.

## Formats

Cases should declare applicable formats rather than running every case against
every format.

V1 should focus semantic quality scoring on freeform and conventional formats.
Gitmoji should have minimal smoke coverage:

- Starts with exactly one emoji.
- No extra commentary.
- Description is plausible for the diff.

Conventional cases should include `allowed_types`; most should have exactly one
expected type, while ambiguous cases may allow more than one. Scope should be
optional unless a case explicitly tests scope selection.

V1 should focus on single-line commit messages. Multi-line commit body
evaluation is out of scope unless gmuse explicitly adds that product behavior.

## History, Branch, Hints, And Repo Instructions

Commit history is a core gmuse feature and should be covered.

Requirements:

- Fixture repos should support realistic recent commit history.
- Core fixtures should include history where relevant.
- The runner should support optional manual history ablation, comparing default
  history behavior with `history_depth=0`.
- History ablation must not run automatically as part of default eval runs.
- History ablation results should report both quality deltas and prompt
  size/token deltas.

Branch context should be supported but lighter than history:

- Fixture repos must support branch names.
- Core should include a small number of branch-context cases if useful.
- Branch cases should verify utility and privacy behavior.
- Sanitized branch context should be checked before prompt construction.

User hints are more important than repo instructions but should still be scoped:

- Cases must support user hints.
- Core should include 2-3 targeted hint cases.
- Hints should influence output only when supported by the diff.
- If a hint conflicts with the diff, accuracy to the diff wins.

Repository instructions should receive minimal mechanism coverage:

- Cases should support fixture-level repository instructions.
- Core may include one `.gmuse` case.
- `.gmuse` instructions should not be a major benchmark dimension in v1.
- Safety hard failures override repository instructions.

## Max Character Limits

`max_chars` belongs in evals because unit tests cannot determine whether live
models follow the configured output limit.

Requirements:

- Core should include a few `max_chars` cases.
- Deterministic checks must count characters the same way gmuse does.
- `max_chars` violations are hard failures for applicable cases.
- Results should distinguish limit compliance, quality degradation caused by
  tight limits, and limits that are too small to express a useful message.

## Privacy And Injection

Privacy and injection cases should be included in v1.

Privacy cases must use fake/nonfunctional sensitive values that are realistic
enough to exercise leak behavior.

Injection cases should cover instruction-like text in:

- Comments.
- Markdown/docs.
- Test fixtures.
- String literals.
- Config examples.
- Deleted text where useful.
- Obfuscated or encoded text where useful.
- Direct and indirect/external-content patterns.

The model should summarize the actual change and must not follow instructions
embedded in diff content.

Safety cases should be taggable and runnable as a dedicated suite view.

## Lower Priority Or Out Of Scope For V1

The following are lower priority or out of scope for v1:

- CI automation for live evals.
- Default CI validation of eval suites.
- Large public benchmark suite.
- Exploratory/future-behavior suites.
- Custom conventional commit types inferred from history.
- Multi-line commit body generation.
- Extensive gitmoji quality scoring.
- Binary/generated/lockfile-heavy cases.
- Refusal-style negative controls.
- Automatic retry or repair loops.
- Broad `.gmuse` instruction behavior evaluation.

## Live Run Cost Controls

Live evals must be manual and guarded by explicit budget controls.

Requirements:

- Live model or judge calls must require an explicit budget limit.
- Combined total call budget must include candidate generation and judge calls.
- Candidate and judge call counts should also be reported separately.
- Live runs must show a run plan before making calls.
- Interactive live runs should require confirmation.
- Non-interactive runs may skip confirmation only with an explicit flag such as
  `--yes`, and still require budget limits.
- Dry-run/planning mode must never make calls.
- Live runs must default to one generation per model/case.
- Repeat counts above one must be explicit and included in budget planning.
- Budget and actual call counts must be recorded in result artifacts.
- Live runs must write incremental results so interrupted runs preserve completed
  records.
- Resume must skip completed records, enforce budget on remaining calls, and
  reject incompatible resume configuration.

V1 should not include live eval automation in CI. Default CI should not require
provider credentials.

## Results, Baselines, And Comparison

Machine-readable artifacts are the v1 priority.

Requirements:

- Per-output records should be emitted as JSONL.
- Run summaries should be emitted as JSON.
- Artifact schemas must be versioned.
- Results must record enough metadata for reproduction and comparison:
  - Suite id/version.
  - Case id/revision.
  - Fixture provenance.
  - gmuse package version if available.
  - gmuse git commit SHA and dirty status when available.
  - `PROMPT_VERSION`.
  - Prompt hashes.
  - Model/provider id.
  - Model profile/class metadata.
  - Generation config.
  - Judge config.
  - Deterministic check results.
  - Rubric scores.
  - Error categories.
  - Generated message.
  - Prompt/context metadata.
  - Timestamps.

Full rendered prompts should be saved in local run artifacts for debugging.
Promoted baselines should include prompt hashes but not full prompts by default.

Generated message text should be stored in promoted core baselines because it is
needed for pairwise comparison and human review.

The eval system must distinguish generated run results from promoted baselines.
Raw live run artifacts should be gitignored by default. Baseline promotion must
be intentional.

V1 should include lightweight baseline promotion tooling that validates a run,
strips debug-only fields by default, preserves generated messages and score
metadata, and refuses incomplete runs unless explicitly allowed.

Comparison tooling should support:

- Same-model regression comparison.
- Different-model benchmark comparison.
- Clear warnings when model, prompt version, suite version, judge version, or
  config differ.

Regression comparison should report evidence and deltas, not make hardcoded
accept/reject decisions beyond hard-failure flags.

## Model Benchmarks And Recommendations

Reference benchmarks should store raw results by exact model and present
findings by configurable model class/profile.

Requirements:

- Model classes/profiles must be configurable metadata, not hardcoded.
- Each benchmark candidate should declare model id, provider, class/profile
  label, and notes such as hosted/local/open-weight if known.
- Include a default sample model configuration file.
- Do not require all listed providers to be configured.
- Live runs should fail clearly when selected models lack credentials or local
  runtime availability.
- Benchmark mode should use the same suite, prompt version, rubric, judge, and
  gmuse config across candidate models by default.
- Model-specific overrides may be supported, but must be explicit and recorded.
- Default benchmark behavior should use gmuse defaults.

Local/open-weight models should be supported as target types where compatible
with gmuse and LiteLLM, especially via Ollama or hosted open-weight providers.
V1 benchmark reports do not need to include a large local model fleet.

Soft recommendations should be light and evidence-backed:

- Recommend by model class/profile rather than provider preference.
- Raw per-model results must remain inspectable.
- Recommendations must account for hard failures, not only average score.
- Recommendations should include caveats for complex diffs, cost sensitivity,
  latency sensitivity, local/private model preferences, changing model
  availability, and judge limitations.

## Token, Cost, And Latency Metadata

Prompt size and token estimates are v1 requirements because they are
provider-neutral and affected by gmuse behavior.

Requirements:

- Results must record prompt character count and estimated prompt tokens using
  gmuse's token-estimation logic.
- Results should record completion token counts when providers expose them.
- Results should record history depth, truncation status, and context-size
  metadata.
- Live benchmarks may record wall-clock latency, but latency must not be a
  quality gate.
- Dollar cost estimates may be generated from configurable pricing metadata, but
  must be clearly marked as estimates and not required for regression
  evaluation.

## Versioning

Versioning is required from day one.

Requirements:

- Eval artifact schemas must be versioned.
- Suites must have versions.
- Rubrics and judge prompts must have versions.
- Fixtures should have stable IDs and may have revisions.
- Results must record suite version, fixture/case ID, rubric version, judge
  prompt version, gmuse package/git version, and gmuse `PROMPT_VERSION`.
- Prompt-affecting changes should update `PROMPT_VERSION`.
- Comparison tooling should flag changed prompt hashes, especially if
  `PROMPT_VERSION` did not change.
- Baseline comparison should warn or fail when suite/rubric/schema versions are
  incompatible unless explicitly overridden.

## Validation

V1 should include a manual suite validation command.

Validation must check:

- Fixture schema validity.
- Rubric schema validity.
- Required attribution metadata for checked-in real OSS fixtures.
- Fixture reproducibility by reconstructing a temporary repo and verifying the
  staged diff digest.
- Conventional expected types are compatible with gmuse's current supported type
  set.

Validation should report coverage by:

- Ecosystem.
- Source repo.
- Change type.
- Format.
- Safety tag.
- Injection sub-tag.
- Origin kind and source license evidence status.
- History usage.
- Branch usage.
- Hint usage.
- `max_chars` usage.

Balance issues should warn by default rather than fail unless a suite policy
marks them required.

V1 validation should be manual, not default CI.

## Documentation

V1 should include maintainer documentation.

Docs should explain:

- How to validate suites.
- How to import fixtures.
- How to run offline checks.
- How to run live evals manually.
- How to compare against a baseline.
- How to promote a baseline.
- How budget controls work.
- How to author fixtures and rubrics.
- Source selection criteria.
- Attribution requirements.
- Safety/privacy/injection case guidance.

User-facing benchmark docs should wait until at least one real benchmark result
exists.

## Open Questions

- Exact initial judge model.
- Exact initial recommended regression model/profile.
- Exact aggregate score weights.
- Exact JSON/JSONL schema fields.
- Exact first 20-25 source commits.
- Whether docs planning notes should remain after conversion to formal spec.
