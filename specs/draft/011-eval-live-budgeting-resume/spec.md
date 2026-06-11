# Feature Specification: Eval Live Run Budgeting And Resume

**Feature Branch**: `011-eval-live-budgeting-resume`

**Created**: 2026-06-11

**Status**: Draft

**Draft Note**: This specification describes proposed maintainer-only eval
tooling. It does not describe current gmuse behavior.

**Input**: User description: "Draft the Speckit design artifacts for `specs/draft/011-eval-live-budgeting-resume/` only in the gmuse repo. Scope: explicit live-call budget controls, run planning, confirmation, incremental writes, and resume compatibility. Depend on eval runner outputs from spec 010 and fixtures from spec 009. Do not include judge rubric design, baseline promotion/comparison, fixture importer, or public benchmark recommendations except as dependencies/out of scope."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preview live eval cost before calls (Priority: P1)

As a maintainer preparing a live eval run, I want gmuse to show the planned candidate and judge call counts before making any provider calls so I can verify the run size and cost exposure.

**Why this priority**: Live eval runs can spend real provider credits. The feature is only safe if maintainers see the run plan before any live work starts.

**Independent Test**: Run a live eval command against a validated suite with multiple models and a judge configuration, omit confirmation, and verify the command displays the planned cases, candidate calls, judge calls, budget requirements, output paths, and exits before any provider call is made.

**Acceptance Scenarios**:

1. **Given** a validated suite from spec 009 and a runnable production-path eval configuration from spec 010, **When** the maintainer requests a live run without confirmation, **Then** gmuse displays a run plan with suite, case count, candidate model count, planned candidate calls, planned judge calls, total planned calls, budget limits, and output locations before making calls.
2. **Given** the planned call count exceeds a supplied budget, **When** the maintainer requests the run, **Then** gmuse rejects the run before provider calls and explains which budget would be exceeded.
3. **Given** the maintainer requests `--plan`, **When** the plan is displayed, **Then** gmuse makes no provider calls and writes no live output records.

---

### User Story 2 - Require explicit confirmation and budgets for live calls (Priority: P1)

As a maintainer running evals manually, I want live calls to require explicit budgets and confirmation so accidental expensive runs cannot start from a copied command or CI job.

**Why this priority**: The eval planning notes require live model and judge calls to be manual, explicit, resumable, and cost-controlled.

**Independent Test**: Attempt live runs with missing budgets, insufficient budgets, interactive confirmation, and non-interactive `--yes`, and verify calls only begin when budgets are present and the requested confirmation mode is satisfied.

**Acceptance Scenarios**:

1. **Given** a live run command omits the required candidate-call budget, **When** the command validates inputs, **Then** it fails before any calls with guidance to provide an explicit budget.
2. **Given** a live run includes judge scoring for completed outputs but omits the judge-call budget, **When** the command validates inputs, **Then** it fails before any calls with guidance to provide an explicit judge budget.
3. **Given** an interactive terminal and valid budgets, **When** the maintainer confirms the displayed plan, **Then** gmuse begins the live run and records calls against the budgets.
4. **Given** a non-interactive environment, valid budgets, and `--yes`, **When** the command starts, **Then** gmuse may proceed without a prompt after displaying the same plan.
5. **Given** a non-interactive environment without `--yes`, **When** a live run is requested, **Then** gmuse fails before calls and explains that live runs require interactive confirmation or `--yes`.

---

### User Story 3 - Preserve completed records during interruption (Priority: P1)

As a maintainer running a long eval, I want completed outputs to be written incrementally so an interrupted run does not lose successful work.

**Why this priority**: Live eval runs may be interrupted by rate limits, network failures, terminal closure, or manual cancellation. Resuming is only useful if completed records are durable.

**Independent Test**: Start a live run, interrupt it after at least one completed output, and verify the output records and run summary preserve completed work with accurate planned, budgeted, attempted, completed, skipped, failed, and remaining counts.

**Acceptance Scenarios**:

1. **Given** a live run produces a candidate output, **When** the output is available and validation metadata is known, **Then** gmuse writes the output record before moving to the next planned record.
2. **Given** a live run produces a judge result for an output, **When** the judge result is available, **Then** gmuse writes the judge record before moving to the next planned judge item.
3. **Given** a live run is interrupted, **When** the maintainer inspects artifacts, **Then** completed records remain readable and the summary reflects a partial run rather than a successful complete run.
4. **Given** an operational error occurs for one planned item, **When** the run continues or stops according to configured behavior, **Then** gmuse records the error without overwriting previously completed records.

