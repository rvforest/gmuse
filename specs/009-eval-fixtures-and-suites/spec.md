# Feature Specification: Understandable Eval Fixtures And Suites

**Feature Branch**: `009-eval-fixtures-and-suites`

**Created**: 2026-06-11

**Revised**: 2026-09-06

**Status**: Revised — ready for clarification and planning

**Input**: Revise the maintainer-only evaluation-fixture foundation so its
reports and reviewable data are understandable to maintainers who are new to
LLM evaluation. Treat the earlier schema as changeable: use established
evaluation practices for transparent composition reporting, explicit scoring
criteria, deterministic gates, and calibration-ready examples.

## Clarifications

### Session 2026-09-06

- Q: What should the first scoring profile report for subjective quality? → A:
  Use four anchored ratings for each subjective dimension plus a categorical
  usability result; defer any aggregate score.
- Q: Where should explicit suite-composition goals apply first? → A: Give the
  smoke suite only minimal required scenarios; apply explicit composition goals
  to the core suite as it grows.
- Q: How should severe injection obedience be handled before judge scoring
  exists? → A: The foundation validates only objective injection evidence;
  semantic instruction obedience is assessed later by a judge.
- Q: Which usability categories should the first scoring profile use? → A:
  `usable`, `minor_edit`, `major_edit`, and `unusable`.
- Q: How much example data should each checked-in case require? → A: Two
  annotated examples per case: one `usable` outcome and one important failure;
  the shared scoring profile illustrates intermediate categories.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand a validated suite at a glance (Priority: P1)

As a gmuse maintainer who is new to evaluation tooling, I want the validation
report to explain what kinds of cases a suite contains in plain language so that
I can tell whether the suite exercises the situations I care about without
having to inspect its data files or learn internal terminology.

**Why this priority**: A report that passes validation but does not communicate
what the suite represents cannot support informed review or high-level product
guidance.

**Independent Test**: Validate the checked-in smoke suite and confirm that a
reader can identify the number of cases by change type, output format, context
variation, safety scenario, and fixture source from the report alone.

**Acceptance Scenarios**:

1. **Given** a suite containing both history-enabled and history-disabled
   cases, **When** a maintainer validates it, **Then** the report presents each
   state with its case count rather than presenting the two states as an
   unexplained comma-separated pair.
2. **Given** a suite containing normal and injection-safety cases, **When** a
   maintainer validates it, **Then** the report groups the scenarios under
   clear, human-readable headings and identifies the injection pattern and
   location where applicable.
3. **Given** a valid suite, **When** validation completes, **Then** the report
   calls this information suite composition and clearly distinguishes it from
   validation status and model-quality results.
4. **Given** an invalid fixture or suite reference, **When** validation
   completes, **Then** its actionable errors remain visible alongside any
   available composition summary without implying that the suite passed.

---

### User Story 2 - Author a rubric that explains future scoring (Priority: P1)

As a gmuse maintainer, I want to read a case's evaluation guidance and predict
how several plausible commit messages would be assessed so that I can review
or author evaluation data with confidence before automated scoring exists.

**Why this priority**: A list of vague required or forbidden concepts does not
provide a usable mental model for a future human or model-based grader.

**Independent Test**: Review a checked-in ordinary case and a safety case,
then use their scoring guidance to classify representative messages as passing
or failing deterministic gates and to explain their expected assessment without
requiring an exact match to an example message.

**Acceptance Scenarios**:

1. **Given** a case with subjective quality expectations, **When** a maintainer
   reads its evaluation guidance, **Then** they can identify the reusable
   assessment dimensions, the meaning of each rating level, and the case-
   specific evidence that affects each dimension.
2. **Given** a generated message that violates an objective safety, format,
   privacy, or length constraint, **When** it is assessed in a future scoring
   run, **Then** the guidance identifies it as a deterministic gate rather than
   concealing it inside a subjective quality score.
3. **Given** a case-specific success criterion or failure condition, **When**
   a maintainer reads it, **Then** it states the observable behavior, the
   assessment dimension or error category it affects, and its importance.
4. **Given** annotated example messages, **When** a maintainer uses them for
   guidance, **Then** each example includes an expected assessment and rationale
   but does not require generated messages to match its wording.

---

### User Story 3 - Curate suites with meaningful composition goals (Priority: P2)

As a gmuse maintainer, I want a suite to express which specific scenarios need
representation so that the small smoke suite stays useful and the future core
suite can become balanced without misleading generic coverage rules.

**Why this priority**: A policy that merely confirms that a field has any value
does not show whether a suite contains the cases needed for regression or
safety confidence.

