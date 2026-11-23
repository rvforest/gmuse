# Research: Eval Fixtures And Suites

**Feature**: 009-eval-fixtures-and-suites
**Date**: 2026-09-06

## Decision: Report suite composition with grouped case counts

**Rationale**: A suite report should tell a maintainer which scenarios it
contains, not expose raw metadata sets. The report groups counted case
contributions under Changes, Output formats, Context variations, Safety
scenarios, and Fixture sources. A case may contribute to multiple groups or
entries; counts make that relationship clear.

Evaluation frameworks distinguish per-output scores from aggregate metrics.
Suite composition is neither: it describes the make-up of the evaluation set.
[Inspect scoring](https://inspect.aisi.org.uk/scoring.html).

## Decision: Use value-specific composition goals

**Rationale**: A composition goal names a particular scenario and the number of
cases required to represent it. It can therefore say that core needs two cases
with enabled history or one direct-instruction safety case. Goals are required
or advisory. Smoke proves the machinery with only minimal required scenarios;
core gains more explicit goals as its curated corpus grows.

## Decision: Use scoring profiles and case rubrics

**Rationale**: A shared scoring profile defines how ratings work across cases.
A case rubric applies that profile to one staged change through independently
assessable criteria, failure conditions, objective gate declarations, and
annotated examples. This lets a maintainer predict how a message would be
assessed without treating an example message as the only correct wording.

Google's evaluator guidance separates rating rubrics, category mapping, and
evaluator inputs, and recommends calibration against trusted human ratings.
Inspect separates per-sample scorers from aggregate metrics and supports
multiple named scores. [Google evaluator guidance](https://developers.google.com/stax/evaluators),
[Google evaluation best practices](https://developers.google.com/stax/best-practices),
[Inspect scorers](https://inspect.aisi.org.uk/scorers.html).

## Decision: Use four anchored ratings and categorical usability

**Rationale**: Each subjective dimension has four explicit anchors, 1 through
4. A separate usability result is one of `usable`, `minor_edit`,
`major_edit`, or `unusable`. The profile does not define a composite score.
Each checked-in case rubric includes one usable example and one important
failure; profile examples illustrate intermediate usability categories.

## Decision: Keep deterministic gates objective

**Rationale**: The foundation can declare and validate objective conditions:
production output validity, applicable length, known fake-secret leakage, and
configured literal injection markers. It does not infer whether a model
semantically followed embedded instructions. Later judge scoring may identify
that behavior and record a judge-sourced hard gate.

This follows the common division between code or heuristic evaluators for
objective conditions and model or human judgment for subjective questions.
[Google evaluation best practices](https://developers.google.com/stax/best-practices).

## Decision: Keep source assets framework-neutral

**Rationale**: Fixtures, profiles, rubrics, cases, and suites are reviewable
source assets independent of an execution framework. The later runner resolves
them into an Inspect sample: a canonical assessment target plus stable metadata
and a privacy-reviewed assessment-evidence reference. The later scoring feature
runs deterministic and judge scorers separately and emits named ratings and
evidence rather than an opaque per-message total.

Inspect supports sample inputs, targets, metadata, custom scorers, multiple
scorers, and separate metrics, which fits this boundary. [Inspect
datasets](https://inspect.aisi.org.uk/datasets.html), [Inspect custom
scorers](https://inspect.aisi.org.uk/custom-scorers.html).
