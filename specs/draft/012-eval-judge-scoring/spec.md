# Feature Specification: Eval Judge And Scoring

**Feature Branch**: `012-eval-judge-scoring`
**Created**: 2026-06-11
**Status**: Draft

**Draft Note**: This specification describes proposed maintainer-only eval
tooling. It does not describe current gmuse behavior.

**Framework Alignment Update (2026-06-14)**: Adopt Inspect AI scorers/logs for
judge execution and score recording when the spike confirms fit. gmuse owns
deterministic hard gates, rubric definitions, and score metadata requirements.
Custom `scored-records.jsonl` and `judge-records.jsonl` artifacts are no longer
the preferred source of truth.

**Input**: User description: "Draft the Speckit design artifacts for eval judge scoring."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gate unsafe or invalid outputs before scoring (Priority: P1)

As a maintainer reviewing eval results, I want deterministic checks to identify
hard failures before any subjective judging so unsafe, invalid, or structurally
unusable messages cannot receive a passing result from a high judge score.

**Why this priority**: Hard failures define the minimum trust boundary for evals.
The scoring feature is not useful unless privacy leaks, severe injection
obedience, and production validation failures are handled consistently.

**Independent Test**: Run scoring against saved runner outputs containing known
privacy leaks, injection-following text, invalid structure, and `max_chars`
violations; verify each output is marked as hard failed before judge scoring can
make it usable.

**Acceptance Scenarios**:

1. **Given** a runner output that failed production validation, **When** scoring
   is applied, **Then** the output receives a hard failure gate and remains
   inspectable with the original generated message and validation details.
2. **Given** a runner output that includes a fake secret from the fixture,
   **When** deterministic privacy checks run, **Then** the output is categorized
   as a privacy hard failure regardless of later judge scores.
3. **Given** a runner output that follows an instruction embedded in the diff,
   **When** deterministic and judge scoring complete, **Then** severe injection
   obedience is recorded as a hard failure and prevents a usable result.

---

### User Story 2 - Score outputs with a fixed judge and rubric (Priority: P1)

As a maintainer comparing candidate model outputs, I want each eligible output
judged against the same rubric, judge prompt, judge model, and parameters so
results are comparable across models and cases.

**Why this priority**: LLM-as-judge results are only useful if the judge setup is
stable, recorded, and tied to the case rubric rather than to ad hoc review.

**Independent Test**: Score a completed eval run with a fixed judge
configuration and verify each scored output contains structured per-dimension
scores, rationales, judge metadata, rubric version, and self-judge flags.

**Acceptance Scenarios**:

1. **Given** completed runner output records from the production-path eval
   runner, **When** a maintainer starts scoring with an explicit judge
   configuration and call budget, **Then** the system judges each eligible output
   using one fixed judge setup for that scoring run.
2. **Given** a candidate output for a case with required and forbidden concepts,
   **When** the judge scores it, **Then** the result includes accuracy, quality,
   usability, error categories, and concise dimension-specific rationales.
3. **Given** the judge model is the same as the candidate model for an output,
   **When** scoring records the result, **Then** the result is flagged as
   self-judged and unsuitable for strong recommendation claims.

---

### User Story 3 - Calibrate judge behavior before relying on scores (Priority: P2)

As a maintainer changing judge prompts or rubrics, I want to run the judge
against manually annotated calibration examples so I can catch obvious rubric,
parse, self-preference, verbosity, or ordering issues before treating scores as
regression evidence.

**Why this priority**: LLM judges can be useful, but published research shows
they can exhibit position, verbosity, and self-enhancement bias. Calibration is
the lightweight maintainer control that keeps judge changes auditable.

**Independent Test**: Run scoring calibration against a small set of manually
annotated outputs and verify the report records expected labels, judge labels,
agreement, parse failures, and any bias-control settings used.

**Acceptance Scenarios**:

1. **Given** calibration examples with maintainer-provided expected usability and
   hard-failure labels, **When** calibration runs, **Then** the report compares
   judge output to those labels and records agreement by dimension.
2. **Given** a judge prompt or rubric version changes, **When** scoring starts
   for a benchmarkable run, **Then** the run records whether calibration was run
   for that judge configuration.
3. **Given** pairwise judge comparison is enabled in a future extension, **When**
   calibration includes pairwise examples, **Then** the system must support
   order-swapped or randomized candidate presentation to detect position bias.

---

### User Story 4 - Preserve manual review and overrides (Priority: P2)

As a maintainer auditing eval results, I want to add annotations and overrides
without losing the original deterministic and judge outputs so future reviewers
can distinguish automated scoring from human correction.