**Independent Test**: Validate a suite with value-specific composition goals and
confirm that the report shows counts for the requested scenarios, warns or
fails at the documented threshold, and does not treat an inapplicable value as
evidence that a requested scenario is represented.

**Acceptance Scenarios**:

1. **Given** a composition goal requiring a minimum number of cases with a
   particular context setting or safety scenario, **When** the suite falls below
   that threshold, **Then** validation identifies the missing scenario, the
   observed count, and the required count.
2. **Given** an advisory composition goal, **When** the suite falls below its
   threshold, **Then** validation warns by default and the maintainer can elect
   to treat the warning as a failure.
3. **Given** a smoke suite, **When** validation runs, **Then** it remains a
   subset of the core suite and can use a deliberately small set of
   composition goals.
4. **Given** a value such as "not applicable" or "not used", **When** a
   composition goal asks for a different value, **Then** the former does not
   satisfy the goal.

### Edge Cases

- A suite has no resolved cases because its selected graph is invalid; the
  report must not present empty or placeholder values as meaningful composition.
- A case exercises multiple output formats; its report must show the count for
  each format without implying that the formats are mutually exclusive.
- A case has no safety scenario; the report must communicate that it is an
  ordinary case without treating "none" as safety coverage.
- A criterion cannot be evaluated from the staged change and permitted case
  context; validation must reject or flag it as unsuitable for reliable
  assessment.
- An example message is high quality but uses different wording from another
  valid message; the rubric must allow both rather than treating examples as
  golden answers.
- A message passes every objective gate but is vague, inaccurate, or poorly
  scoped; its subjective assessment must remain visible.
- A message receives strong subjective ratings but violates a hard gate; the
  hard gate must take precedence.
- Fixture reconstruction, provenance, path, digest, and reference failures
  continue to be reported with actionable diagnostics.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The evaluation foundation MUST define versioned, reviewable
  fixture, case, suite, and assessment-guidance data.
- **FR-002**: Fixtures MUST remain offline and self-contained after they are
  checked in.
- **FR-003**: Fixture validation MUST reconstruct an isolated repository,
  stage the evaluated changes, and verify that the staged-change identity
  matches fixture metadata.
- **FR-004**: Fixtures MUST preserve original changed file paths and MUST NOT
  pre-truncate evaluated changes.
- **FR-005**: Real open-source fixtures MUST record sufficient source,
  licensing, and redistribution-review information for maintainers to audit
  their provenance; this record MUST NOT claim legal approval.
- **FR-006**: Synthetic fixtures MUST be explicitly identified as synthetic,
  and adapted fixtures MUST explain their adaptation.
- **FR-007**: Validation reports MUST label the distribution of scenarios in a
  suite as **suite composition**, not coverage.
- **FR-008**: A suite-composition report MUST group information into
  understandable categories, including changes, output formats, context
  variations, safety scenarios, and fixture sources when present.
- **FR-009**: Each composition entry MUST show how many cases it represents.
  The report MUST NOT rely on unexplained raw status values or comma-separated
  sets to communicate mutually different case states.
- **FR-010**: Suite composition MUST be reported separately from validation
  status, validation errors, and future model-quality results.
- **FR-011**: A suite MAY define composition goals only for a specific scenario
  value and a minimum number of cases. A generic requirement that a category
  merely have any value is insufficient.
- **FR-012**: Composition goals MUST identify whether falling short is required
  or advisory. Advisory shortfalls MUST be visible by default and may be
  promoted to failures by maintainer choice. The smoke suite MUST use only
  minimal required scenarios; the core suite is the first suite expected to use
  explicit composition goals as it grows.
- **FR-013**: Suite definitions MUST support smoke, core, and safety membership
  without duplicating fixture content. The smoke suite MUST remain a subset of
  the core suite.
- **FR-014**: Assessment guidance MUST distinguish reusable scoring rules from
  the expectations that are specific to one case.
- **FR-015**: Reusable scoring rules MUST define each subjective assessment
  dimension, explain every rating level, and state how individual assessments
  are presented to maintainers. The first profile MUST use a four-level,
  anchored rating for each subjective dimension and a separate categorical
  usability result: `usable`, `minor_edit`, `major_edit`, or `unusable`.
- **FR-016**: Case-specific assessment guidance MUST use independently
  assessable criteria and failure conditions. Each item MUST state the
  observable behavior, its affected dimension or error category, and its
  importance.
- **FR-017**: Objective constraints that can be reliably checked without
  subjective judgment—including applicable output validity, length, privacy,
  and objective injection evidence—MUST be represented as deterministic gates
  separate from subjective assessments. Semantic instruction obedience is
  deferred to later judge scoring.
- **FR-018**: A failed deterministic gate MUST prevent a result from being
  considered usable regardless of subjective assessment. The foundation MUST
  preserve the gate and its evidence for later review.
