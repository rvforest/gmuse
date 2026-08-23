# Research: Eval Judge And Scoring

**Date**: 2026-06-11
**Feature**: `012-eval-judge-scoring`

## Deterministic Gates Before Judge Scoring

**Decision**: Run deterministic checks before judge scoring for production
validation failures, applicable `max_chars` violations, obvious extra-output
format failures, known fake secret leakage, and strong injection-following
markers that fixtures declare as forbidden output. By default, records with
deterministic hard failures are not sent to the LLM judge; they are written as
hard-failed scoring records without spending judge calls.

**Rationale**: These checks are objective, cheap, and aligned with the eval
requirements. Hard failures must not depend on subjective judge leniency.
Running them first also avoids spending live-call guardrails on
outputs that are already unusable unless the maintainer explicitly asks for
diagnostic judge scoring.

**Alternatives considered**:

- Let the judge decide every failure: rejected because privacy and validation
  failures need zero-tolerance gates.
- Only use production validation: rejected because privacy and injection cases
  need fixture/rubric-aware checks beyond generic commit-message validation.
- Always judge hard-failed outputs: rejected for the default path because it
  spends live calls on unusable records and can make zero-tolerance failures
  appear softer than they are. A diagnostic flag can be added for explicit
  maintainer analysis.

## Inspect Scorer Adoption

**Decision**: Implement deterministic gates and LLM-as-judge scoring as Inspect
AI scorers when the framework spike confirms the required metadata can be stored
in Inspect logs. gmuse should not create a parallel scored JSONL artifact system
unless Inspect cannot represent required gmuse metadata.

**Rationale**: Specs 010 and 011 adopt Inspect for local task execution, logs,
and guardrails. Scoring is exactly where Inspect's scorer abstraction can remove
custom orchestration while preserving gmuse-owned hard gates and rubrics. Using
Inspect scorers keeps execution evidence and score evidence in the same local
log system.

**Alternatives considered**:

- Custom `scored-records.jsonl` and `judge-records.jsonl`: rejected as the
  preferred path because it duplicates Inspect scorer/log functionality.
- Hosted/account-backed scoring platforms: rejected because evals must remain
  local and not require hosted service accounts.
- Use only generic framework metrics: rejected because gmuse still needs
  deterministic commit-message validation, privacy/injection hard gates, and
  fixture-aware rubrics.

## Scoring Command Boundary

**Decision**: Implement scoring as Inspect scorer configuration plus an optional
maintainer command that consumes an existing Inspect eval log, for example
`python -m tools.evals.gmuse_evals score --log <inspect-log> ...`, when a
separate command is useful.

**Rationale**: Candidate generation and judge scoring have different failure
modes and are useful independently. A separate command lets maintainers run
deterministic-only scoring offline, retry or resume judge scoring without
touching candidate outputs, and keep failed judge work from making the candidate
run itself feel incomplete.

**Alternatives considered**:

- Add scoring as an optional phase of `run --mode live`: rejected because it
  couples candidate generation and judge scoring too tightly and makes resume
  targets less clear.
- Add a public `gmuse eval score` command: rejected to stay aligned with specs
  009 and 010, which keep eval tooling in maintainer repository commands.

## Scoring Artifact Layout

**Decision**: Treat Inspect logs as canonical scored artifacts. If the Inspect
spike exposes a required metadata gap, gmuse may write a compact sidecar under a
scoring subdirectory, but sidecars are not the default design.

**Rationale**: Scoring is an interpretation of immutable candidate sample
results, and there may be multiple scoring configurations as judge prompts,
rubrics, or models evolve. Inspect already models eval logs and scorer outputs,
so duplicating that structure should be avoided unless necessary.

**Alternatives considered**:

- Keep bespoke scored records as the primary record: rejected because it fights
  the framework adoption.
- Store scoring evidence outside local Inspect logs: rejected because source
  outputs and scoring should remain portable together.

## Hard Failure Semantics

**Decision**: Hard failure gates are independent boolean findings that force the
effective usability category to `unusable` and set `hard_failed=true`. Per-
dimension judge scores remain recorded when available.

**Rationale**: Maintainers need to inspect whether a model wrote an otherwise
good message that failed one safety gate. Preserving scores supports analysis
without allowing aggregate scores to hide a hard failure.

**Alternatives considered**:

- Zero all numeric scores after a hard failure: rejected because it loses
  diagnostic information.
- Treat hard failures as large aggregate penalties: rejected because weighted
  scores can obscure zero-tolerance failures.

## Judge Input Evidence

