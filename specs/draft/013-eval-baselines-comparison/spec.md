# Feature Specification: Eval Baselines and Comparison

**Feature Branch**: `013-eval-baselines-comparison`
**Created**: 2026-06-11
**Status**: Draft

**Draft Note**: This specification describes proposed maintainer-only eval
tooling. It does not describe current gmuse behavior.

**Input**: User description: "Draft the Speckit design artifacts for eval baseline promotion and comparison. Scope: intentional baseline promotion, baseline artifact shape, same-model regression comparison, optional different-model benchmark comparison, warnings for incompatible versions/configs, pairwise deltas and hard-failure flags. Depend on scored outputs from spec 012 and result artifacts from spec 010. Do not include fixture importer or public recommendation pages."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Promote a reviewed scored run as a baseline (Priority: P1)

As the maintainer, I want to intentionally promote a reviewed eval result into a stable baseline artifact so future prompt, context, validation, and generation-path changes can be compared against known-good evidence.

**Why this priority**: Baselines must be deliberate and reviewable. Regression comparison is only useful if a raw run cannot accidentally become the standard of record.

**Independent Test**: Given a completed result artifact from spec 010 and scored outputs from spec 012, run the baseline promotion flow and verify a baseline artifact is created only after explicit promotion, preserves required comparison fields, and omits debug-only fields by default.

**Acceptance Scenarios**:

1. **Given** a completed scored eval run, **When** the maintainer promotes it with the required explicit baseline metadata, **Then** the system writes a baseline artifact with suite, case, model, config, prompt, judge, judge calibration, score, and generated-message metadata needed for later comparison.
2. **Given** an unscored run or a run with missing required comparison metadata, **When** the maintainer attempts promotion, **Then** the system rejects the promotion with actionable missing-field guidance.
3. **Given** a scored run containing debug-only or transient execution details, **When** the maintainer promotes it without opting into debug retention, **Then** those fields are excluded from the baseline artifact while comparison-critical hashes, metadata, outputs, and scores are preserved.

---

### User Story 2 - Compare a candidate run against the same-model baseline (Priority: P1)

As the maintainer, I want to compare a new scored run against a promoted baseline for the same model so I can inspect regressions, improvements, and hard failures before accepting generation-path changes.

**Why this priority**: Same-model regression review is the core maintainer workflow for this feature and must report evidence instead of hiding differences behind a single aggregate number.

**Independent Test**: Given a baseline and candidate run with matching suite, case, model, config, prompt, judge, and schema metadata, run comparison and verify the report includes pairwise per-case deltas, per-dimension score deltas, hard-failure changes, prompt size/token changes, first-shot success changes, and error category changes.

**Acceptance Scenarios**:

1. **Given** compatible baseline and candidate artifacts for the same model, **When** the maintainer compares them, **Then** the report lists every shared case with baseline result, candidate result, score deltas, failure deltas, and generated-message references.
2. **Given** a candidate case that introduces a new privacy leak, severe injection obedience, or production validation failure, **When** comparison is generated, **Then** the report marks the case with a hard-failure flag regardless of aggregate score.
3. **Given** changes in prompt size, estimated tokens, first-shot success, or error categories, **When** comparison is generated, **Then** those changes are visible both per case and in summary counts.

---

### User Story 3 - Warn on incompatible comparison inputs (Priority: P1)

As the maintainer, I want comparison to warn when baseline and candidate artifacts differ in versions, suite definitions, case revisions, model identity, config, prompt version, judge version, or schema shape so I do not mistake an apples-to-oranges comparison for a clean regression result.

**Why this priority**: Eval evidence is only trustworthy when compatibility risks are explicit. Some differences should not block comparison, but they must be visible.

**Independent Test**: Compare artifacts with deliberate differences across suite version, case revision, model metadata, generation config, prompt version, judge metadata, and artifact schema version; verify each difference produces a structured warning with a clear severity.

**Acceptance Scenarios**:

