# Research: Eval Judge And Scoring

**Date**: 2026-06-11
**Feature**: `012-eval-judge-scoring`

## Deterministic Gates Before Judge Scoring

**Decision**: Run deterministic checks before judge scoring for production
validation failures, applicable `max_chars` violations, obvious extra-output
format failures, known fake secret leakage, and strong injection-following
markers that fixtures declare as forbidden output.

**Rationale**: These checks are objective, cheap, and aligned with the eval
requirements. Hard failures must not depend on subjective judge leniency.
Running them first also avoids spending judge budget on outputs that are already
unusable unless the maintainer explicitly asks for diagnostic judge scoring.

**Alternatives considered**:

- Let the judge decide every failure: rejected because privacy and validation
  failures need zero-tolerance gates.
- Only use production validation: rejected because privacy and injection cases
  need fixture/rubric-aware checks beyond generic commit-message validation.

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
history, branch, hints, or repository instructions. The rendered generation
prompt is not primary judge evidence.

**Rationale**: The judge should assess whether the output matches the underlying
change and rubric, not whether it matches the exact prompt wording. Runner
prompt hashes and prompt metadata from spec 010 remain traceability metadata.

**Alternatives considered**:

- Include full rendered prompts by default: rejected because prompts can bias the
  judge toward prompt compliance over diff accuracy and may increase cost.
- Judge only the generated message and expected labels: rejected because
  accuracy cannot be assessed without the diff and rubric.

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
metadata that references scored output identifiers. Overrides produce effective
scores/gates but never mutate original deterministic checks or original judge
results.

**Rationale**: Human correction is useful only when auditable. Append-only
metadata lets maintainers revise interpretation while preserving the automated
evidence that prompted the correction.

**Alternatives considered**:

- Edit scored JSONL records in place: rejected because it destroys provenance.
- Allow annotations only with no score effect: rejected because judge mistakes
  sometimes need corrected effective results for summaries.

## Budgeting And Resume Dependency

**Decision**: Treat judge calls as live calls governed by spec 011. Scoring must
show planned judge call counts, require explicit budgets, write incrementally,
and skip completed compatible scored records on resume.

**Rationale**: Judge calls incur the same cost and interruption risks as
candidate generation calls. Reusing spec 011 behavior keeps live evals explicit
and cost-controlled.

**Alternatives considered**:

- Add separate judge-only budget behavior: rejected because it duplicates spec
  011 concepts.
- Make scoring always offline: rejected because LLM-as-judge integration is in
  scope for this feature.