**Decision**: Judge input uses the raw staged diff, generated message, case
rubric, selected format/config constraints, and relevant case context such as
history, branch, hints, or repository instructions. The scoring command resolves
the canonical staged diff and rubric from Inspect sample metadata and spec 009
fixture/rubric assets rather than requiring full diffs or rubrics to be copied
into every Inspect sample result. The rendered generation prompt is not primary
judge evidence.

**Rationale**: The judge should assess whether the output matches the underlying
change and rubric, not whether it matches the exact prompt wording. Runner
prompt hashes and prompt metadata from spec 010 remain traceability metadata.
Keeping full diffs and rubrics out of ordinary sample metadata avoids
duplicated, stale large fields while still making the judge evidence available at
scoring time.

**Alternatives considered**:

- Include full rendered prompts by default: rejected because prompts can bias the
  judge toward prompt compliance over diff accuracy and may increase cost.
- Judge only the generated message and expected labels: rejected because
  accuracy cannot be assessed without the diff and rubric.
- Embed full diffs and rubrics into every Inspect sample result: rejected because
  Inspect sample metadata plus spec 009 assets provide a simpler source of truth.

## Judge Configuration Stability

**Decision**: A scoring run uses one fixed judge model, provider, judge prompt
version, rubric version, and parameter set for comparable outputs. Results record
that configuration on every scored output and in the summary.