1. **Given** artifacts with a suite or case revision mismatch, **When** comparison is generated, **Then** the report warns that case-level deltas may not be directly comparable and identifies the affected cases.
2. **Given** artifacts with model or generation-config differences in same-model regression mode, **When** comparison is requested, **Then** the report emits a high-severity incompatibility warning and requires the output to be labeled as non-clean regression evidence.
3. **Given** artifacts with different judge prompt, rubric, or schema versions, **When** comparison is generated, **Then** the report warns that score deltas may reflect scoring changes rather than candidate behavior changes.

---

### User Story 4 - Optionally compare different models as a benchmark view (Priority: P2)

As the maintainer, I want an explicit benchmark comparison mode that can compare different model outputs against the same cases so I can inspect relative behavior without treating the result as a regression gate or public recommendation.

**Why this priority**: Different-model comparison is useful for private model selection and reference benchmarking, but it must be clearly separate from same-model regression review.

**Independent Test**: Given compatible scored outputs for two different models over the same suite, run benchmark comparison mode and verify the report allows different model metadata, still warns on suite/config/judge mismatches, and does not produce accept/reject decisions or public recommendations.

**Acceptance Scenarios**:

1. **Given** two scored runs for different models over the same case set, **When** benchmark comparison mode is selected, **Then** the report shows pairwise deltas and hard-failure flags while clearly labeling the comparison as different-model benchmark evidence.
2. **Given** a model with privacy or severe injection hard failures, **When** benchmark comparison is generated, **Then** the report flags those failures and does not present the model as recommended.
3. **Given** a maintainer requests benchmark comparison without selecting benchmark mode, **When** model metadata differs, **Then** the system warns or rejects according to the requested mode rather than silently treating it as a same-model regression.

---

### Edge Cases

- Promotion is attempted from result artifacts that exist but do not include scored outputs from spec 012.
- Promotion is attempted from partial, interrupted, or resumed runs with incomplete case coverage.
- Candidate and baseline include overlapping but non-identical case sets.
- A case has a score improvement but introduces a new hard failure.
- A candidate removes a previous hard failure but regresses accuracy or quality scores.
- Judge metadata changes while generated outputs are otherwise identical.
- Judge calibration metadata is present in one artifact but absent or different
  in the other.
- Prompt hashes match but prompt size or token estimates differ because instrumentation changed.
- Same model name appears with different provider, revision, endpoint, or resolved model metadata.
- Optional debug retention is requested for promotion even though baseline artifacts default to stripped debug fields.
- Operational failures such as timeouts and rate limits appear in one artifact but not the other.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an intentional baseline promotion flow that creates a baseline artifact only from an explicitly selected eval result artifact.
- **FR-002**: The promotion flow MUST require scored outputs from spec 012 and result artifact metadata from spec 010 before a baseline can be promoted.
- **FR-003**: The promotion flow MUST reject unscored, incomplete, or schema-incompatible inputs with actionable guidance.
- **FR-004**: A baseline artifact MUST preserve generated messages, score metadata, hard-failure metadata, prompt hashes, prompt size/token metadata, model metadata, generation config metadata, suite metadata, case metadata, judge metadata, judge calibration metadata when available, and artifact schema versions.
- **FR-005**: A baseline artifact MUST strip debug-only and transient execution fields by default while allowing an explicit maintainer choice to retain them when needed for private analysis.
- **FR-006**: The system MUST support same-model regression comparison between a promoted baseline and a candidate scored result.
- **FR-007**: Same-model regression comparison MUST report pairwise per-case baseline-versus-candidate evidence rather than only aggregate summaries.
- **FR-008**: Comparison reports MUST include per-dimension score deltas for accuracy, quality, format/compliance, privacy, injection resistance, usability, and any additional scored dimensions present in the artifacts.
- **FR-009**: Comparison reports MUST include new, removed, and changed hard-failure flags, including privacy leaks, severe injection obedience, and production validation failures.
- **FR-010**: Comparison reports MUST include prompt hash changes, prompt size/token deltas, first-shot success deltas, and error category deltas.
- **FR-011**: Comparison reports MUST preserve per-case baseline and candidate details needed to inspect generated messages, judge rationales, deterministic checks, manual overrides, and operational failures.
- **FR-012**: The system MUST warn when suite version, suite membership, case IDs, case revisions, fixture revisions, model metadata, generation config, prompt version, judge model, judge prompt version, rubric version, judge calibration metadata, scoring schema version, or artifact schema version differ between compared artifacts.
- **FR-013**: Compatibility warnings MUST include a severity and identify whether the comparison remains clean regression evidence, degraded regression evidence, benchmark evidence, or invalid evidence.
- **FR-014**: Same-model regression mode MUST treat model or generation-config differences as high-severity incompatibilities.
- **FR-015**: The system MUST support an explicit optional different-model benchmark comparison mode.
- **FR-016**: Different-model benchmark comparison mode MUST allow model metadata differences while still warning about suite, case, config, prompt, judge, scoring, and schema mismatches.
- **FR-017**: The system MUST NOT produce hardcoded accept/reject decisions beyond hard-failure flags and compatibility severity.
- **FR-018**: The system MUST NOT generate public recommendation pages, provider preference claims, fixture importer behavior, or user-facing model ranking pages as part of this feature.
- **FR-019**: Comparison summaries MUST distinguish quality/compliance failures from operational provider or judge failures.
- **FR-020**: Reports MUST be reproducible from saved artifacts without making live candidate or judge calls.

