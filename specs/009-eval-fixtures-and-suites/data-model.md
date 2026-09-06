# Data Model: Understandable Eval Fixtures And Suites

**Schema version**: 2.0

## Asset identities

Every checked-in asset declares `schema_version = "2.0"`, a stable `id`,
and its applicable version or revision. A direct migration replaces schema 1.0;
the loader rejects unknown versions and does not infer the new semantics from
legacy fields.

## EvalFixture and FixtureProvenance

`EvalFixture` continues to reconstruct one staged change. Its stable fields
are `id`, `revision`, `origin`, `provenance`, `ecosystem`,
`change_type`, safety/injection tags, base files, patch, expected changed
paths and digest, optional history and context, and selection rationale.

`FixtureProvenance` continues to distinguish real, adapted, and synthetic
content; source-license evidence is distinct from redistribution review.
Fixture schema changes are limited to the version migration and terminology
needed for composition reporting.

## ScoringProfile

A reusable, versioned description of how future subjective assessment works.

| Field | Meaning |
|---|---|
| `id` | Stable profile identifier, initially `commit-message-v1` |
| `version` | Profile contract version |
| `dimensions` | Ordered subjective dimensions |
| `usability_labels` | Definitions for usable, minor edit, major edit, unusable |
| `usability_examples` | Annotated illustrations of intermediate labels |

Each dimension has:

| Field | Meaning |
|---|---|
| `id` | Stable key used by case guidance and later scorers |
| `label` | Maintainer-facing name |
| `description` | What the dimension assesses |
| `anchors` | Exactly four explicit meanings, keyed 1 through 4 |

Initial dimensions are `accuracy`, `message_quality`, and
`style_context_fit`. A case may mark a dimension not applicable when it does
not supply relevant context; a future scorer must preserve that state rather
than invent a rating.

The profile does not define weights or an aggregate score.

## CaseAssessmentGuidance

A versioned, case-specific application of one scoring profile. It is stored in
the existing `evals/rubrics/` directory but is not a list of loose concepts.

| Field | Meaning |
|---|---|
| `id` / `revision` | Stable case-guidance identity |
| `scoring_profile_id` | Referenced profile |
| `criteria` | Independently assessable positive or required evidence |
| `failure_conditions` | Specific undesirable behavior or claim |
| `deterministic_gates` | Objective checks and their evidence configuration |
| `examples` | Two annotated messages for the case |
| `notes` | Optional maintainer context that does not replace a criterion |

A criterion contains `id`, `dimension`, `description`, and importance
(`major` or `minor`). A failure condition contains `id`,
`error_category`, `description`, and severity (`major` or `minor`).
Each reference must use a profile dimension or supported error category.

A deterministic-gate declaration contains `id`, `gate`, and objective
evidence configuration. Supported gates are production output validity,
applicable length, known fake-secret leakage, and configured literal injection
markers. It cannot claim semantic instruction obedience.

Each example contains a message, expected ratings for applicable profile
dimensions, expected usability, expected gate/failure identifiers, and a
rationale. Every checked-in guidance asset has exactly two examples: one usable
example and one important failure. The profile supplies the intermediate-label
illustrations. Examples are calibration evidence, never exact-match targets.

## EvalCase

An `EvalCase` still binds one fixture to one case-assessment-guidance asset
and generation context. `rubric_id` is replaced by
`assessment_guidance_id`. Existing formats, history depth, branch inclusion,
hint, maximum length, and tags remain case configuration.

## EvalSuite and CompositionGoal

An `EvalSuite` contains ordered case IDs and zero or more composition goals.

A `CompositionGoal` contains:

| Field | Meaning |
|---|---|
| `selector` | One supported scenario selector |
| `value` | A permitted value for that selector |
| `minimum_cases` | Positive minimum number of matching cases |
| `severity` | `required` or `advisory` |

Supported selectors are:

- `fixture.origin`, `fixture.ecosystem`, `fixture.change_type`
- `fixture.source_repository`
- `case.format`
- `context.history`, `context.branch`, `context.hint`,
  `context.max_chars`
- `safety.scenario`, `safety.tag`, `safety.injection_pattern`, and
  `safety.injection_location`

Boolean context selectors use `enabled` or `disabled`; `safety.scenario`
uses `ordinary` or `injection`. A matching case counts once for one goal,
even when it contributes multiple values to other goals. Duplicate or
conflicting goals are invalid.

Smoke remains a subset of core. Its goals are intentionally minimal. Core can
add advisory or required goals as curation expands.

## SuiteComposition and ValidationReport

`SuiteComposition` is a report-only summary of resolved cases. It consists of
ordered groups and entries:

| Group | Example entries |
|---|---|
| Changes | `docs: 1 case`, `test: 1 case` |
| Output formats | `conventional: 2 cases` |
| Context variations | `commit history enabled: 1 case` |
| Safety scenarios | `ordinary change: 1 case`, `direct instruction in code comment: 1 case` |
| Fixture sources | `synthetic: 2 cases` |

Each entry has a stable machine key, human label, and case count. Empty or
unresolved records do not fabricate an `none` entry.

`ValidationReport` keeps status, errors, warnings, timestamp, and
`suite_composition`. Composition is separate from validation success and is
never a model score or metric.

## Relationships and lifecycle

```text
EvalSuite ──contains──> EvalCase ──uses──> EvalFixture
                         │
                         └──uses──> CaseAssessmentGuidance ──uses──> ScoringProfile
ValidationReport ──summarizes──> resolved cases + composition goals
```

A source asset revision changes the corresponding stable identity/digest used
by later runner and scorer work. Feature 010 resolves the source assets into a
canonical assessment target and immutable evidence reference. Feature 012
later emits named ratings and gate results; it does not change source assets.
