# Research: Understandable Eval Fixtures And Suites

**Feature**: 009-eval-fixtures-and-suites
**Date**: 2026-09-06

## Decision: Call the suite's make-up “composition,” not “coverage”

**Rationale**: The prior report collected distinct metadata values across the
selected cases and called them coverage. Readers interpreted values such as
`history: not-used, used` as contradictory. In evaluation frameworks, a
per-output scorer produces scores and metrics summarize them; the collection of
cases is separate from both. The maintainer report will therefore present a
grouped suite composition with per-case counts.

**Alternatives considered**:

- Retain `Coverage` and add documentation: rejected because the term remains
  overloaded with code coverage and score metrics.
- Show raw metadata sets with improved labels: rejected because it still hides
  how many cases a value represents.

## Decision: Use value-specific composition goals

**Rationale**: A generic requirement that a dimension be non-empty is satisfied
by values such as `not-used` or `not-applicable`, so it cannot express the
scenario a suite needs. A goal selects one declared scenario value, specifies a
minimum case count, and is either required or advisory. Smoke has only minimal
required scenarios; core gains explicit goals as its curated corpus grows.

**Alternatives considered**:

- Count distinct values per dimension: rejected because that is not a case
  count and does not identify the desired scenario.
- Enforce detailed quotas in smoke: rejected because it would make a
  two-case machinery check artificially broad.

## Decision: Separate scoring profiles from case assessment guidance

**Rationale**: A reusable scoring profile provides common, versioned 1–4 anchors
for subjective dimensions and defines usability labels. Case assessment guidance
then supplies independently assessable criteria, failure conditions,
deterministic-gate declarations, and examples for one fixture/case. This lets a
maintainer predict an assessment without requiring exact wording.

Google's evaluator guidance separates rating rubrics, score/category mapping,
and evaluator inputs, and recommends calibration against trusted human ratings.
Inspect similarly separates per-sample scorers from aggregate metrics and
supports multiple scores. [Google evaluator guidance](https://developers.google.com/stax/evaluators),
[Google evaluation best practices](https://developers.google.com/stax/best-practices),
[Inspect scoring](https://inspect.aisi.org.uk/scoring.html).

**Alternatives considered**:

- Continue `required_concepts` and `forbidden_concepts`: rejected because
  they do not state severity, scoring effect, or decision rule.
- Put all score anchors in every case: rejected because repeated anchors drift.
- Use a one-to-five scale with a weighted aggregate: rejected because the
  project selected four anchored levels and aggregate scoring is uncalibrated.

## Decision: Use four anchored ratings and categorical usability

**Rationale**: The initial profile uses a 1–4 anchored rating for every
subjective dimension and separately reports `usable`, `minor_edit`,
`major_edit`, or `unusable`. No composite score is emitted or required.
Each checked-in case has two examples: one usable outcome and one important
failure. The profile supplies intermediate-category illustrations.

**Alternatives considered**:

- Binary criteria only: rejected because it loses the useful distinction between
  minor and major editing work.
- Weighted aggregate: deferred until calibration establishes that component
  ratings are reliable and interpretable.

## Decision: Keep deterministic gates objective

**Rationale**: Code or heuristic checks are appropriate where a condition is
objectively observable; model judgment is appropriate for subjective semantic
questions. The foundation declares and validates evidence for output validity,
length, known fake-secret leakage, and configured literal injection markers.
It does not infer whether a model semantically obeyed an embedded instruction.
That later judge finding may create a hard gate with `source = judge`.

**Alternatives considered**:

- Classify all injection obedience deterministically: rejected as unreliable
  and outside this offline foundation.
- Defer all safety evidence: rejected because fixture safety data must still be
  reviewable and structured now.

## Decision: Keep source assets framework-neutral; adapt only at the runner boundary

**Rationale**: Feature 009 owns TOML assets and their stable identities. Feature
010 resolves them into an Inspect sample: its target contains canonical
assessment instructions and metadata contains stable profile/guidance identities
and machine-checkable gate configuration. Feature 012 executes deterministic
and judge scorers separately, emitting named ratings and evidence rather than a
hidden aggregate. This preserves a possible future framework change while using
Inspect's dataset, target, metadata, scorer, and metric model. [Inspect
datasets](https://inspect.aisi.org.uk/datasets.html), [Inspect custom
scorers](https://inspect.aisi.org.uk/custom-scorers.html).

**Required downstream alignment**: The runner must preserve a privacy-reviewed,
immutable assessment-evidence snapshot or locator plus its digest. Fixture/case
IDs alone are insufficient after source assets change, while raw prompts must
not be added indiscriminately to ordinary log metadata.

## Decision: Migrate the maintainer asset schema directly to 2.0

**Rationale**: Existing assets and models are pre-release maintainer tooling.
Keeping two incompatible rubric and composition shapes would obscure the
contract and add code with no user value. All checked-in assets migrate together
and unknown schema versions fail validation.

**Alternatives considered**:

- Preserve schema 1.0 indefinitely: rejected because it would retain ambiguous
  report and rubric semantics.
- Infer new guidance from legacy fields: rejected because the legacy fields lack
  required scoring meaning.