### Key Entities *(include if feature involves data)*

- **Baseline Promotion Request**: The maintainer's explicit request to convert a completed scored eval result into a baseline artifact, including label, source run, promotion timestamp, and debug retention choice.
- **Baseline Artifact**: A durable snapshot of selected scored outputs and run metadata used as the comparison reference for future evals.
- **Comparison Input Pair**: A baseline artifact and candidate scored result selected for comparison.
- **Compatibility Warning**: A structured warning describing differences that may affect comparability.
- **Pairwise Case Delta**: Per-case comparison record containing baseline outcome, candidate outcome, score deltas, hard-failure changes, prompt/token deltas, first-shot success changes, and error category changes.
- **Comparison Report**: The maintainer-facing artifact summarizing pairwise deltas, warnings, aggregate evidence, and hard-failure flags.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In validation scenarios, 100% of baseline artifacts are created only through an explicit promotion request and never as a side effect of raw eval execution.
- **SC-002**: In contract tests, 100% of required baseline comparison fields are preserved from compatible spec 010 and spec 012 artifacts.
- **SC-003**: In regression comparison tests, 100% of shared cases appear in pairwise output with score deltas, hard-failure changes, prompt/token deltas, first-shot success deltas, and error category changes.
- **SC-004**: In compatibility tests, 100% of configured version/config mismatch categories produce structured warnings with severity and affected scope.
- **SC-005**: In hard-failure tests, any new privacy leak, severe injection obedience, or production validation failure is flagged regardless of aggregate score movement.
- **SC-006**: In offline validation, comparison report generation completes without live model or judge calls for saved artifacts covering at least the smoke and core suite sizes defined by upstream eval specs.

---

## Assumptions

- Spec 010 provides eval result artifacts from production-path runs, including generated outputs, prompt/context metadata, validation outcomes, operational errors, and run summaries.
- Spec 012 provides scored outputs, deterministic checks, judge metadata, hard-failure classifications, manual annotations, and score schema metadata.
- Baseline and comparison tooling is maintainer-only and is not part of the ordinary `gmuse msg` or commit-generation user workflow.
- The default comparison workflow is same-model regression review; different-model comparison is available only through an explicit benchmark mode.
- Saved artifacts contain enough metadata to compare results offline without re-running candidate generation or judge scoring.
- Public benchmark recommendation pages and fixture importing are separate future concerns and are out of scope for this feature.
