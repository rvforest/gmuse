# Feature Specification: Production-Path Eval Runner

**Feature Branch**: `010-eval-runner`
**Created**: 2026-06-11
**Status**: Draft

**Draft Note**: This specification describes proposed maintainer-only eval
tooling. It does not describe current gmuse behavior.

**Input**: User description: "Production-path eval runner only, depending on fixtures/suites from spec 009. Use a local eval framework where it simplifies execution/logging. Do not include custom judge scoring, custom resume budgeting, baseline promotion, importer, or public benchmark recommendations except as out of scope/dependencies."

**Framework Alignment Update (2026-06-14)**: Adopt Inspect AI as the primary
local eval framework candidate for runner execution and logs. gmuse owns fixture
validation/reconstruction and production-path generation; Inspect owns task
execution, sample logging, limits, and native analysis artifacts when the spike
confirms fit. Custom `outputs.jsonl` runner artifacts are no longer the preferred
source of truth.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check an eval run before live provider calls (Priority: P1)

As a maintainer, I want to run a local check of the eval runner before any live
model calls happen so I can verify the selected suite, cases, generation
settings, Inspect logs, and production-path plumbing.

**Why this priority**: Maintainer evals can call paid providers and process sensitive prompt context. The first usable slice must make live execution explicit and reviewable.

**Independent Test**: With a validated fixture suite from spec 009, run the eval
runner in check mode and verify it reports selected cases and generation
settings, reconstructs fixtures, writes Inspect logs, and makes zero
provider calls.

**Acceptance Scenarios**:

1. **Given** a valid suite, **When** the maintainer runs the runner in check mode, **Then** the command lists the cases and generation settings, executes with deterministic local output through an Inspect task, writes Inspect logs, and calls no provider.
2. **Given** a requested suite contains no matching cases, **When** the maintainer runs check mode, **Then** the command fails clearly and writes no completed Inspect sample results.
3. **Given** a fixture cannot be validated by the spec 009 foundation, **When** the maintainer runs check mode, **Then** the runner reports the fixture validation failure and refuses to execute generation for that case.

---

### User Story 2 - Generate outputs through gmuse production behavior (Priority: P1)

As a maintainer, I want the runner to apply each fixture into a temporary git repository and call gmuse through the same production generation behavior used by normal commit-message generation so eval results reflect real product behavior.

**Why this priority**: The runner is valuable only if it evaluates the actual generation path rather than a separate benchmark-only pipeline.

**Independent Test**: Execute the runner against a tiny validated suite with
deterministic local output and verify each case reconstructs staged changes,
uses the production git/context/prompt/validation path, and records the
generated message or validation failure.

**Acceptance Scenarios**:

1. **Given** a valid fixture with staged changes, **When** the runner executes that case, **Then** it reconstructs the repository state, stages the fixture changes, and generates a message using gmuse's production generation behavior.
2. **Given** a case configuration includes format, history depth, branch context, hints, repository instructions, `max_chars`, model, temperature, or token limits, **When** the runner executes the case, **Then** those settings are applied consistently with normal gmuse generation.
3. **Given** the generated output violates production validation, **When** the runner records the case result, **Then** the raw generated message and validation failure are both preserved.

---

### User Story 3 - Inspect durable result logs (Priority: P1)

As a maintainer, I want durable Inspect logs so I can review failures, compare
raw outputs manually, and preserve enough metadata for later scoring or strict
safety comparison work.

**Why this priority**: This slice intentionally excludes judge scoring and baselines, so durable raw artifacts are the handoff point for later eval phases.

**Independent Test**: Run a small suite and verify the Inspect log contains one
sample result per executed case/model/config entry plus suite metadata,
model/config metadata, counts, validation outcomes, prompt hashes, prompt size,
estimated token counts, and operational errors.

**Acceptance Scenarios**:

1. **Given** a run with multiple cases and models, **When** the runner completes, **Then** every executed case/model/config entry has an Inspect sample result.
2. **Given** a provider timeout, authentication failure, context-length failure, or empty response, **When** the runner records the outcome, **Then** the operational error is captured separately from message-quality or validation outcomes.
3. **Given** a completed run, **When** the maintainer opens the Inspect log or gmuse run summary view, **Then** it reports total planned entries, completed entries, validation failures, operational failures, and log locations.

---

### User Story 4 - Keep eval tooling isolated from normal users (Priority: P2)

As a maintainer, I want eval runner commands and dependencies to stay out of ordinary `gmuse msg` use so normal users do not pay for eval-only complexity.

**Why this priority**: Evals are maintainer tooling. They must not change the default user workflow, require provider credentials in default CI, or add runtime dependencies for normal package use.

**Independent Test**: Install/use gmuse normally and verify standard generation commands remain unchanged while eval runner behavior is available only through explicit maintainer-facing commands or development extras.

**Acceptance Scenarios**:

1. **Given** a user runs normal commit-message generation, **When** the eval runner exists, **Then** no eval fixtures, suites, result artifact writing, or eval-only settings affect that workflow.
2. **Given** default automated checks have no provider credentials, **When** tests run, **Then** runner tests can pass without exposing live model calls.

### Edge Cases

- Check mode must never call a provider, even when model credentials are configured.
- Live mode must fail before provider calls unless the maintainer accepts the
  displayed plan and configures Inspect/gmuse spend guardrails such as sample,
  token, cost, time, or concurrency limits.