---

### User Story 4 - Resume compatible partial runs (Priority: P1)

As a maintainer, I want to resume a partial live run and skip completed records so I pay only for missing work.

**Why this priority**: Resume is the main cost-control mechanism after interruptions and provider failures.

**Independent Test**: Create a partial run artifact, rerun the same command with resume enabled and compatible settings, and verify completed records are skipped, missing records are planned within remaining budgets, and the final summary contains both prior and newly completed work.

**Acceptance Scenarios**:

1. **Given** a partial run has completed candidate outputs, **When** the maintainer resumes with compatible suite, case selection, model list, generation config, prompt version, artifact schema, and output directory, **Then** gmuse skips completed candidate records and only schedules missing candidate records.
2. **Given** a partial run has completed judge records, **When** the maintainer resumes with compatible judge settings, **Then** gmuse skips completed judge records and only schedules missing judge records.
3. **Given** a resumed run includes skipped records, **When** budgets are checked, **Then** only newly planned provider calls consume the new run's budget while the summary still reports prior completed records.
4. **Given** a resumed run finishes all missing work, **When** the run summary is written, **Then** it reports the run as complete and includes candidate, judge, budgeted, actual, skipped, failed, and resumed counts.

---

### User Story 5 - Reject incompatible resumes (Priority: P2)

As a maintainer, I want gmuse to reject resume attempts when run settings no longer match so old outputs are not silently mixed with a different evaluation.

**Why this priority**: Mixing records from different suites, models, prompts, judge settings, or schemas would invalidate eval results and make later judging or comparison misleading.

**Independent Test**: Attempt to resume a partial run while changing each compatibility field one at a time and verify gmuse rejects the resume with a clear reason before any provider call.

**Acceptance Scenarios**:

1. **Given** a partial run was created for one suite revision, **When** the maintainer resumes with a different suite, fixture revision, or case selection, **Then** gmuse rejects the resume before provider calls.
2. **Given** a partial run was created with one candidate model list or generation configuration, **When** the maintainer resumes with different models or prompt-affecting options, **Then** gmuse rejects the resume before provider calls.
3. **Given** a partial run includes judge records, **When** the maintainer resumes with different judge model, judge prompt version, judge parameters, or rubric version, **Then** gmuse rejects judge resume before judge calls.
4. **Given** the artifact schema version is no longer supported for resume, **When** the maintainer requests resume, **Then** gmuse rejects the run and explains how to start a new run instead.

### Edge Cases