- **FR-019**: Assessment guidance MUST support annotated examples that include
  an expected assessment and rationale. Examples MUST illustrate acceptable and
  unacceptable outcomes without becoming exact-match targets. Each checked-in
  case MUST include two examples: one `usable` outcome and one important
  failure. The reusable scoring profile MUST illustrate intermediate usability
  categories.
- **FR-020**: The foundation MUST validate fixture and suite structure,
  references, provenance, reconstructability, staged-change identity, and
  suitability of declared assessment guidance for later scoring.
- **FR-021**: Injection-safety cases MUST identify both the instruction pattern
  and the location in which it appears. Secret-like safety test data MUST be
  explicitly marked fake or nonfunctional. The foundation MUST validate only
  objective injection evidence, not infer semantic instruction obedience.
- **FR-022**: The foundation MUST provide enough structured information for a
  later evaluation runner and scorer to apply the same assessment guidance
  consistently without redefining its meaning.
- **FR-023**: This feature MUST NOT make live candidate-model or judge-model
  calls, produce model-quality scores, calculate a composite score, compare
  baselines, import fixtures over a network, or publish benchmark
  recommendations.
- **FR-024**: Default continuous integration MUST NOT require provider
  credentials or live evaluation execution for this foundation.

### Key Entities *(include if feature involves data)*

- **EvalFixture**: Offline source data that reconstructs the repository state
  and staged change to be evaluated.
- **EvalCase**: A runnable scenario that combines a fixture with requested
  output formats and context variations.
- **EvalSuite**: A named collection of case IDs and optional, value-specific
  composition goals.
- **Composition Summary**: A readable count of the scenarios represented by a
  suite, grouped by their purpose rather than presented as raw metadata.
- **Scoring Profile**: A versioned, reusable description of subjective
  assessment dimensions, their four rating-level meanings, and the separate
  categorical usability result (`usable`, `minor_edit`, `major_edit`, or
  `unusable`). It describes how a future scorer will assess messages but does
  not itself run scoring.
- **Case Assessment Guidance**: Independently assessable criteria, failure
  conditions, deterministic gates, and annotated examples that apply a scoring
  profile to one evaluation case.
- **Deterministic Gate**: An objective requirement whose failure makes an
  output unusable regardless of subjective assessment.
- **Fixture Provenance**: Attribution and origin information for real, adapted,
  or synthetic fixture content.
- **Validation Report**: A maintainer-facing result that separately presents
  validation status, actionable errors, and suite composition.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can validate the checked-in smoke suite in under 30
  seconds on a typical development machine without provider credentials.
- **SC-002**: The smoke-suite report identifies the count for every represented
  change type, output format, context variation, safety scenario, and fixture
  source without requiring the reader to inspect asset files.
- **SC-003**: For every declared composition goal, validation reports the
  requested scenario value, observed case count, required case count, and
  whether the result is advisory or required.
- **SC-004**: Every checked-in case assessment guide identifies its scoring
  profile, and every criterion or failure condition identifies its affected
  dimension or error category and importance.
- **SC-005**: Every checked-in case includes two annotated examples: one
  `usable` outcome and one important failure. Each example includes an expected
  assessment and rationale, and validation accepts semantically valid messages
  that do not exactly match example wording.
- **SC-006**: Validation detects 100% of checked-in fixture provenance,
  reconstruction, staged-change identity, suite-reference, and deterministic-
  gate metadata failures.
- **SC-007**: Later runner and scoring work can consume the versioned fixture,
  case, suite, scoring-profile, and assessment-guidance identities without
  redefining their semantics.

## Assumptions

- Eval assets are maintainer-only and do not change the ordinary `gmuse`
  command workflow.
- The checked-in smoke suite remains intentionally small and may contain only
  synthetic fixtures while real open-source cases are curated. It has minimal
  composition requirements; core-suite composition goals expand with the
  curated corpus.
- The immediate purpose of a scoring profile and case assessment guidance is to
  make future scoring understandable and consistent; execution of an automated
  scorer is deferred to a later feature.
- Human review and calibration examples are the reference point for future
  model-based grading. Automated grading is not assumed to replace maintainer
  judgment.
- Semantic judgments about whether an output obeyed embedded instructions are
  deferred to the future judge-scoring feature; this foundation only preserves
  the structured safety evidence that the judge will need.
- Aggregate or weighted quality scores are deferred until calibration shows
  that individual assessments are useful and trustworthy.
- Because these are maintainer-only, pre-release schemas, existing checked-in
  assets may be migrated directly rather than preserving an obsolete contract.
- Existing gmuse staged-change behavior remains the source of truth once a
  fixture is reconstructed.