**Why this priority**: Eval quality depends on reviewer trust. Manual overrides
are necessary when a judge is wrong, but they must be transparent and reversible.

**Independent Test**: Add a manual annotation and override to a scored output and
verify the original judge output, original deterministic gates, override reason,
reviewer identifier, and timestamp remain available.

**Acceptance Scenarios**:

1. **Given** a scored output with a questionable judge decision, **When** a
   maintainer records an override, **Then** the final effective score reflects
   the override while preserving the original automated result.
2. **Given** a scored output that needs reviewer context but no score change,
   **When** a maintainer adds an annotation, **Then** the annotation is attached
   without changing the effective score or hard failure status.

---

### User Story 5 - Review scoring failures separately from model quality (Priority: P3)

As a maintainer running live evals, I want judge provider failures and parse
errors recorded separately from candidate output errors so operational problems
do not look like poor model quality.

**Why this priority**: Live evals can fail because of auth, rate limits, network
issues, timeouts, or judge response formatting. Those failures must be resumable
and diagnosable without contaminating quality scores.

**Independent Test**: Simulate judge auth, timeout, rate limit, empty response,
and structured-output parse failures; verify each is recorded as an operational
scoring failure and can be resumed according to the live-run budget rules.

**Acceptance Scenarios**:

1. **Given** a judge call times out, **When** scoring records the outcome, **Then**
   the affected output has a judge operational error and no fabricated rubric
   score.
2. **Given** scoring is resumed after an interruption, **When** previously scored
   outputs are present and compatible, **Then** completed scoring records are
   skipped and remaining judge calls stay within the explicit budget.

### Edge Cases

- Outputs with hard failures must still preserve deterministic check details,
  original generated text, and any judge output that was already captured.
- `max_chars` must be counted the same way as production validation and must be a
  hard failure only for cases where the limit applies.
- Wrong or suboptimal conventional commit type is an accuracy or quality issue,
  not a safety hard failure.
- Candidate operational errors from the runner must not be sent to the judge as
  if they were generated commit messages.
- Judge structured-output parse failures must be recorded as judge operational
  errors, not as model quality failures.
- Self-judged results must remain usable for local inspection but must be
  clearly flagged as limited evidence.
- Candidate model/provider identity should be hidden from judge prompts unless
  it is needed for an explicit diagnostic mode; self-judge flags are computed by
  scoring metadata, not by asking the judge to account for model identity.
- If future pairwise judge scoring is added, position/order controls must be
  recorded with judge output.
- Manual overrides must never delete or mutate the original judge output.
- Scoring must reject or warn on incompatible runner artifact schema, suite
  version, rubric version, judge prompt version, or judge configuration changes
  according to compatibility rules.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST score completed Inspect sample results produced by
  the production-path eval runner from spec 010.
- **FR-002**: The system MUST use live-run guardrails, explicit confirmation, and
  Inspect/gmuse limits from spec 011 for live judge calls.
- **FR-003**: The system MUST run deterministic checks before LLM judge scoring
  wherever a check can be decided without subjective semantic evaluation.
- **FR-004**: The system MUST treat privacy leaks, severe injection obedience,
  production validation failures, and applicable `max_chars` violations as hard
  failure gates.
- **FR-005**: A hard failure gate MUST prevent an output from being considered
  usable, regardless of any numeric judge score or aggregate score.
- **FR-006**: The system MUST preserve per-dimension scoring even when an
  aggregate score is computed.
- **FR-007**: The system MUST score accuracy and commit message quality using a
  documented numeric rubric.
- **FR-008**: The system MUST classify usability using categories that include at
  least `usable`, `minor_edit`, `major_edit`, and `unusable`.
- **FR-009**: The system MUST record a versioned quality/compliance error
  taxonomy with at least `format_error`, `accuracy_error`, `hallucination`,
  `vague`, `too_verbose`, `wrong_scope`, `wrong_conventional_type`,
  `injection_followed`, `privacy_leak`, `extra_output`, `validation_error`, and
  `other`.
- **FR-010**: The system MUST record judge and provider operational failures
  separately from quality/compliance errors, including at least `auth_error`,
  `rate_limit`, `timeout`, `network_error`, `context_length`, `empty_response`,
  `judge_parse_error`, and `unknown_error`.
- **FR-011**: The system MUST use one fixed judge model, judge prompt version,
  rubric version, and judge parameter set for all comparable candidate outputs in
  a scoring run.
- **FR-012**: The system MUST record judge model, judge provider, judge prompt
  version, rubric version, parameters, timestamps, and structured judge output
  with each scored result.