**Rationale**: LLM-as-judge results are only comparable when the judge setup is
stable. Recording the setup at record level protects JSONL artifacts even if
they are split or merged later. OpenAI Evals similarly emphasizes versioning eval
data and bumping versions when an eval changes, because reproducibility depends
on stable eval definitions
([OpenAI Evals build guide](https://raw.githubusercontent.com/openai/evals/main/docs/build-eval.md)).

**Alternatives considered**:

- Allow per-model judge overrides inside one comparison: rejected for v1 because
  it weakens comparability.
- Store judge config only in the summary: rejected because individual scored
  records must remain self-describing.

## Judge Bias Controls And Calibration

**Decision**: Hide candidate model/provider identity from ordinary judge prompts,
record judge input controls, and support a calibration mode that compares judge
outputs against manually annotated examples for each judge prompt/rubric version.
If pairwise judge scoring is added later, it must support order-swapped or
randomized presentation for calibration.

**Rationale**: LLM-as-judge can be useful for open-ended outputs, but published
work documents systematic risks. MT-Bench/Chatbot Arena reports position,
verbosity, and self-enhancement biases while still finding strong judges useful
when limitations are handled explicitly. G-Eval reports stronger alignment with
human ratings than traditional NLG metrics but notes potential bias toward
LLM-generated text. A later position-bias study shows ordering effects can vary
by judge and task. OpenAI Evals recommends meta-evals with human-provided labels
for model-graded evals. For gmuse, the practical response is not to discard
judges; it is to treat judge configuration and calibration as first-class
metadata and keep human overrides available
([MT-Bench/Chatbot Arena](https://arxiv.org/abs/2306.05685),
[G-Eval](https://arxiv.org/abs/2303.16634),
[position bias study](https://arxiv.org/abs/2406.07791),
[OpenAI Evals model-graded workflow](https://raw.githubusercontent.com/openai/evals/main/docs/build-eval.md)).

**Alternatives considered**:

- Trust one judge prompt without calibration: rejected because prompt and judge
  changes could silently alter scores.
- Expose candidate model identity to help the judge contextualize output:
  rejected for ordinary scoring because it increases self-preference and brand
  bias risk.
- Require a large human-labeled calibration set in v1: rejected because the
  maintainer tool needs a lightweight path; small stable calibration examples are
  enough to catch obvious prompt, parse, and gate regressions.
- Add pairwise judge scoring immediately: rejected because absolute rubric
  scoring is enough for v1 and avoids position-bias complexity.

## Rubric Dimensions And Aggregate Score

**Decision**: Use numeric 1-5 scores for `accuracy`, `quality`, and optional
`style_history_fit`; use pass/fail gates for hard constraints; use categorical
`usable`, `minor_edit`, `major_edit`, `unusable` for usability. Compute a
secondary aggregate using accuracy 50%, quality 35%, and style/history fit 15%
when style/history context applies; otherwise redistribute the style/history
weight proportionally across accuracy and quality.

**Rationale**: The weights match the eval planning notes and keep factual
accuracy dominant. Usability remains categorical because it maps better to
maintainer review than a single number.

**Alternatives considered**:

- Single overall score only: rejected because it hides why a message is good or
  bad.
- Many fine-grained dimensions in v1: rejected because it would increase judge
  prompt complexity before the eval suite has enough scored examples.

## Error Taxonomy

**Decision**: Define two versioned taxonomies: quality/compliance errors and
judge/provider operational errors. Quality categories are attached to candidate
outputs; operational categories describe why scoring could not complete.

**Rationale**: A timeout or parse failure is not evidence that a candidate model
produced a bad commit message. Separating the taxonomies keeps summaries honest.

**Alternatives considered**:

- One combined taxonomy: rejected because operational failures would pollute
  quality metrics.
- Free-form error labels only: rejected because comparisons and summaries need
  stable categories.

## Self-Judging

**Decision**: Flag a result as self-judged when judge and candidate provider/model
identifiers are exactly equal or when model metadata declares them equivalent.
Self-judged results remain inspectable but are marked limited evidence. Candidate
identity should be hidden from the judge prompt where practical; self-judging is
computed from run metadata after the judge response is parsed.

**Rationale**: The requirements prefer a judge distinct from the candidate model
and warn against strong recommendations from self-judged results. Exact matching
is deterministic, while equivalence metadata allows provider aliases to be
handled explicitly. External judge research reinforces this because
self-enhancement and related self-preference effects are known limitations of
LLM-as-judge setups.

**Alternatives considered**:

- Block all self-judging: rejected because maintainers may need local diagnostic
  runs with limited credentials.
- Ignore self-judging: rejected because it overstates evidence quality.

## Manual Annotations And Overrides

**Decision**: Store manual annotations and overrides as append-only review
event files (`annotations.jsonl` and `overrides.jsonl`) that reference scored
output identifiers. Overrides produce effective scores/gates but never mutate
original deterministic checks or original judge results.

**Rationale**: Human correction is useful only when auditable. Append-only
metadata lets maintainers revise interpretation while preserving the automated
evidence that prompted the correction.

**Alternatives considered**:

- Edit scored JSONL records in place: rejected because it destroys provenance.
- Allow annotations only with no score effect: rejected because judge mistakes
  sometimes need corrected effective results for summaries.
- Maintain one mutable review-state JSON file: rejected because append-only
  events make revisions auditable and avoid rewriting scoring records.

## Live Guardrail Dependency

**Decision**: Treat judge calls as live calls governed by spec 011 guardrails.
Scoring must show planned judge sample count, require explicit configured limits
for live judge work, and use Inspect logging/reuse behavior where practical.

**Rationale**: Judge calls incur the same cost and interruption risks as
candidate generation calls. Reusing spec 011 guardrails keeps live evals
explicit and cost-controlled without a separate custom budget ledger.

**Alternatives considered**:

- Add separate judge-only budget behavior: rejected because this feature should
  reuse spec 011 guardrail concepts.
- Make scoring always offline: rejected because LLM-as-judge integration is in
  scope for this feature.

## Candidate Operational Errors

**Decision**: Include candidate operational-error inputs as explicit unscored
sample metadata in Inspect logs.

**Rationale**: Every source candidate sample should have corresponding scoring
metadata so summaries reconcile cleanly and operational candidate failures
remain visible during review. These samples are not judge-eligible and must not
fabricate scores.

**Alternatives considered**:

- Omit candidate operational errors from scoring metadata: rejected because input
  counts would not reconcile and failures could disappear from scoring review.
- Send candidate operational errors to the judge: rejected because there is no
  generated commit message to evaluate.

## Calibration Requirement

**Decision**: Support calibration and record whether a scoring run used a
calibration report, but do not require calibration before every live judge
scoring run.

**Rationale**: Calibration is effectively judging the judge against
maintainer-labeled examples. It is valuable for catching prompt/rubric regressions
and parse failures, but making it mandatory would add friction before the scoring
loop has proven useful. Future baseline promotion or benchmark-claim workflows
can require calibration.

**Alternatives considered**:

- Require calibration for all scoring: rejected as too heavy for maintainer
  iteration.
- Omit calibration support from v1: rejected because judge prompt/rubric changes
  need an auditable sanity check.

## V1 Implementation Scope

**Decision**: Implement the scoring core first: deterministic gates, budgeted
judge calls, scored/unscored records, summaries, resume compatibility, and
append-only review event formats. Calibration and review event handling should
be contract-ready in v1, but rich calibration and review command UX can be
deferred unless immediately needed.

**Rationale**: gmuse needs practical maintainer eval evidence, not a general eval
platform. Keeping v1 focused reduces implementation risk while preserving stable
artifact shapes for calibration and manual review when those workflows become
useful.

**Alternatives considered**:

- Build full calibration and review commands immediately: rejected as likely
  overbuilt for the first usable scoring slice.
- Remove calibration and manual review from artifacts: rejected because later
  baseline promotion and comparison need to preserve whether scoring was
  calibrated and whether human overrides affected effective scores.