- A missing, malformed, or unsupported fixture/suite schema from spec 009 must stop the affected run before generation.
- Temporary repositories must be cleaned up after successful and failed cases unless an explicit debug-preserve option is selected.
- A case with no staged diff after reconstruction must fail as an invalid fixture or setup error rather than producing an eval output.
- Prompt hashes and prompt-size metadata must be recorded without requiring raw prompt text to be written by default.
- Raw generated messages must be preserved even when deterministic validation fails.
- Operational provider errors must not be misclassified as format or quality failures.
- The runner must make no baseline-promotion, pass/fail recommendation, or public benchmark claim.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a maintainer-facing eval runner that consumes validated fixtures and suites produced by spec 009.
- **FR-002**: The runner MUST support a check mode that performs fixture/suite resolution, reports the run plan, executes the runner pipeline with deterministic local output through Inspect, writes Inspect logs, and makes no provider calls.
- **FR-003**: The runner MUST reject missing, invalid, or unsupported fixtures and suites before live generation for affected cases.
- **FR-004**: The runner MUST apply each selected fixture into an isolated temporary git repository and stage the fixture changes before generation.
- **FR-005**: The runner MUST use gmuse's production git/context/prompt/generation/validation behavior for message generation, allowing instrumentation only when it does not alter generated behavior.
- **FR-006**: The runner MUST support per-run or per-case generation overrides for format, history depth, branch context, hints, repository instructions, `max_chars`, model, temperature, and token limits when those inputs are available in the fixture/suite contract.
- **FR-007**: The runner MUST record one Inspect sample result for every executed case/model/config entry.
- **FR-008**: Each Inspect sample result MUST preserve or expose run ID, suite ID, fixture/case identity, fixture revision or digest, model/config metadata, generated message when available, production validation outcome, context metadata, prompt hash, prompt size, estimated token count, timing, and operational error details when applicable.
- **FR-009**: The runner MUST preserve invalid model outputs and production validation failures rather than dropping or repairing them.
- **FR-010**: The runner MUST rely on Inspect logs and summaries as canonical execution artifacts while exposing enough gmuse metadata for later strict safety comparison and reporting.
- **FR-011**: The runner MUST separate operational provider/setup failures from deterministic validation outcomes.
- **FR-012**: The runner MUST avoid writing raw prompt text by default while still recording prompt hashes and size metadata.
- **FR-013**: The runner MUST provide an explicit debug/preserve mode for troubleshooting temporary repositories or prompt material, and this mode MUST be opt-in.
- **FR-014**: The runner MUST keep eval functionality out of the normal commit-message generation workflow and default package runtime path.
- **FR-015**: The runner MUST be testable offline with deterministic local output and validated smoke fixtures.
- **FR-016**: The runner MUST NOT perform custom LLM-as-judge scoring, aggregate quality scoring, custom resume accounting, baseline promotion, fixture importing, or public benchmark recommendation generation in this feature.
- **FR-017**: Live execution MUST display planned cases/models and require explicit maintainer confirmation plus configured spend guardrails before provider calls. Exact custom provider-call accounting is not required when Inspect-native limits provide adequate runaway-spend protection.
- **FR-018**: Default repository automation MUST NOT expose a live-call runner path.

### Key Entities *(include if feature involves data)*

- **Eval Run**: A maintainer-initiated execution over one or more suites, cases, models, and generation settings.
- **Run Plan**: The resolved list of case/model/config entries that would execute for a run.
- **Case Execution**: One entry execution that reconstructs a fixture, stages changes, generates a message, validates it, and records the outcome.
- **Inspect Sample Result**: The canonical Inspect log entry representing one case/model/config entry and its generated output, validation result, or operational failure.
- **Run Summary**: Inspect-native run metadata plus gmuse metadata needed to interpret selected cases, validation outcomes, operational errors, and log locations.
- **Operational Error**: A setup or provider failure such as authentication, rate limit, timeout, network, context length, empty response, or unknown execution error.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, check mode completes for the smoke suite with zero provider calls and reports 100% of planned case/config entries.
- **SC-002**: For a validated smoke suite using deterministic local output, 100% of selected case/config entries produce exactly one Inspect sample result.
- **SC-003**: In controlled tests, 100% of production validation failures preserve both the raw generated message and the validation error category in the Inspect log.
- **SC-004**: In controlled tests, 100% of simulated operational failures are recorded as operational errors rather than deterministic message-validation failures.
- **SC-005**: Normal user-facing generation commands behave unchanged in regression tests, with no eval artifact writing or fixture loading.
- **SC-006**: Default tests can validate the runner with offline fixtures and deterministic local output without requiring live provider credentials or exposing a live-call automation path.

## Assumptions

- Spec 009 will provide validated fixture and suite schemas, stable case IDs, fixture revisions or digests, reconstructed staged diffs, and smoke/core/safety suite membership.
- This feature is the second eval slice from `docs/planning/evals/implementation-plan.md` and intentionally depends on spec 009 rather than redefining fixture and suite schemas.
- Live model calls use Inspect-native limits and gmuse preflight confirmation for spend guardrails. Exact custom provider-call accounting is not required in this slice.
- Deterministic production validation is in scope; judge scoring and quality rubrics are deferred to the later judge and scoring spec.
- Baseline promotion, regression comparison, fixture importing, and public benchmark recommendations are separate future specs.