- **FR-013**: The system MUST flag any result where the judge model and candidate
  model are the same or otherwise declared equivalent for self-judging purposes.
- **FR-014**: The judge input MUST use the raw staged diff and case rubric as
  primary evidence, plus only the case context needed to evaluate the generated
  message.
- **FR-015**: Judge prompts SHOULD hide candidate model/provider identity unless
  an explicit diagnostic mode records why identity is included.
- **FR-016**: The judge MUST NOT require exact match to an original source commit
  message or example good message.
- **FR-017**: The system MUST support a calibration mode for judge prompt and
  rubric versions using manually annotated examples.
- **FR-018**: Calibration output MUST record expected labels, judge labels,
  agreement by dimension, parse failures, judge configuration, rubric version,
  and whether model identity was hidden from the judge.
- **FR-019**: If pairwise judge comparisons are supported, the system MUST record
  candidate ordering and MUST support order-swapped or randomized presentation
  for calibration and bias checks.
- **FR-020**: The system MUST support manual annotations and pass/fail or score
  overrides while preserving original deterministic checks and original judge
  output.
- **FR-021**: Manual overrides MUST include reviewer identity or label,
  timestamp, changed fields, and rationale.
- **FR-022**: Scoring metadata in Inspect logs MUST preserve the source runner
  identifiers needed to trace each score back to the spec 010 Inspect sample
  result, including suite, case, fixture, model, generation config, prompt hash,
  and generated message.
- **FR-023**: The system MUST reject or clearly mark unscored records when
  candidate generation failed operationally before a generated message existed.
- **FR-024**: The system MUST make aggregate scores secondary by documenting
  weights and never hiding hard failure gates or per-dimension scores.
- **FR-025**: The system MUST be maintainer-only tooling and MUST NOT require
  provider credentials in default CI.

### Key Entities *(include if feature involves data)*

- **Inspect Sample Result**: A completed candidate generation result from spec
  010, including case identity, generated message, production validation outcome,
  prompt/context metadata, model metadata, and operational status.
- **Scored Sample Result**: An Inspect sample result enriched with deterministic
  checks, judge result, hard failure gates, error categories, effective scores,
  and scoring metadata.
- **Deterministic Check Result**: A non-LLM evaluation of format, validation,
  privacy, injection, or length constraints where objective evidence exists.
- **Judge Configuration**: The fixed judge model, provider, prompt version,
  rubric version, parameters, and budget metadata used for a scoring run.
- **Judge Calibration Report**: Maintainer-facing artifact comparing judge
  output against manually annotated examples for one judge configuration.
- **Judge Result**: Structured LLM-as-judge output with per-dimension scores,
  usability, error categories, rationales, and raw response metadata.
- **Manual Annotation**: Reviewer-supplied note attached to a scored output.
- **Manual Override**: Reviewer-supplied replacement for selected effective
  scores, gates, or categories with rationale and audit metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In validation fixtures, 100% of known privacy leaks, severe
  injection-following outputs, production validation failures, and applicable
  `max_chars` violations are recorded as hard failures.
- **SC-002**: In scoring runs with a fixed judge configuration, 100% of scored
  outputs include judge metadata sufficient to identify the judge model, prompt
  version, rubric version, and parameters used.
- **SC-003**: In scored artifacts, 100% of outputs preserve per-dimension scores
  and hard failure gates even when an aggregate score is present.
- **SC-004**: In simulated operational-failure tests, 100% of judge auth, rate
  limit, timeout, network, empty response, and parse failures are recorded as
  operational errors rather than quality errors.
- **SC-005**: In manual review tests, 100% of annotations and overrides preserve
  the original automated result and include reviewer, timestamp, and rationale
  metadata.
- **SC-006**: In calibration tests, 100% of judge prompt or rubric versions can
  be evaluated against manually annotated examples and produce agreement and
  parse-failure counts before being used for promoted regression evidence.

## Assumptions

- Specs 010 and 011 define the runner artifact shape and live-call budgeting
  behavior; this feature consumes those outputs rather than redefining them.
- The initial scoring flow targets absolute rubric scoring for maintainer review
  and regression analysis only.
- Baseline promotion/comparison, fixture importing, and public benchmark
  recommendations are intentionally out of scope for this feature.
- Exact initial judge model selection can remain configurable as long as each
  scoring run records one fixed judge configuration.
- Judge calibration examples may be small in v1, but they must be stable,
  manually annotated, and versioned with the judge prompt or rubric they assess.
- Eval data and live run artifacts remain maintainer-controlled and are not part
  of normal `gmuse msg` or `gmuse commit` user workflows.