- Dry-run planning must never make candidate or judge provider calls.
- A live run with zero selected cases, zero selected models, or zero newly planned resume work must finish without provider calls and explain why.
- Missing or unreadable prior output artifacts must fail resume before calls.
- Duplicate completed records for the same planned item must fail resume compatibility unless the records are explicitly marked superseded by the prior run format.
- Corrupt JSONL records must fail resume compatibility before calls.
- Budget limits must count provider call attempts, including attempts that return operational errors.
- Candidate-call budgets and judge-call budgets must be tracked separately, and total-call reporting must not hide either category.
- A run stopped by user cancellation must preserve already written records and mark the summary as interrupted.
- A provider timeout, rate limit, auth error, or network error must be recorded as an operational error separate from output quality or validation failures.
- Resume must not alter or revalidate completed records in a way that changes their original output content.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Live eval runs MUST require an explicit candidate-call budget before any candidate provider call can be made.
- **FR-002**: Live eval runs that include judge calls MUST require an explicit judge-call budget before any judge provider call can be made.
- **FR-003**: gmuse MUST display a run plan before live calls, including suite identity, case count, candidate model list, judge configuration if enabled, planned candidate calls, planned judge calls, total planned calls, budgets, resume status, and output artifact paths.
- **FR-004**: gmuse MUST require interactive confirmation before live calls unless the maintainer supplies an explicit non-interactive confirmation flag.
- **FR-005**: Non-interactive confirmation MUST still require explicit candidate and judge budgets; `--yes` MUST NOT imply unlimited or default live-call budgets.
- **FR-006**: Dry-run planning MUST make zero provider calls and MUST clearly identify that no live output records were written.
- **FR-007**: gmuse MUST reject a live run before calls when planned new candidate calls exceed the supplied candidate budget.
- **FR-008**: gmuse MUST reject a live run before calls when planned new judge calls exceed the supplied judge budget.
- **FR-009**: gmuse MUST track planned, budgeted, attempted, completed, skipped, failed, and remaining call counts separately for candidate and judge work.
- **FR-010**: gmuse MUST write candidate output records incrementally as soon as each planned candidate item finishes with a generated output, validation failure, or operational error.
- **FR-011**: gmuse MUST write judge records incrementally as soon as each planned judge item finishes with a judge result or operational error.
- **FR-012**: gmuse MUST write or update a run summary that can represent planned, running, interrupted, failed, and complete states.
- **FR-013**: Resume mode MUST skip completed candidate output records whose run identity and record identity match the requested run.
- **FR-014**: Resume mode MUST skip completed judge records whose run identity, record identity, and judge identity match the requested run.
- **FR-015**: Resume mode MUST count only newly planned provider calls against the newly supplied budgets while reporting skipped prior records separately.
- **FR-016**: Resume mode MUST reject incompatible prior artifacts before provider calls when suite identity, suite revision, fixture revisions, case selection, candidate model list, generation configuration, prompt version, artifact schema version, or output schema version differs.
- **FR-017**: Resume mode MUST reject incompatible judge resume before judge calls when judge model, judge prompt version, judge parameters, rubric version, or judge output schema version differs.
- **FR-018**: Resume mode MUST fail before calls when prior artifacts are missing, unreadable, corrupt, or contain duplicate active records for the same planned item.
- **FR-019**: gmuse MUST preserve completed record content during resume and MUST NOT overwrite generated messages or judge outputs from prior completed records.
- **FR-020**: gmuse MUST depend on validated fixtures and suites from spec 009 and production-path eval runner output schemas from spec 010 rather than defining a parallel fixture, runner, or generation pipeline.
- **FR-021**: gmuse MUST keep this tooling maintainer-only and MUST NOT require provider credentials for default CI or ordinary `gmuse` message generation workflows.
- **FR-022**: This feature MUST NOT define judge rubric design, baseline promotion, baseline comparison, fixture importer behavior, or public benchmark recommendations.

### Key Entities *(include if feature involves data)*

- **Live Run Plan**: The pre-call plan for selected suite cases, candidate models, optional judge work, call counts, budgets, resume status, and artifact paths.
- **Call Budget**: An explicit maintainer-supplied limit for candidate calls or judge calls in one run attempt.
- **Planned Work Item**: One candidate generation or judge scoring item derived from the selected suite, models, generation config, and judge config.
- **Run Artifact Set**: The output directory and files containing run metadata, incremental candidate records, incremental judge records, and run summary.
- **Candidate Output Record**: A durable record from the production-path eval runner for one case/model/config item, including output, validation outcome, prompt metadata, and operational error if any.
- **Judge Record**: A durable record for one judge scoring item associated with a candidate output record. The scoring rubric itself is out of scope for this feature.
- **Resume Identity**: The compatibility fingerprint used to decide whether prior artifacts can be resumed safely.
- **Run Summary**: A readable summary of run status, call accounting, skipped records, failures, and completion/interruption state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of live-run acceptance tests, no candidate or judge provider call occurs before a run plan is displayed and confirmation requirements are satisfied.
- **SC-002**: In 100% of live-run validation cases, commands with missing required budgets or budgets below planned new calls fail before provider calls.
- **SC-003**: After an interrupted run with at least one completed item, 100% of completed records remain readable and are skipped by a compatible resume.
- **SC-004**: Compatible resume reduces newly planned calls by exactly the number of completed matching candidate and judge records.
- **SC-005**: In compatibility tests covering suite, config, model, prompt, judge, and schema changes, 100% of incompatible resume attempts fail before provider calls with a reason naming the mismatch.
- **SC-006**: Dry-run planning performs zero provider calls in all automated tests and clearly reports planned candidate and judge calls.

## Assumptions

- Spec 009 will provide validated fixture and suite identities, revisions, case selections, and staged-diff reconstruction guarantees.
- Spec 010 will provide production-path eval runner output records, prompt metadata, validation outcomes, operational error categories, and artifact schema versions.
- Judge execution may exist as a later or adjacent capability, but this feature only budgets, plans, writes, and resumes judge call records when a judge configuration is supplied by that dependency.
- Live eval tooling is maintainer-only and is not part of the ordinary `gmuse msg`, `gmuse generate`, or commit-message workflow.
- Provider pricing estimation is out of scope; this feature controls call counts rather than currency cost.
- Automatic retries and repair loops are out of scope. If a future feature adds retries, each provider attempt must consume budget explicitly.
